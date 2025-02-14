from typing import List
from pydantic import BaseModel

class CreateTaskRequestDTO(BaseModel):
    file_name: str
    
class CreateTaskResponseDTO(BaseModel):
    message: str
    task_id: str
    success: bool
    
class GetTaskStatusRequestDTO(BaseModel):
    task_id: str
    
class GetTaskStatusResponseDTO(BaseModel):
    task_id: str
    status: str
    message: str
    
class CancelTaskRequestDTO(BaseModel):
    task_id: str
    
class CancelTaskResponseDTO(BaseModel):
    message: str
    success: bool
    
class DeleteTaskResponseDTO(BaseModel):
    message: str
    success: bool