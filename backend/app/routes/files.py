from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/files", tags=["Files upload/download"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return {"message": "File uploaded successfully"}


@router.get("/download")
async def download_file(file_hashtag: str):
    return {"message": f"File '{file_hashtag}' downloaded successfully"}
