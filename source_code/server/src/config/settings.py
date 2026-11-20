from pathlib import Path
from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SERVER_DIR / ".env", env_file_encoding="utf-8", extra="ignore")
    APP_NAME: str = "JobContact"
    DEBUG: bool = False
    DATABASE_URL: str = "mysql+pymysql://root@localhost:3306/job_contact_db"
    SECRET_KEY: str = "secret_key_default"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = "uploads/"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@jobcontact.local"
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False
    FRONTEND_URL: str = "http://localhost:5500"

    @field_validator("FRONTEND_URL")
    @classmethod
    def parse_frontend_url(cls, value):
        url = HttpUrl(value)
        if url.path not in (None, "/") or url.query or url.fragment or url.username or url.password:
            raise ValueError("FRONTEND_URL must be an HTTP(S) origin without a path, query or credentials")
        return str(url).rstrip("/")

    @property
    def cors_origins(self):
        origins = [self.FRONTEND_URL]
        local_origins = ["http://localhost:5500", "http://127.0.0.1:5500"]
        if self.FRONTEND_URL in local_origins:
            origins = local_origins
        return origins

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        # Some Windows hosts export DEBUG=release independently of this app.
        if isinstance(value,str) and value.lower() in ("release","production"):
            return False
        return value

settings = Settings()
