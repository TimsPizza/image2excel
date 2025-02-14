"""
Module for API self-correction execution.
This module defines the Image2ExcelTaskExecutor class. For a given Image2ExcelTask,
the executor is responsible for:
  - Initiating and maintaining an OpenAI conversation session.
  - Generating code based on a prompt and caching the generated code.
  - Executing the generated code and analyzing execution output.
  - Handling self-correction by using error messages and user feedback to refine the code.
  - Exposing detailed state codes and messages to the parent task.
  - When code execution is successful and produces a DataFrame (captured as the variable 'df'),
    the DataFrame is cached and returned to the task for preview.
  - Upon user approval, the cached DataFrame can be exported to an Excel file using pandas.
    
State Codes (returned by methods):
  STATE_CONVERSATION_INIT = 0         -> Conversation session started.
  STATE_CODE_GENERATED = 1            -> Code generated successfully.
  STATE_CODE_EXECUTION_SUCCESS = 2    -> Code executed successfully and returned a DataFrame.
  STATE_CODE_EXECUTION_ERROR = 3      -> Code execution encountered an error.
  STATE_WAITING_FOR_USER_FEEDBACK = 4 -> Awaiting user feedback.
  STATE_EXCEL_EXPORT_SUCCESS = 5      -> Excel export successful.
"""

import asyncio
import traceback
import os
from typing import Any, Dict, Optional, Callable

import pandas as pd  # Required for exporting DataFrame to Excel.

from backend.app.image2excel.Image2Excel import send_request
from backend.app.image2excel.engine.request import send_request

# Define state codes for clarity.
STATE_CONVERSATION_INIT = 0
STATE_CODE_GENERATED = 1
STATE_CODE_EXECUTION_SUCCESS = 2
STATE_CODE_EXECUTION_ERROR = 3
STATE_WAITING_FOR_USER_FEEDBACK = 4
STATE_EXCEL_EXPORT_SUCCESS = 5

