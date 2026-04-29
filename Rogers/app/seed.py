"""种子数据：启动时自动创建测试账户"""
from sqlalchemy.orm import Session
from src.fitme.utils.database import SessionLocal
from src.fitme.models import User, UserSettings
from src.fitme.services.auth_service import AuthService


TEST_ACCOUNTS = [
    {"name": "测试用户", "email": "user@test.com", "password": "password123", "role": "user"},
]


def seed_test_accounts():
    """如果数据库为空，则插入测试账户"""
    db: Session = SessionLocal()
    try:
        if db.query(User).count() == 0:
            for account in TEST_ACCOUNTS:
                user = User(
                    name=account["name"],
                    email=account["email"],
                    password_hash=AuthService.hash_password(account["password"]),
                    role=account["role"],
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                db.add(UserSettings(user_id=user.user_id))
                db.commit()
            print(f"Seed: created {len(TEST_ACCOUNTS)} test accounts.")
        else:
            print("Seed: users already exist, skipping.")
    finally:
        db.close()
