"""Harness 专用 fixtures — DB 隔离、事务回滚、测试用户。"""
from contextlib import contextmanager
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository

TEST_USER_EMAIL = "harness@test.com"


@contextmanager
def isolated_db_session():
    """提供事务隔离的 DB session：每个 Task 执行后自动回滚，不污染生产数据。"""
    db = SessionLocal()
    try:
        nested = db.begin_nested()
        yield db
        nested.commit()
    except Exception:
        nested.rollback()
        raise
    finally:
        db.close()


def get_or_create_test_user(db):
    """获取或创建测试用户"""
    import bcrypt
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(TEST_USER_EMAIL)
    if not user:
        pw_hash = bcrypt.hashpw("harness_test_123".encode(), bcrypt.gensalt()).decode()
        user = user_repo.create_user(
            email=TEST_USER_EMAIL,
            phone=None,
            password_hash=pw_hash,
            name="Harness Test User",
        )
    return user
