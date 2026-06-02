from datetime import datetime, timedelta, timezone
from app.infrastructure.db.config import settings
import jwt

class JwtService:

    @staticmethod
    def createToken(payload: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

        data = payload.copy()
        data.update({"exp": expire})

        return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decodeToken(token: str) -> dict:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])