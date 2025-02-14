from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request

from app.dtos.AuthDTO import (
    AuthRequestDTO,
    AuthResponseDTO,
    RefreshTokenRequestDTO,
    RefreshTokenResponseDTO,
)
from app.services.AuthService import AuthService

router = APIRouter(prefix="/auth", tags=["TOTP Authentication"])


@router.post("/totp", response_model=AuthResponseDTO)
async def access_token(request: Request, formData: AuthRequestDTO):
    user_agent = request.headers.get("user-agent")
    totp = formData.totp
    username = formData.username
    if not AuthService.validate_totp(totp):
        raise HTTPException(status_code=401, detail="Invalid TOTP")
    if AuthService.has_user(username):
        raise HTTPException(status_code=400, detail="Username already in use")
    try:
        AuthService.create_blank_user_record(username)
        access_token = AuthService.create_access_token(username)
        client_hash = AuthService.get_client_hash(user_agent)
        refresh_token = AuthService.create_refresh_token(
            username=username, client_hash=client_hash
        )
        return AuthResponseDTO(access_token=access_token, refresh_token=refresh_token)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=RefreshTokenResponseDTO)
async def refresh_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid refresh token")

    refresh_token = auth_header.split(" ")[1]
    user_agent = request.headers.get("user-agent")
    print(user_agent)
    try:
        client_hash = AuthService.get_client_hash(user_agent)
        username = AuthService.verify_refresh_token(
            client_hash=client_hash, refresh_token=refresh_token
        )
        if not username:
            raise HTTPException(
                status_code=401, detail="Invalid or expired refresh token"
            )
        AuthService.invalidate_refresh_token(username)
        AuthService.invalidate_access_token(username)
        new_refresh_token = AuthService.create_refresh_token(username, client_hash)
        new_access_token = AuthService.create_access_token(username)
        return RefreshTokenResponseDTO(
            access_token=new_access_token, refresh_token=new_refresh_token
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unknown error occurred")
