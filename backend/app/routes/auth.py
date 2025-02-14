from email.policy import HTTP
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dtos.AuthDTO import AuthRequestDTO, AuthResponseDTO
from app.services.AuthService import AuthService

router = APIRouter(prefix="/auth", tags=["TOTP Authentication"])


@router.post("/totp", response_model=AuthResponseDTO)
async def access_token(formData: AuthRequestDTO):
    totp = formData.totp
    if AuthService.validate_totp(totp):
        access_token = AuthService.create_access_token()
        return AuthResponseDTO(access_token=access_token)
    else:
        raise HTTPException(status_code=401, detail="Invalid TOTP")
    