from datetime import datetime, timedelta
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from app.core.security import TOTP
from app.core.config import ENV_CONFIG

http_bearer = HTTPBearer()


class AuthService:
    @staticmethod
    def create_access_token() -> str:
        expire = datetime.now() + timedelta(minutes=ENV_CONFIG.JWT_EXPIRE_MINUTES)
        expire = expire.timestamp()
        to_encode = {"exp": expire}
        return jwt.encode(
            to_encode, ENV_CONFIG.JWT_SECRET_KEY, algorithm=ENV_CONFIG.JWT_ALGORITHM
        )

    @staticmethod
    def validate_totp(totp: str) -> bool:
        return TOTP.validate(totp)

    @staticmethod
    def verify_access_token(token: str) -> dict:
        try:
            return jwt.decode(
                token, ENV_CONFIG.JWT_SECRET_KEY, algorithms=[ENV_CONFIG.JWT_ALGORITHM]
            )
        except:
            return None

    @staticmethod
    def validate_access_token(
        credentials: HTTPAuthorizationCredentials = Security(http_bearer),
    ):
        # this is used as depends in the routes
        token = credentials.credentials
        decoded_token = AuthService.verify_access_token(token)
        if decoded_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
