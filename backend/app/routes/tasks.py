from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from fastapi import HTTPException, status
from app.services.AuthService import AuthService
from app.core.config import ENV_CONFIG
from app.dtos.TaskDTO import (
    CancelTaskRequestDTO,
    CancelTaskResponseDTO,
    CreateTaskRequestDTO,
    CreateTaskResponseDTO,
    DeleteTaskResponseDTO,
    GetTaskStatusRequestDTO,
    GetTaskStatusResponseDTO,
)
from app.services.TaskService import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks management"])


@router.post("/create", response_model=CreateTaskResponseDTO)
async def create_task(
    image_fileNames: List[str],
    form_data: CreateTaskRequestDTO,
    username: str = Depends(AuthService.verify_access_token),
) -> Optional[CreateTaskResponseDTO]:
    # returns a task_id
    task_id = TaskService.create_task(username, image_fileNames)
    if not task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not created",
        )
    return CreateTaskResponseDTO(
        task_id=task_id, message="Task created successfully", success=True
    )
        


@router.get("/status/{task_id}", response_model=GetTaskStatusResponseDTO)
async def get_task_status(
    task_id: str,
    username: str = Depends(AuthService.verify_access_token),
) -> Optional[GetTaskStatusResponseDTO]:
    # returns the status of the task
    status = TaskService.get_status(username, task_id)
    if status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return GetTaskStatusResponseDTO(
        task_id=task_id, status=status, message="Task status retrieved successfully"
    )


@router.post("/delete", response_model=DeleteTaskResponseDTO)
async def delete_task(
    task_id: str,
    username: str = Depends(AuthService.verify_access_token),
) -> Optional[DeleteTaskResponseDTO]:
    # Optionally include a success message
    success = TaskService.delete_task(username, task_id)
    return DeleteTaskResponseDTO(message=f"Task {task_id} deleted successfully", success=success)


@router.post("/cancel", response_model=CancelTaskResponseDTO)
async def cancel_task(
    task_id: str,
    form_data: CancelTaskRequestDTO,
    username: str = Depends(AuthService.verify_access_token),
) -> Optional[CancelTaskResponseDTO]:
    success = TaskService.cancel_task(username, task_id)
    return CancelTaskResponseDTO(
        message=f"Task {task_id} cancellation successful", success=success
    )
