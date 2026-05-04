"""Training Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from .exercise import PlanExerciseItemInput, PlanExerciseItemOutput


class WeeklyStats(BaseModel):
    """本周训练统计"""
    weeklyCount: int
    weeklyHours: float
    weeklyCalories: int
    streakDays: int
    completedCount: int
    remainingCount: int


class WeeklyStatsResponse(BaseModel):
    """本周训练统计响应"""
    code: int = 200
    data: WeeklyStats


class TrainingSchedule(BaseModel):
    """训练安排"""
    planId: Optional[int] = None
    dayOfWeek: int
    date: date
    planName: str
    planType: str
    duration: int
    intensity: str
    status: str
    isRecurring: bool = False
    completedAt: Optional[datetime] = None


class WeeklyScheduleResponse(BaseModel):
    """本周训练安排响应"""
    code: int = 200
    data: List[TrainingSchedule]


class MonthlyScheduleItem(BaseModel):
    """月度训练安排"""
    planId: Optional[int] = None
    date: str
    planName: str
    planType: str
    duration: int
    intensity: str
    status: str
    isRecurring: bool = False
    isLastInGroup: bool = False


class MonthlyScheduleResponse(BaseModel):
    """月度训练安排响应"""
    code: int = 200
    data: List[MonthlyScheduleItem]


class DayProgress(BaseModel):
    """每日进度"""
    day: str
    completed: bool


class WeeklyProgress(BaseModel):
    """本周进度"""
    targetCount: int
    completedCount: int
    progressPercent: int
    daysProgress: List[DayProgress]


class WeeklyProgressResponse(BaseModel):
    """本周进度响应"""
    code: int = 200
    data: WeeklyProgress


class RecommendedTraining(BaseModel):
    """推荐训练"""
    recommendId: int
    planName: str
    planType: str
    duration: int
    intensity: str
    caloriesBurn: Optional[int] = None
    suitability: Optional[str] = None


class RecommendedTrainingResponse(BaseModel):
    """推荐训练响应"""
    code: int = 200
    data: List[RecommendedTraining]


class CreateTrainingPlanRequest(BaseModel):
    """创建训练计划请求"""
    planName: str
    planType: str
    targetIntensity: Optional[str] = "medium"
    estimatedDuration: Optional[int] = 60
    scheduledDate: date
    note: Optional[str] = None
    isRecurring: bool = False
    recurringGroupId: Optional[int] = None
    exercises: Optional[List[PlanExerciseItemInput]] = None


class CreateTrainingPlanResponse(BaseModel):
    """创建训练计划响应"""
    code: int = 200
    message: str = "创建成功"
    data: dict


class UpdateTrainingPlanRequest(BaseModel):
    """更新训练计划请求"""
    planName: Optional[str] = None
    scheduledDate: Optional[date] = None
    targetIntensity: Optional[str] = None
    estimatedDuration: Optional[int] = None
    note: Optional[str] = None


class CompleteTrainingRequest(BaseModel):
    """完成训练请求"""
    actualDuration: int
    actualIntensity: Optional[str] = None
    caloriesBurned: Optional[int] = None
    note: Optional[str] = None
    completedDate: Optional[str] = None  # YYYY-MM-DD，默认今天


# ---------------------------------------------------------------------------
# 日期范围趋势
# ---------------------------------------------------------------------------


class DailyTrainingTrendItem(BaseModel):
    """日期范围每日训练趋势"""
    date: date
    duration: int
    caloriesBurned: int
    planCount: int


class DateRangeTrainingTrend(BaseModel):
    """日期范围训练趋势"""
    dailyStats: List[DailyTrainingTrendItem]


class DateRangeTrainingTrendResponse(BaseModel):
    """日期范围训练趋势响应"""
    code: int = 200
    data: DateRangeTrainingTrend