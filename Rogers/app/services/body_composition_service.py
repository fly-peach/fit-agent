from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.body_composition_repository import BodyCompositionRepository
from app.schemas.body_composition import (
    BodyCompositionCompareResponse,
    BodyCompositionCreate,
    BodyCompositionResponse,
    BodyCompositionTrendPoint,
    INDICATOR_GROUPS,
)


class BodyCompositionService:
    def __init__(self, db: Session) -> None:
        self.repo = BodyCompositionRepository(db)

    @staticmethod
    def _metric_fields() -> list[str]:
        return [
            "weight", "bmi", "body_fat_rate", "visceral_fat_level", "fat_mass",
            "muscle_mass", "skeletal_muscle_mass", "skeletal_muscle_rate",
            "water_rate", "water_mass", "bmr",
            "muscle_rate", "bone_mass", "protein_mass", "protein_rate",
            "ideal_weight", "weight_control", "fat_control", "muscle_control",
            "body_age", "subcutaneous_fat", "fat_free_mass",
            "fat_burn_hr_low", "fat_burn_hr_high",
        ]

    def create(self, *, current_user: User, payload: BodyCompositionCreate):
        return self.repo.create(member_id=current_user.id, obj_in=payload)

    def get(self, *, current_user: User, record_id: int):
        record = self.repo.get(record_id=record_id, member_id=current_user.id)
        if not record:
            raise HTTPException(status_code=404, detail="体成分记录不存在")
        return record

    def get_multi(
        self,
        *,
        current_user: User,
        from_dt: datetime | None,
        to_dt: datetime | None,
        assessment_id: int | None,
        skip: int,
        limit: int,
    ):
        return self.repo.get_multi(
            member_id=current_user.id,
            from_dt=from_dt,
            to_dt=to_dt,
            assessment_id=assessment_id,
            skip=skip,
            limit=limit,
        )

    def trend(
        self,
        *,
        current_user: User,
        metric: str,
        from_dt: datetime | None,
        to_dt: datetime | None,
        limit: int,
    ) -> list[BodyCompositionTrendPoint]:
        if metric not in self._metric_fields():
            raise HTTPException(status_code=400, detail="metric 不支持")

        records = self.repo.get_multi(member_id=current_user.id, from_dt=from_dt, to_dt=to_dt, skip=0, limit=limit)
        records = list(reversed(records))

        points: list[BodyCompositionTrendPoint] = []
        for r in records:
            value = getattr(r, metric, None)
            if value is None:
                continue
            points.append(BodyCompositionTrendPoint(measured_at=r.measured_at, value=float(value)))
        return points

    def compare(self, *, current_user: User, a_id: int, b_id: int) -> BodyCompositionCompareResponse:
        a = self.repo.get(record_id=a_id, member_id=current_user.id)
        b = self.repo.get(record_id=b_id, member_id=current_user.id)
        if not a or not b:
            raise HTTPException(status_code=404, detail="体成分记录不存在")

        diff: dict[str, float] = {}
        diff_ratio: dict[str, float] = {}
        tags: list[str] = []
        for f in self._metric_fields():
            va = getattr(a, f, None)
            vb = getattr(b, f, None)
            if va is None or vb is None:
                continue
            d = float(vb) - float(va)
            diff[f] = d
            if float(va) != 0:
                diff_ratio[f] = d / float(va)
            if d > 0:
                tags.append(f"{f}_up")
            elif d < 0:
                tags.append(f"{f}_down")

        return BodyCompositionCompareResponse(
            a=BodyCompositionResponse.model_validate(a),
            b=BodyCompositionResponse.model_validate(b),
            diff=diff,
            diff_ratio=diff_ratio,
            tags=tags,
        )
