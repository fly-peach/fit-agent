from datetime import date

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.daily_nutrition import DailyNutrition
from app.schemas.daily_nutrition import DailyNutritionUpsert


def _apply_meal(obj: DailyNutrition, payload: DailyNutritionUpsert) -> None:
    """Apply meal-level fields from payload, preserving existing values if not provided."""
    for meal in ("breakfast", "lunch", "dinner"):
        meal_data = getattr(payload, meal, None)
        if meal_data is not None:
            setattr(obj, f"{meal}_calories_kcal", meal_data.calories_kcal)
            setattr(obj, f"{meal}_protein_g", meal_data.protein_g)
            setattr(obj, f"{meal}_carb_g", meal_data.carb_g)
            setattr(obj, f"{meal}_fat_g", meal_data.fat_g)


class DailyNutritionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_date(self, *, user_id: int, record_date: date) -> DailyNutrition | None:
        stmt = select(DailyNutrition).where(
            and_(DailyNutrition.user_id == user_id, DailyNutrition.record_date == record_date)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(self, *, user_id: int, record_date: date, payload: DailyNutritionUpsert) -> DailyNutrition:
        obj = self.get_by_user_and_date(user_id=user_id, record_date=record_date)

        _apply_meal_updates = obj is not None

        if obj:
            if payload.calories_kcal is not None:
                obj.calories_kcal = payload.calories_kcal
            if payload.protein_g is not None:
                obj.protein_g = payload.protein_g
            if payload.carb_g is not None:
                obj.carb_g = payload.carb_g
            if payload.fat_g is not None:
                obj.fat_g = payload.fat_g
            if payload.notes is not None:
                obj.notes = payload.notes
        else:
            obj = DailyNutrition(
                user_id=user_id,
                record_date=record_date,
                calories_kcal=payload.calories_kcal or 0,
                protein_g=payload.protein_g or 0,
                carb_g=payload.carb_g or 0,
                fat_g=payload.fat_g or 0,
                notes=payload.notes,
            )
            self.db.add(obj)

        # Apply meal data
        _apply_meal(obj, payload)

        # Recompute totals from meal data after applying
        obj.recalc_totals()

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_by_user(
        self, *, user_id: int, from_date: date | None, to_date: date | None, skip: int = 0, limit: int = 100
    ) -> list[DailyNutrition]:
        stmt = select(DailyNutrition).where(DailyNutrition.user_id == user_id)
        if from_date is not None:
            stmt = stmt.where(DailyNutrition.record_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(DailyNutrition.record_date <= to_date)
        stmt = stmt.order_by(desc(DailyNutrition.record_date)).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