class Image2ExcelTaskExecutor:
    def __init__(self, task, update_hook: Callable[[str, str], None], max_iterations: int = 3) -> None:
        """
        Initialize the executor for a given Image2ExcelTask.

        :param task: The Image2ExcelTask instance to be executed.
        :param update_hook: Callback function to update the task status.
        :param max_iterations: Maximum number of iterations for self-correction.
        """
        self.task = task
        self.update_hook = update_hook
        self.max_iterations = max_iterations
        self.iteration = 0
        self.conversation_id: Optional[str] = None
        self.last_generated_code: Optional[str] = None
        self.cached_dataframe: Optional[pd.DataFrame] = None
        self.last_error: Optional[str] = None
        self.user_feedback: Optional[str] = None
        self.execution_details: Dict[str, Any] = {}

    async def start_conversation(self) -> int:
        """
        Start an OpenAI conversation session.
        This method initializes the conversation and caches the conversation_id.
        Returns:
           STATE_CONVERSATION_INIT on success.
        """
        self.update_hook(self.task.username, "启动OpenAI会话...")
        # For simulation purposes: assign a dummy conversation id.
        self.conversation_id = "dummy_conversation_id"
        self.update_hook(self.task.username, f"会话已启动，ID: {self.conversation_id}")
        return STATE_CONVERSATION_INIT

    async def generate_code(self) -> Dict[str, Any]:
        """
        Generate code from the model using the established conversation.
        Uses the current iteration count and optional user feedback to construct the prompt.
        Caches the generated code and returns a dictionary with a state code and message.
        """
        self.iteration += 1
        prompt = f"处理任务 for user {self.task.username}, 迭代 {self.iteration}."
        if self.user_feedback:
            prompt += f" 用户反馈: {self.user_feedback}"
        self.update_hook(self.task.username, f"请求生成代码, 迭代 {self.iteration}...")
        try:
            response = send_request(prompt)
            # Cache conversation id from response if provided.
            if response.get("completion_id"):
                self.conversation_id = response.get("completion_id")
            generated_code = response.get("generated_code")
            self.last_generated_code = generated_code
            self.execution_details[f"iteration_{self.iteration}_code"] = generated_code
            self.update_hook(self.task.username, f"迭代 {self.iteration}: 代码已生成")
            return {"state": STATE_CODE_GENERATED, "message": "代码生成成功", "code": generated_code}
        except Exception as e:
            self.last_error = traceback.format_exc()
            self.execution_details[f"iteration_{self.iteration}_error"] = self.last_error
            self.update_hook(self.task.username, f"迭代 {self.iteration}: 生成代码出错")
            return {"state": STATE_CODE_EXECUTION_ERROR, "message": "代码生成失败", "error": self.last_error}

    async def execute_generated_code(self) -> Dict[str, Any]:
        """
        Execute the last generated code.
        The generated code is expected to define a variable 'df' as a pandas DataFrame.
        Captures 'df' from the execution environment.
        Returns:
            - STATE_CODE_EXECUTION_SUCCESS with the DataFrame if execution is successful.
            - STATE_WAITING_FOR_USER_FEEDBACK if the result is not as expected.
            - STATE_CODE_EXECUTION_ERROR if an execution error occurs.
        Note: This method does not save the generated code to a file; instead it pauses and returns the DataFrame for preview.
        """
        if not self.last_generated_code:
            self.update_hook(self.task.username, "无可执行的代码")
            return {"state": STATE_CODE_EXECUTION_ERROR, "message": "没有生成代码可执行"}
        self.update_hook(self.task.username, "执行生成的代码...")
        try:
            local_vars = {}
            # Prepare an execution environment with pandas available.
            exec(self.last_generated_code, {"pd": pd}, local_vars)
            if "df" not in local_vars:
                self.update_hook(self.task.username, "执行成功，但未检测到变量 'df'")
                return {"state": STATE_WAITING_FOR_USER_FEEDBACK, "message": "代码执行成功，但未返回DataFrame", "result": None}
            df = local_vars["df"]
            # Cache the DataFrame.
            if isinstance(df, pd.DataFrame):
                self.cached_dataframe = df
                self.execution_details[f"iteration_{self.iteration}_result"] = "DataFrame captured"
                self.update_hook(self.task.username, "代码执行成功，已获得DataFrame，等待用户预览")
                return {"state": STATE_CODE_EXECUTION_SUCCESS, "message": "代码执行成功", "result": df}
            else:
                self.update_hook(self.task.username, "返回结果不是一个DataFrame")
                return {"state": STATE_WAITING_FOR_USER_FEEDBACK, "message": "返回结果不是DataFrame", "result": df}
        except Exception as e:
            self.last_error = traceback.format_exc()
            self.execution_details[f"iteration_{self.iteration}_exec_error"] = self.last_error
            self.update_hook(self.task.username, "代码执行出错")
            return {"state": STATE_CODE_EXECUTION_ERROR, "message": "代码执行出错", "error": self.last_error}

    async def correct_code(self) -> Dict[str, Any]:
        """
        In case of code execution error, generate a new code iteration with an updated prompt including error details.
        Returns a dictionary with a state code and message.
        """
        prompt = f"修正代码 for user {self.task.username}, 迭代 {self.iteration}."
        if self.last_error:
            prompt += f" 错误信息: {self.last_error}"
        self.update_hook(self.task.username, "请求纠错代码...")
        try:
            response = send_request(prompt, completion_id=self.conversation_id)
            if response.get("completion_id"):
                self.conversation_id = response.get("completion_id")
            new_generated_code = response.get("generated_code")
            self.last_generated_code = new_generated_code
            self.execution_details[f"iteration_{self.iteration}_corrected_code"] = new_generated_code
            self.update_hook(self.task.username, "已获得纠错代码")
            return {"state": STATE_CODE_GENERATED, "message": "纠错代码生成成功", "code": new_generated_code}
        except Exception as e:
            self.last_error = traceback.format_exc()
            self.update_hook(self.task.username, "纠错代码生成出错")
            return {"state": STATE_CODE_EXECUTION_ERROR, "message": "纠错代码生成失败", "error": self.last_error}

    async def provide_feedback(self, feedback: str) -> Dict[str, Any]:
        """
        Accept user feedback to refine the code generation.
        Saves the feedback for use in subsequent code generation.
        Returns a status message indicating feedback receipt.
        """
        self.user_feedback = feedback
        self.update_hook(self.task.username, "用户反馈已记录，将用于下次生成代码")
        return {"state": STATE_WAITING_FOR_USER_FEEDBACK, "message": "反馈已记录"}

    async def export_to_excel(self, dataframe: pd.DataFrame) -> Dict[str, Any]:
        """
        Export the provided DataFrame to an Excel file using pandas.
        The Excel file is saved to the files/generated/ directory.
        Returns a dictionary with a state code and message.
        """
        self.update_hook(self.task.username, "尝试将DataFrame导出为Excel文件...")
        try:
            export_dir = "files/generated"
            os.makedirs(export_dir, exist_ok=True)
            excel_file_path = os.path.join(export_dir, f"{self.task.username}_iteration_{self.iteration}_output.xlsx")
            # Use pandas to export the DataFrame.
            dataframe.to_excel(excel_file_path, index=False)
            self.update_hook(self.task.username, "Excel文件导出成功")
            return {"state": STATE_EXCEL_EXPORT_SUCCESS, "message": "Excel导出成功", "excel_file": excel_file_path}
        except Exception as e:
            self.last_error = traceback.format_exc()
            self.update_hook(self.task.username, "Excel文件导出失败")
            return {"state": STATE_CODE_EXECUTION_ERROR, "message": "Excel导出失败", "error": self.last_error}
