"""
Module for managing image-to-Excel conversion tasks.
Implements the task lifecycle and coordinates with TaskExecutor for actual execution.
"""

import asyncio
import base64
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import uuid

from app.image2excel.ImageUtils import ImageUtils
from app.image2excel.TaskExecutor import TaskExecutor, TaskState, ExecutionState
from backend.app.image2excel.engine.prompt import (
    get_initial_prompt,
    get_initial_user_prompt,
)


class TaskStatus(Enum):
    """Task lifecycle states"""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class TaskMetadata:
    """Task metadata for tracking and management"""

    created_at: float  # Unix timestamp
    last_updated_at: float
    total_iterations: int = 0
    current_iteration: int = 0
    error_count: int = 0


class Image2ExcelTask:
    """
    Main task class for image-to-Excel conversion.
    Manages task lifecycle and coordinates with TaskExecutor.
    """

    def __init__(
        self,
        username: str,
        image_path: str,
        update_hook: Optional[Callable[[str, str], None]] = None,
        task_id: Optional[str] = None,
    ):
        """
        Initialize a new image-to-Excel conversion task.

        Args:
            username (str): User identifier
            image_path (str): Path to the image file
            update_hook (Callable): Status update callback
            task_id (str, optional): Custom task ID, auto-generated if None
        """
        self.task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        self.username = username
        self.image_path = image_path

        self.update_hook = update_hook or self.default_update_hook

        # Task state management
        self._status = TaskStatus.CREATED
        self._metadata = TaskMetadata(
            created_at=asyncio.get_event_loop().time(),
            last_updated_at=asyncio.get_event_loop().time(),
        )
        self._error: Optional[str] = None
        self._cancellation_event = asyncio.Event()

        # Task execution configuration
        self._executor: Optional[TaskExecutor] = None
        self._last_execution_state: Optional[ExecutionState] = None
        self._system_prompt: Optional[str] = None
        self._initial_user_prompt: Optional[str] = None

    @property
    def status(self) -> TaskStatus:
        """Get current task status"""
        return self._status

    @property
    def metadata(self) -> TaskMetadata:
        """Get task metadata"""
        return self._metadata

    @property
    def error(self) -> Optional[str]:
        """Get last error message if any"""
        return self._error

    def _update_status(self, new_status: TaskStatus, message: str) -> None:
        """Update task status and notify via hook"""
        self._status = new_status
        self._metadata.last_updated_at = asyncio.get_event_loop().time()
        self.update_hook(self.username, message)

    def _prepare_system_prompt(self) -> str:
        """
        Prepare the global system prompt with task description and image.
        This prompt remains constant throughout the task lifecycle.
        """

        return get_initial_prompt()

    async def _prepare_initial_user_prompt(self) -> str:
        image_b64 = await ImageUtils.from_file(self.image_path)
        return get_initial_user_prompt(image_b64)

    async def initialize(self) -> bool:
        """Initialize task and prepare executor"""
        try:
            self._update_status(TaskStatus.INITIALIZING, "初始化任务...")

            # Prepare system prompt
            self._system_prompt = self._prepare_system_prompt()
            self._initial_user_prompt = await self._prepare_initial_user_prompt()

            # Initialize executor
            self._executor = TaskExecutor(
                task_id=self.task_id,
                username=self.username,
                update_hook=self.update_hook,
            )

            self._update_status(TaskStatus.CREATED, "任务初始化完成")
            return True

        except Exception as e:
            self._error = f"初始化错误: {str(e)}"
            self._update_status(TaskStatus.FAILED, self._error)
            return False

    async def run(self) -> None:
        """
        Execute the task through its lifecycle.
        Coordinates with TaskExecutor for code generation, execution, and iteration.
        """
        if not self._executor or not self._system_prompt:
            await self.initialize()
            if self.status == TaskStatus.FAILED:
                return

        self._update_status(TaskStatus.RUNNING, "开始执行任务...")

        try:
            while (
                self._metadata.current_iteration < self._executor.max_iterations
                and not self._cancellation_event.is_set()
            ):
                # Get user prompt for current iteration
                if self._metadata.current_iteration == 0:
                    user_prompt = self._initial_user_prompt
                else:
                    # Get last iteration result
                    iteration_results = self._executor.get_iteration_results()
                    last_result = iteration_results.get(
                        self._metadata.current_iteration
                    )
                    if last_result:
                        user_prompt = self._executor._generate_correction_prompt(
                            last_result
                        )
                    else:
                        user_prompt = self._initial_user_prompt

                # Generate code using API
                self.current_iteration += 1
                exec_state = await self._executor.call_api(
                    system_prompt=self._system_prompt, user_prompt=user_prompt
                )
                self._last_execution_state = exec_state

                if exec_state.state == TaskState.CODE_GENERATED:
                    self._metadata.total_iterations += 1

                    # Execute generated code
                    exec_state = await self._executor.execute_code(
                        self._metadata.current_iteration
                    )
                    self._last_execution_state = exec_state

                    if exec_state.state == TaskState.CODE_EXECUTION_SUCCESS:
                        # Success! Export to Excel
                        export_state = await self._executor.export_excel(
                            self._metadata.current_iteration,
                            "backend/app/image2excel/files/generated",
                        )
                        if export_state.state == TaskState.EXCEL_EXPORT_SUCCESS:
                            self._update_status(
                                TaskStatus.COMPLETED,
                                f"任务完成。Excel文件已保存: {export_state.data.get('file_path')}",
                            )
                            return
                    else:
                        self._metadata.error_count += 1

                elif exec_state.state == TaskState.TASK_FAILED:
                    self._error = exec_state.message
                    self._update_status(TaskStatus.FAILED, f"任务失败: {self._error}")
                    return

                # Wait briefly before next iteration
                await asyncio.sleep(1)

            if self._cancellation_event.is_set():
                self._update_status(TaskStatus.CANCELLED, "任务已取消")
            elif self._metadata.current_iteration >= self._executor.max_iterations:
                self._update_status(
                    TaskStatus.FAILED,
                    f"达到最大迭代次数 ({self._executor.max_iterations})",
                )

        except Exception as e:
            self._error = f"执行错误: {str(e)}"
            self._update_status(TaskStatus.FAILED, self._error)

    async def cancel(self) -> None:
        """Cancel the task"""
        self._cancellation_event.set()
        self._update_status(TaskStatus.CANCELLED, "任务取消中...")

    async def pause(self) -> None:
        """Pause the task (if supported)"""
        if self.status == TaskStatus.RUNNING:
            self._update_status(TaskStatus.PAUSED, "任务已暂停")

    async def resume(self) -> None:
        """Resume the paused task (if supported)"""
        if self.status == TaskStatus.PAUSED:
            self._update_status(TaskStatus.RUNNING, "任务已恢复")
            await self.run()

    async def provide_feedback(self, feedback: str) -> None:
        """
        Process user feedback for the current iteration

        Args:
            feedback (str): User feedback for improving the result
        """
        if self._executor and self._metadata.current_iteration > 0:
            await self._executor.process_feedback(
                feedback, self._metadata.current_iteration
            )

    def get_last_state(self) -> Dict[str, Any]:
        """Get the last execution state details"""
        if not self._last_execution_state:
            return {
                "status": self.status.value,
                "message": "No execution state available",
            }

        return {
            "status": self.status.value,
            "state": self._last_execution_state.state.value,
            "message": self._last_execution_state.message,
            "data": self._last_execution_state.data or {},
        }

    @staticmethod
    def default_update_hook(username: str, status: str) -> None:
        """Default status update handler"""
        print(f"Task status update for user '{username}': {status}")
