from pydantic import BaseModel


class AuthRequestDTO(BaseModel):
    totp: str
    
class AuthResponseDTO(BaseModel):
    token: str    
