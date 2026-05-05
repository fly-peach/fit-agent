"""FitMe Core Configuration"""
import logging
import secrets
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings

_DEFAULT_JWT_SECRET = "your-secret-key-change-in-production"

logger = logging.getLogger("fitagent.config")

# 项目根目录 - rogers/
_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 统一的数据根目录 - rogers/data
_DATA_DIR = _BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings"""
    # 统一数据目录
    DATA_DIR: Path = _DATA_DIR

    # Base DB (基础数据库：健身动作库、食物库等系统预置数据)
    BASE_DB_URL: str = f"sqlite:///{_DATA_DIR / 'fitbase.db'}"

    # User DB (用户数据库：用户数据、自定义数据等)
    USER_DB_URL: str = f"sqlite:///{_DATA_DIR / 'fituser.db'}"

    # 兼容旧代码 - 指向 user_db
    DATABASE_URL: str = f"sqlite:///{_DATA_DIR / 'fituser.db'}"

    # Agent工作区目录
    AGENT_DB_DIR: Path = _DATA_DIR / "agent_db"

    JWT_SECRET_KEY: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS 跨域配置：逗号分隔允许的前端域名
    CORS_ORIGINS: str = ""

    APP_NAME: str = "FitAgent"
    APP_VERSION: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        if self.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "必须设置 JWT_SECRET_KEY！请在 .env 中配置 "
                "(生成命令: python -c \"import secrets; print(secrets.token_hex(32))\")"
            )

        if not self.CORS_ORIGINS:
            raise ValueError(
                "必须设置 CORS_ORIGINS！请在 .env 中配置允许的跨域域名（逗号分隔）"
            )

        return self


settings = Settings()
