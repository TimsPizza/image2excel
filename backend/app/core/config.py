import logging
from typing import Any, Dict, List
from dotenv import load_dotenv
import os


class EnvConfig:
    def __init__(self):
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self._load()

    def _load(self):
        if not load_dotenv():
            raise ValueError("Couldn't load .env file")
        self._loaded = True

    @property
    def OPENAI_COMPATIBLE_API_KEY(self) -> str:
        self._ensure_loaded()
        return os.getenv("OPENAI_COMPATIBLE_API_KEY")

    @property
    def JWT_SECRET_KEY(self) -> str:
        self._ensure_loaded()
        return os.getenv("JWT_SECRET_KEY")

    @property
    def JWT_ALGORITHM(self) -> str:
        self._ensure_loaded()
        return os.getenv("JWT_ALGORITHM")

    @property
    def JWT_EXPIRE_MINUTES(self) -> str:
        self._ensure_loaded()
        return os.getenv("JWT_EXPIRE_MINUTES")

    @property
    def TOTP_SECRET_KEY(self) -> str:
        self._ensure_loaded()
        return os.getenv("TOTP_SECRET_KEY")

    @property
    def BACKEND_PORT(self) -> str:
        self._ensure_loaded()
        return os.getenv("BACKEND_PORT")

    @property
    def CORS_ORIGINS(self) -> List[str]:
        self._ensure_loaded()
        cors_str = os.getenv("CORS_ORIGINS")
        return EnvConfig._parse_cors(cors_str)
    
    @property
    def BACKEND_HOST(self) -> str:
        self._ensure_loaded()
        return os.getenv("BACKEND_HOST")
    
    @staticmethod
    def _parse_cors(v: Any) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

ENV_CONFIG = EnvConfig()
