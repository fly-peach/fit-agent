from datetime import date

from app.models.user import User
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.schemas.daily_metrics import DailyMetricsUpsert


class DailyMetricsService:
    def __init__(self, repo: DailyMetricsRepository) -> None:
        self.repo = repo

    def upsert(self, *, current_user: User, record_date: date, payload: DailyMetricsUpsert):
        return self.repo.upsert(user_id=current_user.id, record_date=record_date, payload=payload)

    def list(
        self, *, current_user: User, from_date: date | None, to_date: date | None, skip: int = 0, limit: int = 100
    ):
        return self.repo.list_by_user(
            user_id=current_user.id, from_date=from_date, to_date=to_date, skip=skip, limit=limit
        )
