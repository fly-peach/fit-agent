from datetime import date

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.daily_workout_plan import DailyWorkoutPlan
from app.schemas.daily_workout_plan import DailyWorkoutPlanUpsert


class DailyWorkoutPlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_date(self, *, user_id: int, record_date: date) -> DailyWorkoutPlan | None:
        stmt = select(DailyWorkoutPlan).where(
            and_(DailyWorkoutPlan.user_id == user_id, DailyWorkoutPlan.record_date == record_date)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(self, *, user_id: int, record_date: date, payload: DailyWorkoutPlanUpsert) -> DailyWorkoutPlan:
        obj = self.get_by_user_and_date(user_id=user_id, record_date=record_date)
        items = [i.model_dump() for i in payload.items]
        if obj:
            obj.plan_title = payload.plan_title
            obj.items = items
            obj.duration_minutes = payload.duration_minutes
            obj.is_completed = payload.is_completed
            obj.notes = payload.notes
        else:
            obj = DailyWorkoutPlan(
                user_id=user_id,
                record_date=record_date,
                plan_title=payload.plan_title,
                items=items,
                duration_minutes=payload.duration_minutes,
                is_completed=payload.is_completed,
                notes=payload.notes,
            )
            self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_by_user(
        self, *, user_id: int, from_date: date | None, to_date: date | None, skip: int = 0, limit: int = 100
    ) -> list[DailyWorkoutPlan]:
        stmt = select(DailyWorkoutPlan).where(DailyWorkoutPlan.user_id == user_id)
        if from_date is not None:
            stmt = stmt.where(DailyWorkoutPlan.record_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(DailyWorkoutPlan.record_date <= to_date)
        stmt = stmt.order_by(desc(DailyWorkoutPlan.record_date)).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
