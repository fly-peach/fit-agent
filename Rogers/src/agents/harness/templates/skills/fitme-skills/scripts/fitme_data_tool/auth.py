"""Fitme 数据工具 - Token 验证

共享的 Token 验证功能。
"""
from __future__ import annotations

from typing import Optional, Tuple
from contextlib import contextmanager

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent))

from sqlalchemy.orm import Session
from src.fitme.utils.database import SessionLocal
from src.fitme.services.auth_service import AuthService
from src.fitme.models import User


@contextmanager
def get_db_session():
    """获取数据库 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(token: str) -> Tuple[Optional[int], Optional[dict]]:
    """
    验证 Token 并返回 user_id 或错误

    Returns:
        (user_id, error) - 成功时 user_id 有值，失败时 error 有值
    """
    # 处理 "Bearer " 前缀
    if token.startswith("Bearer "):
        token = token[7:]

    # 解码 token
    user_id = AuthService.get_user_id_from_token(token)
    if not user_id:
        return None, {"success": False, "error": "无效或已过期的 Token"}

    # 验证用户存在
    with get_db_session() as db:
        user = db.query(User).filter(
            User.user_id == user_id,
            User.deleted_at.is_(None)
        ).first()
        if not user:
            return None, {"success": False, "error": "用户不存在或已被删除"}

    return user_id, None
