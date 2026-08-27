from pydantic_settings import BaseSettings, SettingsConfigDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class Settings(BaseSettings):

    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: int
    DB_NAME: str

    WP_DB_HOST: str
    WP_DB_USER: str
    WP_DB_PASSWORD: str    
    WP_DB_PORT: int
    WP_DB_NAME: str

    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True
    APP_TIMEZONE: str = "America/Bogota"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    INTRANET_SSO_SECRET: str
    INTRANET_SSO_EXPIRE_SECONDS: int = 120

    PUBLIC_BASE_URL: str = "http://localhost:5173"
    UPLOAD_DIR: str = "uploads"

    ONLYOFFICE_PUBLIC_URL: str = "http://localhost:8085"
    ONLYOFFICE_STORAGE_BASE_URL: str = "http://host.docker.internal:8000"
    ONLYOFFICE_JWT_SECRET: str | None = None
    ONLYOFFICE_TOKEN_EXPIRE_MINUTES: int = 30
    ONLYOFFICE_TEMP_FILE_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "Sistema de Registro de Asistencia"
    SMTP_REPLY_TO: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: int = 15

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()

try:
    APP_TIMEZONE_INFO = ZoneInfo(settings.APP_TIMEZONE)
except ZoneInfoNotFoundError as error:
    raise RuntimeError(
        f"No se pudo cargar la zona horaria '{settings.APP_TIMEZONE}'. "
        "Instale las dependencias del backend, incluido el paquete tzdata."
    ) from error
