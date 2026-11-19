import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SERVER_DIR / os.getenv("VIECO_ENV_FILE", ".env"), env_file_encoding="utf-8", extra="ignore")
    APP_NAME: str = "JobContact"
    DEBUG: bool = False
    DATABASE_URL: str = "mysql+pymysql://root@localhost:3306/job_contact_db"
    DATABASE_SSL: bool = False
    DATABASE_SSL_CA: str = ""
    SECRET_KEY: str = "secret_key_default"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = "uploads/"
    SERVE_FRONTEND: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@jobcontact.local"
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False
    FRONTEND_URL: str = "http://localhost:5500"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        # Some Windows hosts export DEBUG=release independently of this app.
        if isinstance(value,str) and value.lower() in ("release","production"):
            return False
        return value

settings = Settings()
