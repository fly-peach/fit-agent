from datetime import date

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.daily_metrics import DailyMetrics
from app.schemas.daily_metrics import DailyMetricsUpsert


class DailyMetricsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_date(self, *, user_id: int, record_date: date) -> DailyMetrics | None:
        stmt = select(DailyMetrics).where(
            and_(DailyMetrics.user_id == user_id, DailyMetrics.record_date == record_date)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(self, *, user_id: int, record_date: date, payload: DailyMetricsUpsert) -> DailyMetrics:
        obj = self.get_by_user_and_date(user_id=user_id, record_date=record_date)
        if obj:
            obj.weight = payload.weight
            obj.body_fat_rate = payload.body_fat_rate
            obj.bmi = payload.bmi
        else:
            obj = DailyMetrics(
                user_id=user_id,
                record_date=record_date,
                weight=payload.weight,
                body_fat_rate=payload.body_fat_rate,
                bmi=payload.bmi,
            )
            self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_by_user(
        self, *, user_id: int, from_date: date | None, to_date: date | None, skip: int = 0, limit: int = 100
    ) -> list[DailyMetrics]:
        stmt = select(DailyMetrics).where(DailyMetrics.user_id == user_id)
        if from_date is not None:
            stmt = stmt.where(DailyMetrics.record_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(DailyMetrics.record_date <= to_date)
        stmt = stmt.order_by(desc(DailyMetrics.record_date)).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
