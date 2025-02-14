from datetime import datetime, timedelta
import random
import string
from typing import Dict, Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from app.core.security import TOTP
from app.core.config import ENV_CONFIG
import hashlib

http_bearer = HTTPBearer()

"""
username: {
    "access_token": str,
    "refresh_token": str,
    "client_hash": str
}
"""
user_records: Dict[str, Dict[str, str]] = {}


class AuthService:

    @staticmethod
    def has_user(username: str) -> bool:
        return username in user_records.keys()

    @staticmethod
    def create_access_token(username: str) -> str:
        expire = datetime.now() + timedelta(minutes=ENV_CONFIG.JWT_EXPIRE_MINUTES)
        expire = expire.timestamp()
        to_encode = {"exp": expire, "sub": username, "iat": datetime.now().timestamp()}
        token = jwt.encode(
            to_encode, ENV_CONFIG.JWT_SECRET_KEY, algorithm=ENV_CONFIG.JWT_ALGORITHM
        )
        AuthService.invalidate_access_token(username)
        user_records[username]["access_token"] = token
        return token

    @staticmethod
    def create_blank_user_record(username: str):
        user_records[username] = {
            "access_token": None,
            "refresh_token": None,
            "client_hash": None,
        }

    @staticmethod
    def get_client_hash(user_agent: str) -> str:
        # Generate a 16-character hash from user agent
        hash_obj = hashlib.md5(user_agent.encode())
        return hash_obj.hexdigest()[:16]

    @staticmethod
    def invalidate_refresh_token(username: str) -> str:
        user_records[username]["refresh_token"] = None

    @staticmethod
    def invalidate_access_token(username: str):
        user_records[username]["access_token"] = None

    @staticmethod
    def create_refresh_token(username: str, client_hash: str) -> str:
        # client_hash is a string of length 16
        # invalidate any existing refresh token for this client_hash
        prefix = "".join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(16)
        )
        token = f"{prefix}.{client_hash}"
        user_records[username]["refresh_token"] = token
        user_records[username]["client_hash"] = client_hash
        return token

    @staticmethod
    def validate_totp(totp: str) -> bool:
        return TOTP.validate(totp)

    @staticmethod
    def _verify_access_token(token: str) -> Optional[str]:
        # returns username if token is valid, None otherwise
        try:
            decoded = jwt.decode(
                token, ENV_CONFIG.JWT_SECRET_KEY, algorithms=[ENV_CONFIG.JWT_ALGORITHM]
            )
            if (
                decoded["sub"] in user_records.keys()
                and decoded["exp"] > datetime.now().timestamp()
                and user_records[decoded["sub"]]["access_token"] == token
            ):
                return decoded["sub"]
            else:
                return None
        except Exception as e:
            return None

    @staticmethod
    def verify_access_token(
        credentials: HTTPAuthorizationCredentials = Security(http_bearer),
    ) -> Optional[str]:
        # this is used as depends in the routes
        token = credentials.credentials
        username = AuthService._verify_access_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return username

    @staticmethod
    def verify_refresh_token(client_hash: str, refresh_token: str) -> Optional[str]:
        # returns username if token is valid, None otherwise
        for username, record in user_records.items():
            print(f"Checking {username}---{record}")
            if (
                record["client_hash"] == client_hash
                and record["refresh_token"] == refresh_token
            ):
                return username
        return None
