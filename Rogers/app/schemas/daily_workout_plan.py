from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkoutItem(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    sets: int = Field(ge=0, default=0)
    reps: int = Field(ge=0, default=0)
    duration_minutes: int = Field(ge=0, default=0)


class DailyWorkoutPlanUpsert(BaseModel):
    plan_title: str = Field(default="今日训练", min_length=1, max_length=128)
    items: list[WorkoutItem] = Field(default_factory=list)
    duration_minutes: int = Field(default=0, ge=0)
    is_completed: bool = False
    notes: str | None = Field(default=None, max_length=255)


class DailyWorkoutPlanResponse(BaseModel):
    id: int
    user_id: int
    record_date: date
    plan_title: str
    items: list[WorkoutItem]
    duration_minutes: int
    is_completed: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
