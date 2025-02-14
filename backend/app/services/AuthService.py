import datetime
from jose import jwt

from app.core.security import TOTP
from core.config import ENV_CONFIG


class AuthService:
    @staticmethod
    def create_access_token() -> str:
        expire = datetime.now() + datetime.timedelta(
            minutes=ENV_CONFIG.jwt_expire_minutes
        )
        expire = expire.timestamp()
        to_encode = {"exp": expire}
        return jwt.encode(
            to_encode, ENV_CONFIG.jwt_secret_key, algorithm=ENV_CONFIG.jwt_algorithm
        )

    @staticmethod
    def validate_totp(totp: str) -> bool:
        return TOTP.validate(totp)