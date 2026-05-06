"""一键初始化所有数据库

通常无需手动运行，应用启动时会自动初始化。
此脚本用于首次部署或重置数据库。

用法：
    cd rogers
    python scripts/init_all.py
"""
import sys
from pathlib import Path


def main():
    print("=" * 50)
    print("  FitAgent 数据库初始化")
    print("=" * 50)

    # 1. fitbase.db
    print("\n[1/2] 基础数据库 (fitbase.db)...")
    from src.fitme.seed import seed_base_db
    result = seed_base_db()
    for table, count in result.items():
        if count > 0:
            print(f"  ✓ {table}: 导入 {count} 条")
        else:
            print(f"  - {table}: 已有数据，跳过")

    # 2. fituser.db
    print("\n[2/2] 用户数据库 (fituser.db)...")
    from src.fitme.models.user_db import Base
    from src.fitme.utils.database import user_engine
    Base.metadata.create_all(bind=user_engine)
    print("  ✓ 表结构创建完成")

    # 测试账户
    from src.fitme.models import User
    from src.fitme.utils.database import UserSessionLocal
    db = UserSessionLocal()
    try:
        if db.query(User).count() == 0:
            from src.fitme.services.auth_service import AuthService
            from src.fitme.models import UserSettings
            user = User(
                name="测试用户",
                email="user@test.com",
                password_hash=AuthService.hash_password("password123"),
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            db.add(UserSettings(user_id=user.user_id))
            db.commit()
            print("  ✓ 创建测试账户: user@test.com / password123")
        else:
            print("  - 用户已存在，跳过")
    finally:
        db.close()

    print("\n" + "=" * 50)
    print("  ✅ 初始化完成！运行 python run.py 启动服务")
    print("=" * 50)


if __name__ == "__main__":
    main()
