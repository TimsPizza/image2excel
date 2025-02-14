"""
Module for processing image-to-Excel tasks.
This module defines the minimal task unit: Image2ExcelTask.
Its sole responsibility is to manage task scheduling and overall state.
It delegates API interaction, code generation, code execution, self-correction, and Excel export to the embedded executor.
"""

import asyncio
from typing import Callable, List

from app.image2excel.engine.request_self_correct import (
    Image2ExcelTaskExecutor,
    STATE_CODE_EXECUTION_SUCCESS,
    STATE_CODE_EXECUTION_ERROR,
    STATE_WAITING_FOR_USER_FEEDBACK,
    STATE_EXCEL_EXPORT_SUCCESS,
    STATE_CODE_GENERATED,
)


class Image2ExcelTask:
    def __init__(
        self, username: str, images: List[str], update_hook: Callable[[str, str], None]
    ) -> None:
        """
        Initialize a new task for processing an image-to-Excel conversion.

        :param username: Identifier for the user.
        :param images: List of image contents (file paths or base64 strings) to process.
        :param update_hook: Callback function to update the task status.
        """
        self.username = username
        self.images = images
        self.update_hook = update_hook
        self.cancelled = False
        self.status: str = "就绪"
        # Instantiate the executor responsible for API inquiries and task execution.
        self.executor = Image2ExcelTaskExecutor(self, update_hook)

    async def run(self) -> None:
        """
        Execute the image-to-Excel task asynchronously.
        This method manages the task scheduling based on state codes returned by the executor.
        It coordinates:
          - Starting an OpenAI conversation.
          - Generating code.
          - Executing the generated code to capture a DataFrame ('df').
          - Based on the execution outcome:
              * If successful (capturing a DataFrame), updates status to allow user preview.
              * If approved (simulated here with immediate export), exports the DataFrame to an Excel file.
              * If execution fails or results are unsatisfactory, triggers code correction.
        """
        self.status = "任务已创建"
        self.update_hook(self.username, self.status)
        await asyncio.sleep(0.1)  # Simulate a minor delay

        if self.cancelled:
            self.status = "任务已取消"
            self.update_hook(self.username, self.status)
            return

        # Start OpenAI conversation.
        await self.executor.start_conversation()

        # Loop for a maximum number of iterations.
        for _ in range(self.executor.max_iterations):
            # Generate code.
            gen_result = await self.executor.generate_code()
            if gen_result.get("state") != STATE_CODE_GENERATED:
                self.status = "代码生成失败"
                self.update_hook(self.username, "代码生成失败，尝试重新生成")
                continue

            # Execute the generated code to capture the DataFrame.
            exec_result = await self.executor.execute_generated_code()
            if exec_result.get("state") == STATE_CODE_EXECUTION_SUCCESS:
                self.status = "代码执行成功，等待用户预览DataFrame"
                self.update_hook(
                    self.username, "代码执行成功，DataFrame已获取，请预览并确认"
                )
                # In a real-world scenario, the task would now wait for user feedback.
                # For simulation, we assume immediate approval to export the Excel file.
                export_result = await self.executor.export_to_excel(
                    self.executor.cached_dataframe
                )
                if export_result.get("state") == STATE_EXCEL_EXPORT_SUCCESS:
                    self.status = "任务完成"
                    self.update_hook(self.username, "Excel导出成功，任务完成")
                    return
                else:
                    self.status = "Excel导出失败"
                    self.update_hook(self.username, "Excel导出失败")
                    return
            elif exec_result.get("state") in [
                STATE_WAITING_FOR_USER_FEEDBACK,
                STATE_CODE_EXECUTION_ERROR,
            ]:
                self.update_hook(self.username, "代码执行出错或结果不符，尝试纠正...")
                # Request code correction based on error or unsatisfactory result.
                await self.executor.correct_code()
                # Optionally, one could incorporate user feedback via self.executor.provide_feedback(feedback)
                # before retrying.

        # If maximum iterations have been reached without success.
        self.status = "任务执行失败"
        self.update_hook(self.username, "达到最大重试次数，任务执行失败")

    def cancel(self) -> None:
        """
        Cancel this task.
        """
        self.cancelled = True


async def create_task(
    username: str, images: List[str], update_hook: Callable[[str, str], None]
) -> Image2ExcelTask:
    """
    Create a new Image2ExcelTask instance and start its execution asynchronously.
    Task management (e.g., storing the task instance) is handled by the task manager.

    :param username: User identifier.
    :param images: List of image contents to process.
    :param update_hook: Callback function to receive status updates.
    :return: The created Image2ExcelTask instance.
    """
    task = Image2ExcelTask(username, images, update_hook)
    asyncio.create_task(task.run())
    return task
