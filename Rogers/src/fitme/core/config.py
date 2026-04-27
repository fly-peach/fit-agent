"""FitMe Core Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    # Database (SQLite for development)
    DATABASE_URL: str = "sqlite:///./fitagent.db"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # App
    APP_NAME: str = "FitAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # AI (these are for the agent module, ignored here)
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    model: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()