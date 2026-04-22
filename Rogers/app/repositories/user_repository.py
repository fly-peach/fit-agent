from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_account(self, account: str) -> User | None:
        stmt = select(User).where(or_(User.email == account, User.phone == account))
        return self.db.execute(stmt).scalar_one_or_none()

    def create_user(
        self,
        *,
        email: str | None,
        phone: str | None,
        password_hash: str,
        name: str,
    ) -> User:
        user = User(
            email=email,
            phone=phone,
            password_hash=password_hash,
            name=name,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
