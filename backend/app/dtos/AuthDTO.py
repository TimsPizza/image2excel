from pydantic import BaseModel


class AuthRequestDTO(BaseModel):
    # username is customized and only refers to a access_token
    username: str
    totp: str
    
class AuthResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    
class RefreshTokenRequestDTO(BaseModel):
    refresh_token: str
    
class RefreshTokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str

