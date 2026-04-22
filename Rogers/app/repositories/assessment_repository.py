from typing import Any, Dict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate


class AssessmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, assessment_id: int) -> Assessment | None:
        return self.db.query(Assessment).filter(Assessment.id == assessment_id).first()

    def get_multi_by_user(self, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100) -> list[Assessment]:
        query = self.db.query(Assessment).filter(Assessment.member_id == user_id)
        if status:
            query = query.filter(Assessment.status == status)
            
        return query.order_by(Assessment.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, *, obj_in: AssessmentCreate, member_id: int) -> Assessment:
        db_obj = Assessment(
            member_id=member_id,
            goal=obj_in.goal,
            questionnaire_summary=obj_in.questionnaire_summary,
            status="draft"
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, *, db_obj: Assessment, obj_in: Dict[str, Any]) -> Assessment:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def latest_by_user(self, user_id: int) -> Assessment | None:
        stmt = select(Assessment).where(Assessment.member_id == user_id).order_by(desc(Assessment.created_at)).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()
