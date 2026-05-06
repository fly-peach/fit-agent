"""命令行脚本：手动初始化 fituser.db

通常无需手动运行，应用启动时会自动初始化。
此脚本用于首次部署或重置用户数据库。

用法：
    cd rogers
    python scripts/init_user_db.py
    python scripts/init_user_db.py --seed   # 含测试账户
"""
import sys
from pathlib import Path


from src.fitme.models.user_db import Base, User, UserSettings
from src.fitme.utils.database import user_engine, UserSessionLocal
from src.fitme.services.auth_service import AuthService

TEST_ACCOUNTS = [
    {"name": "测试用户", "email": "user@test.com", "password": "password123", "role": "user"},
]


def init_tables():
    Base.metadata.create_all(bind=user_engine)
    print("  ✓ 表结构创建完成")


def seed_test_accounts():
    db = UserSessionLocal()
    try:
        if db.query(User).count() > 0:
            print("  - 用户已存在，跳过")
            return
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
        print(f"  ✓ 创建了 {len(TEST_ACCOUNTS)} 个测试账户")
    finally:
        db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="同时插入测试账户")
    args = parser.parse_args()

    print("初始化 fituser.db...")
    init_tables()
    if args.seed:
        seed_test_accounts()
    print("完成！")


if __name__ == "__main__":
    main()
