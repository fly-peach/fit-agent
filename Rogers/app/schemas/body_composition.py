from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BodyType(str, Enum):
    HIDDEN_OBESE = "隐藏型肥胖"
    STANDARD = "标准"
    MUSCLE = "肌肉型"
    OBESE = "肥胖"
    UNDERWEIGHT = "偏瘦"
    ATHLETIC = "运动型偏胖"


class NutritionStatus(str, Enum):
    DEFICIENT = "营养不足"
    BALANCED = "营养均衡"
    EXCESS = "营养过剩"


class IndicatorLevel(str, Enum):
    LOW = "不足"
    NORMAL = "标准"
    HIGH = "偏高"
    EXCELLENT = "优"
    WARNING = "警戒型"
    REDUCE = "减重"
    INCREASE = "增重"


# 指标分组定义（供前端动态渲染）
INDICATOR_GROUPS = {
    "body_composition": {
        "label": "身体成分",
        "icon": "BodyOutlined",
        "indicators": ["weight", "bmi", "body_fat_rate", "visceral_fat_level", "fat_mass"],
    },
    "muscle_bone": {
        "label": "肌肉骨骼",
        "icon": "FireOutlined",
        "indicators": ["muscle_mass", "skeletal_muscle_mass", "skeletal_muscle_rate", "muscle_rate", "bone_mass"],
    },
    "water_metabolism": {
        "label": "水分代谢",
        "icon": "DropletOutlined",
        "indicators": ["water_rate", "water_mass", "protein_mass", "protein_rate"],
    },
    "metabolism": {
        "label": "代谢能力",
        "icon": "ThunderboltOutlined",
        "indicators": ["bmr", "fat_free_mass", "fat_burn_hr_low", "fat_burn_hr_high"],
    },
    "control_goals": {
        "label": "控制目标",
        "icon": "TargetOutlined",
        "indicators": ["ideal_weight", "weight_control", "fat_control", "muscle_control"],
    },
    "health_assessment": {
        "label": "健康评估",
        "icon": "HeartOutlined",
        "indicators": ["body_type", "nutrition_status", "body_age", "subcutaneous_fat"],
    },
}


class BodyCompositionBase(BaseModel):
    measured_at: datetime = Field(..., description="体测时间")

    weight: float | None = None
    bmi: float | None = None
    body_fat_rate: float | None = None
    visceral_fat_level: float | None = None
    fat_mass: float | None = None
    muscle_mass: float | None = None
    skeletal_muscle_mass: float | None = None
    skeletal_muscle_rate: float | None = None
    water_rate: float | None = None
    water_mass: float | None = None
    bmr: float | None = None

    # 新增指标
    muscle_rate: float | None = None
    bone_mass: float | None = None
    protein_mass: float | None = None
    protein_rate: float | None = None
    ideal_weight: float | None = None
    weight_control: float | None = None
    fat_control: float | None = None
    muscle_control: float | None = None
    body_type: str | None = None
    nutrition_status: str | None = None
    body_age: float | None = None
    subcutaneous_fat: float | None = None
    fat_free_mass: float | None = None
    fat_burn_hr_low: float | None = None
    fat_burn_hr_high: float | None = None

    raw_payload: dict[str, Any] | None = None


class BodyCompositionCreate(BodyCompositionBase):
    assessment_id: int | None = Field(default=None, description="关联评估ID（可选）")


class BodyCompositionResponse(BodyCompositionBase):
    id: int
    member_id: int
    assessment_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BodyCompositionTrendPoint(BaseModel):
    measured_at: datetime
    value: float


class BodyCompositionCompareResponse(BaseModel):
    a: BodyCompositionResponse
    b: BodyCompositionResponse
    diff: dict[str, float]
    diff_ratio: dict[str, float]
    tags: list[str]


# 评估响应
class BodyCompositionEvaluateResponse(BaseModel):
    body_type: str | None
    nutrition_status: str | None
    body_age: float | None
    health_score: int
    subcutaneous_fat: float | None
    ideal_weight: float | None
    weight_control: float | None
    fat_control: float | None
    muscle_control: float | None
    fat_free_mass: float | None
    protein_rate: float | None
    fat_burn_hr_low: float | None
    fat_burn_hr_high: float | None
    indicator_levels: dict[str, str] = Field(default_factory=dict)


# 指标配置响应
class IndicatorConfigResponse(BaseModel):
    groups: dict[str, dict]
    level_colors: dict[str, str]
