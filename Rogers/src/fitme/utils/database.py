"""Database Utility - Support for base_db and user_db"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings


def _ensure_db_dir(db_url: str):
    """Ensure database directory exists for SQLite"""
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "", 1)
        if not db_path.startswith(":memory"):
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)


# ========== Base DB (系统基础数据 ==========
_ensure_db_dir(settings.BASE_DB_URL)
if settings.BASE_DB_URL.startswith("sqlite"):
    base_engine = create_engine(settings.BASE_DB_URL, connect_args={"check_same_thread": False})
else:
    base_engine = create_engine(settings.BASE_DB_URL, pool_pre_ping=True)

BaseSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=base_engine)


# ========== User DB (用户数据 ==========
_ensure_db_dir(settings.USER_DB_URL)
if settings.USER_DB_URL.startswith("sqlite"):
    user_engine = create_engine(settings.USER_DB_URL, connect_args={"check_same_thread": False})
else:
    user_engine = create_engine(settings.USER_DB_URL, pool_pre_ping=True)

UserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)


# ========== Compatibility - Default to User DB ==========
engine = user_engine
SessionLocal = UserSessionLocal


def get_db():
    """获取用户数据库会话（兼容旧代码）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_base_db():
    """获取基础数据库会话"""
    db = BaseSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_db():
    """获取用户数据库会话"""
    db = UserSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Context managers for convenience
class BaseDBContext:
    """Base DB 上下文管理器"""

    def __enter__(self):
        self.db = BaseSessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


class UserDBContext:
    """User DB 上下文管理器"""

    def __enter__(self):
        self.db = UserSessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
