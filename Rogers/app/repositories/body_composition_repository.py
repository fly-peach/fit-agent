from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.body_composition import BodyCompositionRecord
from app.schemas.body_composition import BodyCompositionCreate


class BodyCompositionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, member_id: int, obj_in: BodyCompositionCreate) -> BodyCompositionRecord:
        db_obj = BodyCompositionRecord(
            member_id=member_id,
            assessment_id=obj_in.assessment_id,
            measured_at=obj_in.measured_at,
            weight=obj_in.weight,
            bmi=obj_in.bmi,
            body_fat_rate=obj_in.body_fat_rate,
            visceral_fat_level=obj_in.visceral_fat_level,
            fat_mass=obj_in.fat_mass,
            muscle_mass=obj_in.muscle_mass,
            skeletal_muscle_mass=obj_in.skeletal_muscle_mass,
            skeletal_muscle_rate=obj_in.skeletal_muscle_rate,
            water_rate=obj_in.water_rate,
            water_mass=obj_in.water_mass,
            bmr=obj_in.bmr,
            raw_payload=obj_in.raw_payload,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, *, record_id: int, member_id: int) -> BodyCompositionRecord | None:
        stmt = select(BodyCompositionRecord).where(
            BodyCompositionRecord.id == record_id, BodyCompositionRecord.member_id == member_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_multi(
        self,
        *,
        member_id: int,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        assessment_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[BodyCompositionRecord]:
        stmt = select(BodyCompositionRecord).where(BodyCompositionRecord.member_id == member_id)
        if assessment_id is not None:
            stmt = stmt.where(BodyCompositionRecord.assessment_id == assessment_id)
        if from_dt is not None:
            stmt = stmt.where(BodyCompositionRecord.measured_at >= from_dt)
        if to_dt is not None:
            stmt = stmt.where(BodyCompositionRecord.measured_at <= to_dt)
        stmt = stmt.order_by(desc(BodyCompositionRecord.measured_at)).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def latest(self, *, member_id: int) -> BodyCompositionRecord | None:
        stmt = (
            select(BodyCompositionRecord)
            .where(BodyCompositionRecord.member_id == member_id)
            .order_by(desc(BodyCompositionRecord.measured_at))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def latest_two(self, *, member_id: int) -> list[BodyCompositionRecord]:
        stmt = (
            select(BodyCompositionRecord)
            .where(BodyCompositionRecord.member_id == member_id)
            .order_by(desc(BodyCompositionRecord.measured_at))
            .limit(2)
        )
        return list(self.db.execute(stmt).scalars().all())
