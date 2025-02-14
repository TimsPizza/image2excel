from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from fastapi import HTTPException, status
import os
from app.services.AuthService import AuthService
from app.core.config import ENV_CONFIG

router = APIRouter(prefix="/tasks", tags=["Tasks management"])


@router.post("/create")
async def create_task(
    image_file_names: List[str],
    username: str = Depends(AuthService.verify_access_token),
) -> str:
    # returns a task_id
    pass
  
@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    username: str = Depends(AuthService.verify_access_token),
) -> str:
    # returns the status of the task
    pass
  
@router.get("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    username: str = Depends(AuthService.verify_access_token),
) -> str:
    # returns the status of the task
    pass
