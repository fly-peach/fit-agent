from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssessmentBase(BaseModel):
    goal: str | None = Field(default=None, description="评估目标")
    questionnaire_summary: dict[str, Any] | None = Field(default=None, description="问卷摘要")


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    status: str | None = None
    risk_level: str | None = None
    questionnaire_summary: dict[str, Any] | None = None
    report_summary: dict[str, Any] | None = None
    goal: str | None = None


class AssessmentComplete(BaseModel):
    risk_level: str = Field(..., description="风险等级(low, medium, high)")
    report_summary: dict[str, Any] = Field(..., description="评估报告内容")


class AssessmentResponse(AssessmentBase):
    id: int
    member_id: int
    status: str
    risk_level: str | None = None
    report_summary: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AssessmentReportResponse(BaseModel):
    id: int
    status: str
    risk_level: str | None
    report_summary: dict[str, Any] | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
