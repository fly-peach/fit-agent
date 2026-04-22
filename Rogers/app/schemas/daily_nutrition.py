from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MealNutrition(BaseModel):
    calories_kcal: float = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)
    carb_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)


class DailyNutritionUpsert(BaseModel):
    # Daily totals (optional, will be computed from meals if not provided)
    calories_kcal: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    carb_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=255)

    # Meal breakdowns
    breakfast: MealNutrition | None = Field(default=None)
    lunch: MealNutrition | None = Field(default=None)
    dinner: MealNutrition | None = Field(default=None)


class DailyNutritionResponse(BaseModel):
    id: int
    user_id: int
    record_date: date
    calories_kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    notes: str | None
    breakfast: MealNutrition
    lunch: MealNutrition
    dinner: MealNutrition
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def _meal_from(obj, prefix: str) -> MealNutrition:
        return MealNutrition(
            calories_kcal=getattr(obj, f"{prefix}_calories_kcal", 0),
            protein_g=getattr(obj, f"{prefix}_protein_g", 0),
            carb_g=getattr(obj, f"{prefix}_carb_g", 0),
            fat_g=getattr(obj, f"{prefix}_fat_g", 0),
        )

    @classmethod
    def model_validate(cls, obj, **kwargs):
        base = super().model_validate(obj, **kwargs)
        base.breakfast = cls._meal_from(obj, "breakfast")
        base.lunch = cls._meal_from(obj, "lunch")
        base.dinner = cls._meal_from(obj, "dinner")
        return base
