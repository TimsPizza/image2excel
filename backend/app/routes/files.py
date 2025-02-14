from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from fastapi import HTTPException, status
import os
from app.services.AuthService import AuthService
from app.core.config import ENV_CONFIG

router = APIRouter(prefix="/files", tags=["Files upload/download"])


@router.post("/upload", dependencies=[Depends(AuthService.validate_access_token)])
async def upload_file(file: UploadFile = File(...), file_name: str = None):
    upload_dir = os.path.normpath(
        os.path.join(ENV_CONFIG.SCRIPT_ROOT_DIR, "app/image2excel/files/uploaded")
    )
    if not file_name:
        file_name = file.filename
    file_path = os.path.join(upload_dir, file_name)

    os.makedirs(upload_dir, exist_ok=True)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"message": f"File '{file_name}' uploaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/download", dependencies=[Depends(AuthService.validate_access_token)])
async def download_file(file_name: str):
    download_dir = os.path.normpath(
        os.path.join(ENV_CONFIG.SCRIPT_ROOT_DIR, "app/image2excel/files/generated")
    )
    file_path = os.path.join(download_dir, file_name)
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return FileResponse(
        file_path, media_type="application/octet-stream", filename=file_name
    )
