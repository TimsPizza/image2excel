"""
Module for executing image-to-Excel conversion tasks.
This module handles the interaction with OpenAI API, code generation, execution and iteration management.
"""

from dataclasses import dataclass
from enum import Enum
import traceback
import os
from typing import Any, Dict, Optional, Callable
import pandas as pd
from backend.app.image2excel.engine.request import send_request

class TaskState(Enum):
    """Enumeration of possible task states"""
    CODE_GENERATED = "CODE_GENERATED"
    CODE_EXECUTION_SUCCESS = "CODE_EXECUTION_SUCCESS"
    CODE_EXECUTION_ERROR = "CODE_EXECUTION_ERROR"
    WAITING_FOR_USER_FEEDBACK = "WAITING_FOR_USER_FEEDBACK"
    EXCEL_EXPORT_SUCCESS = "EXCEL_EXPORT_SUCCESS"
    TASK_FAILED = "TASK_FAILED"

@dataclass
class IterationResult:
    """Data class for storing iteration results"""
    generated_code: str
    execution_output: Optional[Any] = None
    error_message: Optional[str] = None
    user_feedback: Optional[str] = None
    dataframe: Optional[pd.DataFrame] = None

@dataclass
class ExecutionState:
    """Data class for representing execution state"""
    state: TaskState
    message: str
    data: Optional[Dict[str, Any]] = None

class TaskExecutor:
    """
    Executor for image-to-Excel conversion tasks.
    Handles OpenAI interaction, code generation, execution, and iteration management.
    """
    
    def __init__(
        self, 
        task_id: str,
        username: str,
        update_hook: Callable[[str, str], None],
        max_iterations: int = 3
    ) -> None:
        self.task_id = task_id
        self.username = username
        self.update_hook = update_hook
        self.max_iterations = max_iterations
        
        # State management
        self.current_iteration = 0
        self.iteration_history: Dict[int, IterationResult] = {}
        self.last_state: Optional[ExecutionState] = None

    def _update_status(self, message: str) -> None:
        """Update task status via hook"""
        self.update_hook(self.username, message)

    def _generate_correction_prompt(self, iteration_result: IterationResult) -> str:
        """
        Generate a correction prompt based on iteration results.
        This prompt guides the model to fix issues from the previous iteration.
        """
        prompt = "根据上次执行的结果，请对代码进行如下改进：\n"
        
        if iteration_result.error_message:
            prompt += f"\n错误信息：\n{iteration_result.error_message}\n"
            prompt += "\n请修复上述错误，确保代码可以正确执行。\n"
            
        if iteration_result.user_feedback:
            prompt += f"\n用户反馈：\n{iteration_result.user_feedback}\n"
            prompt += "\n请根据用户反馈调整代码实现。\n"
            
        if iteration_result.execution_output:
            prompt += f"\n执行输出：\n{iteration_result.execution_output}\n"
            
        prompt += """
请确保：
1. 代码生成正确的DataFrame
2. 所有列使用适当的数据类型
3. 数据经过适当的清理和格式化
4. 最终结果保存在'df'变量中
"""
        return prompt

    async def call_api(self, system_prompt: str, user_prompt: str) -> ExecutionState:
        """
        Make an API call to OpenAI with system and user prompts.
        
        Args:
            system_prompt: Global system prompt including task description
            user_prompt: Current iteration's specific prompt
        """
        try:
            self._update_status(f"正在生成代码 (迭代 {self.current_iteration})...")
            
            response = await send_request(
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            generated_code = response.get("generated_code", "")
            if not generated_code:
                raise ValueError("No code generated from API")
                
            self.iteration_history[self.current_iteration] = IterationResult(
                generated_code=generated_code
            )
            
            return ExecutionState(
                state=TaskState.CODE_GENERATED,
                message="代码生成成功",
                data={"code": generated_code, "iteration": self.current_iteration}
            )
        except Exception as e:
            error_msg = f"代码生成失败: {str(e)}\n{traceback.format_exc()}"
            if self.current_iteration in self.iteration_history:
                self.iteration_history[self.current_iteration].error_message = error_msg
                
            return ExecutionState(
                state=TaskState.TASK_FAILED,
                message=error_msg
            )

    async def execute_code(self, iteration: int) -> ExecutionState:
        """Execute generated code and capture results"""
        if iteration not in self.iteration_history:
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_ERROR,
                message=f"未找到迭代 {iteration} 的代码"
            )
            
        iteration_result = self.iteration_history[iteration]
        code = iteration_result.generated_code
        
        try:
            self._update_status(f"正在执行代码 (迭代 {iteration})...")
            
            # Execute code in isolated environment
            local_vars = {}
            exec(code, {"pd": pd}, local_vars)
            
            if "df" not in local_vars:
                raise ValueError("代码执行未生成'df'变量")
                
            df = local_vars["df"]
            if not isinstance(df, pd.DataFrame):
                raise ValueError("生成的'df'不是pandas DataFrame类型")
                
            # Update iteration result
            iteration_result.dataframe = df
            iteration_result.execution_output = "DataFrame successfully created"
            
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_SUCCESS,
                message="代码执行成功",
                data={"dataframe": df}
            )
            
        except Exception as e:
            error_msg = f"代码执行失败: {str(e)}\n{traceback.format_exc()}"
            iteration_result.error_message = error_msg
            
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_ERROR,
                message=error_msg
            )

    async def process_feedback(self, feedback: str, iteration: int) -> ExecutionState:
        """Process user feedback for an iteration"""
        if iteration not in self.iteration_history:
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_ERROR,
                message=f"未找到迭代 {iteration} 的记录"
            )
            
        self.iteration_history[iteration].user_feedback = feedback
        return ExecutionState(
            state=TaskState.WAITING_FOR_USER_FEEDBACK,
            message="用户反馈已记录"
        )

    async def export_excel(self, iteration: int, output_dir: str) -> ExecutionState:
        """Export DataFrame to Excel file"""
        if iteration not in self.iteration_history:
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_ERROR,
                message=f"未找到迭代 {iteration} 的数据"
            )
            
        iteration_result = self.iteration_history[iteration]
        if not iteration_result.dataframe is not None:
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_ERROR,
                message="没有可导出的DataFrame"
            )
            
        try:
            self._update_status("正在导出Excel文件...")
            
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(
                output_dir,
                f"{self.task_id}_iteration_{iteration}.xlsx"
            )
            
            iteration_result.dataframe.to_excel(output_path, index=False)
            
            return ExecutionState(
                state=TaskState.EXCEL_EXPORT_SUCCESS,
                message="Excel导出成功",
                data={"file_path": output_path}
            )
        except Exception as e:
            return ExecutionState(
                state=TaskState.CODE_EXECUTION_ERROR,
                message=f"Excel导出失败: {str(e)}"
            )

    def get_iteration_results(self) -> Dict[int, IterationResult]:
        """Get all iteration results"""
        return self.iteration_history.copy()

    def get_last_successful_dataframe(self) -> Optional[pd.DataFrame]:
        """Get the DataFrame from the last successful iteration"""
        for iteration in sorted(self.iteration_history.keys(), reverse=True):
            result = self.iteration_history[iteration]
            if result.dataframe is not None:
                return result.dataframe
        return None
