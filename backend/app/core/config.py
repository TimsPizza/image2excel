import logging
from typing import Any, Dict, List
from dotenv import load_dotenv
import os


class EnvConfig:
    def __init__(self):
        self._loaded = False
        self.SCRIPT_ROOT_DIR = None

    def _ensure_loaded(self):
        if not self._loaded:
            self._load()

    def _load(self):
        if not load_dotenv():
            raise ValueError("Couldn't load .env file")
        self._loaded = True

    @property
    def OPENAI_API_KEY(self) -> str:
        self._ensure_loaded()
        return os.getenv("OPENAI_API_KEY")

    @property
    def JWT_SECRET_KEY(self) -> str:
        self._ensure_loaded()
        return os.getenv("JWT_SECRET_KEY")

    @property
    def JWT_ALGORITHM(self) -> str:
        self._ensure_loaded()
        return os.getenv("JWT_ALGORITHM")

    @property
    def JWT_EXPIRE_MINUTES(self) -> int:
        self._ensure_loaded()
        try:
            minutes = int(os.getenv("JWT_EXPIRE_MINUTES"))
            return minutes
        except ValueError:
            raise ValueError("JWT_EXPIRE_MINUTES must be an integer")

    @property
    def TOTP_SECRET_KEY(self) -> str:
        self._ensure_loaded()
        return os.getenv("TOTP_SECRET_KEY")

    @property
    def BACKEND_PORT(self) -> int:
        self._ensure_loaded()
        try:
            port = int(os.getenv("BACKEND_PORT"))
            return port
        except ValueError:
            raise ValueError("BACKEND_PORT must be an integer")
        
    @property
    def CORS_ORIGINS(self) -> List[str]:
        self._ensure_loaded()
        cors_str = os.getenv("CORS_ORIGINS")
        return EnvConfig._parse_cors(cors_str)
    
    @property
    def BACKEND_HOST(self) -> str:
        self._ensure_loaded()
        return os.getenv("BACKEND_HOST")
    
    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        self._ensure_loaded()
        try:
            days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))
            return days
        except ValueError:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be an integer")
    
    
    @staticmethod
    def _parse_cors(v: Any) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

ENV_CONFIG = EnvConfig()
