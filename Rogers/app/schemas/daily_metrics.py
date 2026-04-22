from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DailyMetricsUpsert(BaseModel):
    weight: float | None = None
    body_fat_rate: float | None = None
    bmi: float | None = None
    visceral_fat_level: float | None = None
    bmr: float | None = None


class DailyMetricsResponse(DailyMetricsUpsert):
    id: int
    user_id: int
    record_date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
