from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DailyNutrition(Base):
    __tablename__ = "daily_nutritions"
    __table_args__ = (UniqueConstraint("user_id", "record_date", name="uq_daily_nutrition_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Daily totals
    calories_kcal: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    carb_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Breakfast
    breakfast_calories_kcal: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    breakfast_protein_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    breakfast_carb_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    breakfast_fat_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Lunch
    lunch_calories_kcal: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    lunch_protein_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    lunch_carb_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    lunch_fat_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Dinner
    dinner_calories_kcal: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    dinner_protein_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    dinner_carb_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    dinner_fat_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def recalc_totals(self) -> None:
        """Recompute daily totals from meal breakdowns."""
        self.calories_kcal = self.breakfast_calories_kcal + self.lunch_calories_kcal + self.dinner_calories_kcal
        self.protein_g = self.breakfast_protein_g + self.lunch_protein_g + self.dinner_protein_g
        self.carb_g = self.breakfast_carb_g + self.lunch_carb_g + self.dinner_carb_g
        self.fat_g = self.breakfast_fat_g + self.lunch_fat_g + self.dinner_fat_g


@event.listens_for(DailyNutrition, "before_update")
@event.listens_for(DailyNutrition, "before_insert")
def _recalc_nutrition_totals(_mapper, _connection, target: DailyNutrition):
    target.recalc_totals()
