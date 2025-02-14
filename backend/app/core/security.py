import pyotp

from app.core.config import ENV_CONFIG


class Totp:
    def __init__(self):
        self.totp = pyotp.TOTP(ENV_CONFIG.TOTP_SECRET_KEY)

    def validate(self, token: str) -> bool:
        return self.totp.verify(token)


TOTP = Totp()