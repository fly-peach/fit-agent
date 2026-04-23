"""Auth Service"""
from sqlalchemy.orm import Session
from typing import Optional
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from ..models import User, UserSettings
from ..schemas.auth import LoginRequest, RegisterRequest
from ..core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)

    @staticmethod
    def create_token(user_id: int, email: str) -> str:
        """生成JWT Token"""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """解码JWT Token"""
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def login(db: Session, data: LoginRequest) -> Optional[dict]:
        """用户登录"""
        user = db.query(User).filter(
            User.email == data.email,
            User.deleted_at.is_(None)
        ).first()

        if user and AuthService.verify_password(data.password, user.password_hash):
            token = AuthService.create_token(user.user_id, user.email)
            return {
                "token": token,
                "user": {
                    "userId": user.user_id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
            }
        return None

    @staticmethod
    def register(db: Session, data: RegisterRequest) -> Optional[dict]:
        """用户注册"""
        # 检查邮箱是否已存在
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            return None

        # 创建用户
        user = User(
            name=data.name,
            email=data.email,
            password_hash=AuthService.hash_password(data.password),
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 创建用户设置
        settings = UserSettings(user_id=user.user_id)
        db.add(settings)
        db.commit()

        # 返回 token 和用户信息
        token = AuthService.create_token(user.user_id, user.email)
        return {
            "token": token,
            "user": {
                "userId": user.user_id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        }

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """从Token获取用户"""
        payload = AuthService.decode_token(token)
        if payload:
            return db.query(User).filter(
                User.user_id == payload["user_id"],
                User.deleted_at.is_(None)
            ).first()
        return None