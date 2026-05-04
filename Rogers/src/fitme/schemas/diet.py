"""Diet Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class NutrientProgress(BaseModel):
    """营养进度"""
    current: int
    goal: int
    percent: int


class DietStats(BaseModel):
    """今日饮食统计"""
    calories: int
    caloriesGoal: int
    remainingCalories: int
    protein: int
    proteinGoal: int
    carbs: int
    carbsGoal: int
    fat: int
    fatGoal: int
    water: int
    waterGoal: int
    streakDays: int


class DietStatsResponse(BaseModel):
    """今日饮食统计响应"""
    code: int = 200
    data: DietStats


class DietMeal(BaseModel):
    """饮食记录"""
    mealId: int
    mealType: str
    mealName: str
    calories: int
    protein: float
    carbs: float
    fat: float
    time: str
    note: Optional[str] = None


class DietMealsResponse(BaseModel):
    """今日饮食记录响应"""
    code: int = 200
    data: List[DietMeal]


class CreateMealRequest(BaseModel):
    """添加饮食记录请求"""
    mealType: str
    mealName: str
    calories: int
    protein: Optional[float] = 0
    carbs: Optional[float] = 0
    fat: Optional[float] = 0
    water: Optional[int] = 0
    time: str
    note: Optional[str] = None
    mealDate: Optional[str] = None  # YYYY-MM-DD，默认今天


class CreateMealResponse(BaseModel):
    """添加饮食记录响应"""
    code: int = 200
    message: str = "添加成功"
    data: dict


class UpdateMealRequest(BaseModel):
    """更新饮食记录请求"""
    mealName: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    water: Optional[int] = None


class NutritionProgress(BaseModel):
    """营养摄入进度"""
    protein: NutrientProgress
    carbs: NutrientProgress
    fat: NutrientProgress


class NutritionProgressResponse(BaseModel):
    """营养摄入进度响应"""
    code: int = 200
    data: NutritionProgress


class RecommendedFood(BaseModel):
    """推荐食物"""
    recommendId: int
    foodName: str
    calories: int
    protein: Optional[float] = None
    reason: Optional[str] = None
    suitableTime: Optional[str] = None


class RecommendedFoodResponse(BaseModel):
    """推荐食物响应"""
    code: int = 200
    data: List[RecommendedFood]


class DailyDietStats(BaseModel):
    """每日饮食统计"""
    day: str
    date: date
    calories: int
    proteinGoalMet: bool
    waterGoalMet: bool


class WeeklyDietSummary(BaseModel):
    """本周饮食摘要"""
    avgCalories: int
    proteinGoalDays: int
    waterGoalDays: int


class WeeklyDietTrend(BaseModel):
    """本周饮食趋势"""
    dailyStats: List[DailyDietStats]
    summary: WeeklyDietSummary


class WeeklyDietTrendResponse(BaseModel):
    """本周饮食趋势响应"""
    code: int = 200
    data: WeeklyDietTrend


# ---------------------------------------------------------------------------
# 食物数据库
# ---------------------------------------------------------------------------

class DateRangeDietTrendItem(BaseModel):
    """日期范围每日饮食趋势"""
    date: date
    calories: int
    protein: float
    carbs: float
    fat: float
    water: int
    proteinGoalMet: bool
    waterGoalMet: bool
    mealCount: int


class DietTrendGoals(BaseModel):
    """饮食目标值"""
    caloriesGoal: int
    proteinGoal: int
    carbsGoal: int
    fatGoal: int
    waterGoal: int


class DateRangeDietTrend(BaseModel):
    """日期范围饮食趋势"""
    dailyStats: List[DateRangeDietTrendItem]
    goals: DietTrendGoals


class DateRangeDietTrendResponse(BaseModel):
    """日期范围饮食趋势响应"""
    code: int = 200
    data: DateRangeDietTrend


class FoodItem(BaseModel):
    """食物项"""
    foodId: int
    name: str
    category: str
    source: str = "system"
    portionUnit: str | None = None
    portionGrams: int | None = None
    portionCalories: int
    caloriesPer100g: int
    calorieLevel: str | None = None
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    suitableMeals: str = "breakfast,lunch,dinner"


class FoodItemsResponse(BaseModel):
    """食物列表响应"""
    code: int = 200
    data: list[FoodItem]


class CreateCustomFood(BaseModel):
    """添加自定义食物请求"""
    name: str
    category: str
    portionUnit: str | None = None
    portionGrams: int | None = None
    portionCalories: int
    caloriesPer100g: int
    calorieLevel: str | None = None
    protein: float = 0
    carbs: float = 0
    fat: float = 0


class CreateCustomFoodResponse(BaseModel):
    """添加自定义食物响应"""
    code: int = 200
    message: str = "添加成功"
    data: dict