import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "JobContact")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456@localhost:3306/job_contact_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret_key_default")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/")

settings = Settings()

