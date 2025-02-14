"""
Module for task service.
This service layer decouples the interface layer (e.g., FastAPI routes) from the task layer.
It communicates directly with the Image2ExcelTaskManager, which handles task creation,
execution, cancellation, deletion, and status queries.
"""

from typing import Any, Callable, Dict, List, Optional

from app.image2excel import task_manager
from backend.app.core.config import ENV_CONFIG


class TaskService:
    """
    Service layer for managing user tasks.
    Acts as an intermediary between the interface layer (e.g., API routes) and the task layer.
    """

    @staticmethod
    def create_task(
        username: str, image_file_name: str, update_hook: Callable[[str, str], None]
    ) -> str:
        """
        Create a new Image2Excel task for a user.

        :param username: User identifier.
        :param images: List of images to process.
        :param update_hook: Callback function to receive status updates.
        :return: The created task instance.
        """
        # TODO: why tf do I need a update_hook??
        image_path = (
            ENV_CONFIG.SCRIPT_ROOT_DIR
            + "/app/image2excel/files/uploaded/"
            + f"{username}_"
            + image_file_name
        )
        task = task_manager.create_task(
            username, image_path, image_file_name, update_hook
        )
        return task

    @staticmethod
    def get_status(username: str, task_id: str) -> Optional[str]:
        """
        Get the current status of the user's task.

        :param username: User identifier.
        :return: Task status if available, else None.
        """
        return task_manager.get_task_status(username, task_id)

    @staticmethod
    def cancel_task(username: str, task_id: str) -> bool:
        """
        Cancel the task associated with a user.

        :param username: User identifier.
        :return: True if the task was found and cancelled, otherwise False.
        """
        return task_manager.cancel_task(username, task_id)

    @staticmethod
    def delete_task(username: str, task_id: str) -> bool:
        """
        Delete the task for a user from the task registry.

        :param username: User identifier.
        :return: True if the task existed and was deleted, otherwise False.
        """
        return task_manager.delete_task(username, task_id)

    @staticmethod
    async def run_task(username: str, task_id: str) -> Optional[Any]:
        """
        Explicitly trigger the execution of a user's task and await its completion.

        :param username: User identifier.
        :return: Final task status if the task exists, else None.
        """
        return await task_manager.start_task(username, task_id)
