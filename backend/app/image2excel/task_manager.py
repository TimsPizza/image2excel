"""
Module for managing Image2Excel tasks at the task layer.
This module provides the Image2ExcelTaskManager class that handles direct task creation,
execution, cancellation, deletion, and status queries.
It maintains a per-user task registry with the following structure:
{
    username: [
        {
            "task_id": str,
            "file_name": str,
            "i2e_task": Image2ExcelTask
        },
        ...
    ]
}
This design enables queries for all tasks associated with a user.
"""

import asyncio
import uuid
from typing import Any, Callable, Dict, List, Optional, Union

from .Image2Excel import (
    create_task as create_image2excel_task,
    cancel_task as cancel_image2excel_task,
    get_task_status as get_image2excel_task_status,
    Image2ExcelTask,
)

class Image2ExcelTaskManager:
    """
    Manages Image2Excel tasks at the task layer.
    Provides methods for creating, executing, canceling, deleting tasks,
    and querying their status.
    Maintains a per-user registry with task metadata.
    """

    def __init__(self) -> None:
        # Registry mapping username to a list of task records.
        # Each record is a dict with keys: task_id, file_name, i2e_task.
        self.user_tasks: Dict[str, List[Dict[str, Union[str, Image2ExcelTask]]]] = {}

    async def create_task(self, username: str, file_name: str, images: List[str], update_hook: Callable[[str, str], None]) -> Dict[str, Union[str, Image2ExcelTask]]:
        """
        Create and immediately start a new Image2Excel task for the specified user.
        
        :param username: User identifier.
        :param file_name: The file name of the uploaded image.
        :param images: List of images (file paths or base64 strings) to process.
        :param update_hook: Callback function for status updates.
        :return: A dictionary record containing task_id, file_name, and i2e_task.
        """
        # Create a new Image2Excel task via the image2excel module.
        i2e_task = await create_image2excel_task(username, images, update_hook)
        task_id = str(uuid.uuid4())
        record = {
            "task_id": task_id,
            "file_name": file_name,
            "i2e_task": i2e_task
        }
        # Add the record to the user's task list.
        if username not in self.user_tasks:
            self.user_tasks[username] = []
        self.user_tasks[username].append(record)
        return record

    def get_status(self, username: str, task_id: str) -> Optional[str]:
        """
        Retrieve the current status of a specific task for the specified user.
        
        :param username: User identifier.
        :param task_id: The unique task identifier.
        :return: Status string if task exists, else None.
        """
        records = self.user_tasks.get(username, [])
        for record in records:
            if record.get("task_id") == task_id:
                i2e_task: Image2ExcelTask = record.get("i2e_task")  # type: ignore
                return i2e_task.status
        return None

    def get_all_tasks(self, username: str) -> List[Dict[str, Union[str, Image2ExcelTask]]]:
        """
        Retrieve all tasks for the specified user.
        
        :param username: User identifier.
        :return: List of task records.
        """
        return self.user_tasks.get(username, [])

    def cancel_task(self, username: str, task_id: str) -> bool:
        """
        Cancel a specific task associated with the given user.
        
        :param username: User identifier.
        :param task_id: Unique task identifier.
        :return: True if the task was found and cancelled, False otherwise.
        """
        records = self.user_tasks.get(username, [])
        for record in records:
            if record.get("task_id") == task_id:
                # Cancel the task via the Image2Excel mechanism.
                result = cancel_image2excel_task(username)
                if result:
                    # Remove the record from the registry.
                    records.remove(record)
                return result
        return False

    def delete_task(self, username: str, task_id: str) -> bool:
        """
        Delete a task for the specified user from the registry.
        If the task is still running, it will be cancelled before deletion.
        
        :param username: User identifier.
        :param task_id: Unique task identifier.
        :return: True if the task existed and was deleted, False otherwise.
        """
        records = self.user_tasks.get(username, [])
        for record in records:
            if record.get("task_id") == task_id:
                i2e_task: Image2ExcelTask = record.get("i2e_task")  # type: ignore
                if i2e_task.status not in ["任务完成", "任务已取消"]:
                    self.cancel_task(username, task_id)
                records.remove(record)
                return True
        return False

    async def run_task(self, username: str, task_id: str) -> Optional[Any]:
        """
        Trigger the execution of a specific user's task and await its completion.
        
        :param username: User identifier.
        :param task_id: Unique task identifier.
        :return: Final status of the task, or None if the task was not found.
        """
        records = self.user_tasks.get(username, [])
        for record in records:
            if record.get("task_id") == task_id:
                i2e_task: Image2ExcelTask = record.get("i2e_task")  # type: ignore
                await i2e_task.run()
                return i2e_task.status
        return None
