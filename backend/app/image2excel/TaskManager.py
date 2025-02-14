"""
Module for managing Image2Excel tasks at the task layer.
This module provides the Image2ExcelTaskManager class that handles task lifecycle management
while abstracting away the asynchronous implementation details.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from queue import Queue

from .Task import Image2ExcelTask

@dataclass
class TaskRecord:
    """Task record data structure"""
    task_id: str
    file_name: str
    task: Image2ExcelTask
    status: str = "CREATED"

class AsyncioEventLoopThread(threading.Thread):
    """
    A dedicated thread for running the asyncio event loop.
    This enables async operations to be executed from synchronous code.
    """
    
    def __init__(self):
        super().__init__(daemon=True)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = threading.Event()
        self._queue: Queue = Queue()

    def run(self):
        """Thread's main loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._running.set()
        self.loop.run_forever()

    def stop(self):
        """Stop the event loop"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self._running.clear()

    def run_coroutine(self, coro) -> Any:
        """
        Run a coroutine in the event loop and wait for its result.
        
        Args:
            coro: The coroutine to run
        Returns:
            The result of the coroutine
        """
        if not self._running.is_set():
            raise RuntimeError("Event loop is not running")
            
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

class Image2ExcelTaskManager:
    """
    Manages Image2Excel tasks with a synchronous API.
    Internally handles asynchronous operations using a dedicated event loop thread.
    """

    def __init__(self):
        """Initialize the task manager"""
        # Start async event loop in separate thread
        self._async_thread = AsyncioEventLoopThread()
        self._async_thread.start()
        self._async_thread._running.wait()  # Wait for thread to start
        
        # Task registry
        self._tasks: Dict[str, Dict[str, TaskRecord]] = {}  # username -> {task_id -> record}
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _run_async(self, coro) -> Any:
        """Helper method to run coroutines in the event loop thread"""
        return self._async_thread.run_coroutine(coro)

    def create_task(
        self, 
        username: str, 
        image_path: str,
        file_name: str,
        update_hook: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """
        Create a new Image2Excel task (synchronous API).
        
        Args:
            username: User identifier
            image_path: Path to the image file
            file_name: Original filename
            update_hook: Optional callback for status updates
        
        Returns:
            task_id: Unique identifier for the created task
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Create task instance
        task = Image2ExcelTask(
            username=username,
            image_path=image_path,
            update_hook=update_hook,
            task_id=task_id
        )
        
        # Create and store task record
        record = TaskRecord(
            task_id=task_id,
            file_name=file_name,
            task=task
        )
        
        if username not in self._tasks:
            self._tasks[username] = {}
        self._tasks[username][task_id] = record
        
        # Initialize task in background
        self._executor.submit(self._run_async, task.initialize())
        
        return task_id

    def start_task(self, username: str, task_id: str) -> bool:
        """
        Start task execution (synchronous API).
        
        Args:
            username: User identifier
            task_id: Task identifier
        
        Returns:
            bool: True if task was started successfully
        """
        if not self._validate_task(username, task_id):
            return False
            
        task = self._tasks[username][task_id].task
        self._executor.submit(self._run_async, task.run())
        return True

    def cancel_task(self, username: str, task_id: str) -> bool:
        """
        Cancel a running task (synchronous API).
        
        Args:
            username: User identifier
            task_id: Task identifier
        
        Returns:
            bool: True if task was cancelled successfully
        """
        if not self._validate_task(username, task_id):
            return False
            
        task = self._tasks[username][task_id].task
        self._run_async(task.cancel())
        return True

    def get_task_status(self, username: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current task status (synchronous API).
        
        Args:
            username: User identifier
            task_id: Task identifier
            
        Returns:
            dict: Task status information or None if task not found
        """
        if not self._validate_task(username, task_id):
            return None
            
        record = self._tasks[username][task_id]
        task = record.task
        
        return {
            "task_id": task_id,
            "file_name": record.file_name,
            "status": task.status.value,
            "metadata": {
                "total_iterations": task.metadata.total_iterations,
                "current_iteration": task.metadata.current_iteration,
                "error_count": task.metadata.error_count
            },
            "error": task.error,
            **task.get_last_state()
        }

    def get_user_tasks(self, username: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a user (synchronous API).
        
        Args:
            username: User identifier
            
        Returns:
            list: List of task information dictionaries
        """
        if username not in self._tasks:
            return []
            
        return [
            {
                "task_id": record.task_id,
                "file_name": record.file_name,
                "status": record.task.status.value,
                "metadata": {
                    "total_iterations": record.task.metadata.total_iterations,
                    "current_iteration": record.task.metadata.current_iteration,
                    "error_count": record.task.metadata.error_count
                }
            }
            for record in self._tasks[username].values()
        ]

    def delete_task(self, username: str, task_id: str) -> bool:
        """
        Delete a task (synchronous API).
        Will cancel the task first if it's running.
        
        Args:
            username: User identifier
            task_id: Task identifier
            
        Returns:
            bool: True if task was deleted successfully
        """
        if not self._validate_task(username, task_id):
            return False
            
        task = self._tasks[username][task_id].task
        if task.status.value == "RUNNING":
            self.cancel_task(username, task_id)
            
        del self._tasks[username][task_id]
        if not self._tasks[username]:
            del self._tasks[username]
            
        return True

    def provide_feedback(self, username: str, task_id: str, feedback: str) -> bool:
        """
        Provide feedback for task improvement (synchronous API).
        
        Args:
            username: User identifier
            task_id: Task identifier
            feedback: User feedback string
            
        Returns:
            bool: True if feedback was processed successfully
        """
        if not self._validate_task(username, task_id):
            return False
            
        task = self._tasks[username][task_id].task
        self._run_async(task.provide_feedback(feedback))
        return True

    def _validate_task(self, username: str, task_id: str) -> bool:
        """Helper method to validate task existence"""
        return (
            username in self._tasks and
            task_id in self._tasks[username]
        )

    def shutdown(self):
        """
        Clean shutdown of the task manager.
        Cancels running tasks and stops the event loop.
        """
        # Cancel all running tasks
        for username in list(self._tasks.keys()):
            for task_id in list(self._tasks[username].keys()):
                self.cancel_task(username, task_id)
        
        # Stop the event loop thread
        self._async_thread.stop()
        self._async_thread.join()
        
        # Shutdown thread pool
        self._executor.shutdown(wait=True)

task_manager = Image2ExcelTaskManager()