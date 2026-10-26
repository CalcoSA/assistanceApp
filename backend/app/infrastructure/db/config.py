from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
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

    ONLYOFFICE_PUBLIC_URL: str = "http://localhost:8086"
    ONLYOFFICE_STORAGE_BASE_URL: str = "http://host.docker.internal:8000"
    ONLYOFFICE_JWT_SECRET: str | None = None
    ONLYOFFICE_TOKEN_EXPIRE_MINUTES: int = 30
    ONLYOFFICE_TEMP_FILE_EXPIRE_MINUTES: int = 60
    ONLYOFFICE_TEMP_DIR: str | None = None

    # GCS is opt-in: validate these only when constructing its storage service.
    GCS_ENVIRONMENT: str | None = None
    GCS_PROJECT_ID: str | None = None
    GCS_BUCKET: str | None = None
    GCS_PREFIX: str | None = None
    GCS_AUTH_MODE: str | None = None
    GCS_ENDPOINT: str = "https://storage.googleapis.com"
    GCS_HMAC_ACCESS_KEY: SecretStr | None = Field(default=None, repr=False)
    GCS_HMAC_SECRET_KEY: SecretStr | None = Field(default=None, repr=False)
    GCS_SIGNING_SERVICE_ACCOUNT_EMAIL: str | None = None
    GCS_TIMEOUT_SECONDS: float = 30

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
        hide_input_in_errors=True,
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
