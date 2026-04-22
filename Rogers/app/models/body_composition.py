from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class BodyCompositionRecord(Base):
    __tablename__ = "body_composition_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assessment_id: Mapped[int | None] = mapped_column(ForeignKey("assessments.id"), nullable=True, index=True)

    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    visceral_fat_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    skeletal_muscle_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    skeletal_muscle_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmr: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 新增指标
    muscle_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    bone_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    ideal_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_control: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_control: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_control: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nutrition_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    body_age: Mapped[float | None] = mapped_column(Float, nullable=True)
    subcutaneous_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_free_mass: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_burn_hr_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_burn_hr_high: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

