"""
Module for task service.
This service layer decouples the interface layer (e.g., FastAPI routes) from the task layer.
It communicates directly with the Image2ExcelTaskManager, which handles task creation,
execution, cancellation, deletion, and status queries.
"""

from typing import Any, Callable, Dict, List, Optional
import asyncio

from backend.app.image2excel.task_manager import Image2ExcelTaskManager

class TaskService:
    """
    Service layer for managing user tasks.
    Acts as an intermediary between the interface layer (e.g., API routes) and the task layer.
    """
    task_manager = Image2ExcelTaskManager()
    @classmethod
    async def create_task(cls, username: str, images: List[str], update_hook: Callable[[str, str], None]) -> Any:
        """
        Create a new Image2Excel task for a user.
        
        :param username: User identifier.
        :param images: List of images to process.
        :param update_hook: Callback function to receive status updates.
        :return: The created task instance.
        """
        task = await cls.task_manager.create_task(username, images, update_hook)
        return task

    @classmethod
    def get_status(cls, username: str) -> Optional[str]:
        """
        Get the current status of the user's task.
        
        :param username: User identifier.
        :return: Task status if available, else None.
        """
        return cls.task_manager.get_status(username)

    @classmethod
    def cancel_task(cls, username: str) -> bool:
        """
        Cancel the task associated with a user.
        
        :param username: User identifier.
        :return: True if the task was found and cancelled, otherwise False.
        """
        return cls.task_manager.cancel_task(username)

    @classmethod
    def delete_task(cls, username: str) -> bool:
        """
        Delete the task for a user from the task registry.
        
        :param username: User identifier.
        :return: True if the task existed and was deleted, otherwise False.
        """
        return cls.task_manager.delete_task(username)


    @classmethod
    async def run_task(cls, username: str) -> Optional[Any]:
        """
        Explicitly trigger the execution of a user's task and await its completion.
        
        :param username: User identifier.
        :return: Final task status if the task exists, else None.
        """
        return await cls.task_manager.run_task(username)
