"""Database Utility"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

url = settings.DATABASE_URL
# SQLite: ensure parent directory exists
if url.startswith("sqlite"):
    db_path = url.replace("sqlite:///", "", 1)
    if not db_path.startswith(":memory"):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

if url.startswith("sqlite"):
    engine = create_engine(url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()