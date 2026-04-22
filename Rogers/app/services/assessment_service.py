from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.assessment import Assessment
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.assessment import AssessmentCreate, AssessmentComplete


class AssessmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AssessmentRepository(db)

    def create_assessment(self, obj_in: AssessmentCreate, current_user: User) -> Assessment:
        return self.repo.create(obj_in=obj_in, member_id=current_user.id)

    def get_assessment(self, assessment_id: int, current_user: User) -> Assessment:
        assessment = self.repo.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="评估记录不存在")

        if assessment.member_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该评估记录")

        return assessment

    def list_assessments(
        self, current_user: User, skip: int = 0, limit: int = 100, status: str | None = None
    ) -> list[Assessment]:
        return self.repo.get_multi_by_user(
            user_id=current_user.id,
            status=status,
            skip=skip,
            limit=limit,
        )

    def complete_assessment(
        self, assessment_id: int, data: AssessmentComplete, current_user: User
    ) -> Assessment:
        assessment = self.get_assessment(assessment_id, current_user)

        if assessment.status == "completed":
            raise HTTPException(status_code=400, detail="评估已完成，无法再次修改")

        update_data = {
            "status": "completed",
            "risk_level": data.risk_level,
            "report_summary": data.report_summary,
            "completed_at": datetime.now(timezone.utc),
        }
        return self.repo.update(db_obj=assessment, obj_in=update_data)

    def get_assessment_report(self, assessment_id: int, current_user: User) -> Assessment:
        assessment = self.get_assessment(assessment_id, current_user)
        if assessment.status != "completed":
            raise HTTPException(status_code=400, detail="评估尚未完成，无法查看报告")
        return assessment
