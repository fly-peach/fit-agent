"""FitMe Database Models"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Date, Time, Boolean, Text, ForeignKey, Index, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import time

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(512), default=None)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, default=None)

    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    health_metrics = relationship("HealthMetric", back_populates="user")
    training_plans = relationship("TrainingPlan", back_populates="user")
    diet_meals = relationship("DietMeal", back_populates="user")
    streak_stats = relationship("StreakStats", back_populates="user", uselist=False)
    images = relationship("UserImage", back_populates="user")
    pinned_exercises = relationship("UserPinnedExercise", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    """用户设置表"""
    __tablename__ = "user_settings"

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    calorie_goal = Column(Integer, default=2000)
    protein_goal = Column(Integer, default=150)
    carbs_goal = Column(Integer, default=250)
    fat_goal = Column(Integer, default=65)
    water_goal = Column(Integer, default=2000)
    weight_goal = Column(DECIMAL(5, 2), default=None)
    weekly_training_goal = Column(Integer, default=5)
    notification_enabled = Column(Boolean, default=True)
    reminder_time = Column(Time, default=time(7, 0))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="settings")


class HealthMetric(Base):
    """健康指标记录表"""
    __tablename__ = "health_metrics"
    __table_args__ = (
        Index("idx_health_user_date", "user_id", "measure_date"),
    )

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    weight = Column(DECIMAL(5, 2))
    height = Column(DECIMAL(5, 2))
    body_fat = Column(DECIMAL(4, 2))
    bmi = Column(DECIMAL(4, 2))
    bmi_status = Column(String(10), default="normal")
    measure_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="health_metrics")


class TrainingPlan(Base):
    """训练计划表"""
    __tablename__ = "training_plans"
    __table_args__ = (
        Index("idx_training_plan_user_date", "user_id", "scheduled_date"),
        Index("idx_training_plan_user_status", "user_id", "status"),
    )

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    plan_name = Column(String(100), nullable=False)
    plan_type = Column(String(20), nullable=False)  # strength/cardio/flexibility
    target_intensity = Column(String(20), default="medium")  # low/medium/high
    estimated_duration = Column(Integer, default=60)
    scheduled_date = Column(Date, nullable=False)
    day_of_week = Column(Integer)
    status = Column(String(20), default="pending")  # pending/completed/cancelled
    is_recurring = Column(Boolean, default=False)  # 是否为循环模板
    recurring_group_id = Column(Integer, default=None)  # 循环组ID，同一组的计划共享
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="training_plans")
    plan_exercise_items = relationship("PlanExerciseItem", back_populates="plan", cascade="all, delete-orphan")
    records = relationship("TrainingRecord", back_populates="plan")


class TrainingRecord(Base):
    """训练完成记录表"""
    __tablename__ = "training_records"
    __table_args__ = (
        Index("idx_training_record_user_date", "user_id", "completed_at"),
    )

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("training_plans.plan_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    actual_duration = Column(Integer)
    actual_intensity = Column(String(20))
    calories_burned = Column(Integer)
    completed_at = Column(DateTime, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("TrainingPlan", back_populates="records")
    user = relationship("User")


class DietMeal(Base):
    """饮食记录表"""
    __tablename__ = "diet_meals"
    __table_args__ = (
        Index("idx_diet_user_date", "user_id", "meal_date"),
        Index("idx_diet_user_type", "user_id", "meal_type"),
    )

    meal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    meal_type = Column(String(20), nullable=False)  # breakfast/lunch/dinner/snack
    meal_name = Column(String(100), nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(DECIMAL(6, 2), default=0)
    carbs = Column(DECIMAL(6, 2), default=0)
    fat = Column(DECIMAL(6, 2), default=0)
    water = Column(Integer, default=0)
    meal_date = Column(Date, nullable=False)
    meal_time = Column(Time, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="diet_meals")


class StreakStats(Base):
    """连续记录统计表"""
    __tablename__ = "streak_stats"

    streak_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    training_streak = Column(Integer, default=0)
    diet_streak = Column(Integer, default=0)
    last_training_date = Column(Date)
    last_diet_date = Column(Date)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="streak_stats")


class DailyDietSummary(Base):
    """每日饮食统计汇总表"""
    __tablename__ = "daily_diet_summary"
    __table_args__ = (
        Index("uk_user_date", "user_id", "summary_date", unique=True),
    )

    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    summary_date = Column(Date, nullable=False)
    total_calories = Column(Integer, default=0)
    total_protein = Column(DECIMAL(6, 2), default=0)
    total_carbs = Column(DECIMAL(6, 2), default=0)
    total_fat = Column(DECIMAL(6, 2), default=0)
    total_water = Column(Integer, default=0)
    protein_goal_met = Column(Boolean, default=False)
    water_goal_met = Column(Boolean, default=False)
    meal_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RecommendedTraining(Base):
    """推荐训练计划表"""
    __tablename__ = "recommended_trainings"

    recommend_id = Column(Integer, primary_key=True, autoincrement=True)
    plan_name = Column(String(100), nullable=False)
    plan_type = Column(String(20), nullable=False)
    duration = Column(Integer, nullable=False)
    intensity = Column(String(20), nullable=False)
    calories_burn = Column(Integer)
    description = Column(Text)
    target_body_type = Column(String(50))
    difficulty_level = Column(String(20), default="medium")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RecommendedFood(Base):
    """推荐食物表"""
    __tablename__ = "recommended_foods"

    recommend_id = Column(Integer, primary_key=True, autoincrement=True)
    food_name = Column(String(100), nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(DECIMAL(6, 2))
    carbs = Column(DECIMAL(6, 2))
    fat = Column(DECIMAL(6, 2))
    reason = Column(String(200))
    suitable_time = Column(String(50))
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserImage(Base):
    """用户图片存储表"""
    __tablename__ = "user_images"
    __table_args__ = (
        Index("idx_user_image_user_id", "user_id"),
    )

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="images")


class FoodItem(Base):
    """食物数据库（食材 + 菜品）"""
    __tablename__ = "food_items"
    __table_args__ = (
        Index("idx_food_category", "category"),
        Index("idx_food_name", "name"),
    )

    food_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)  # 主食/肉类/蔬菜/水果/豆制品/水产/蛋类/调料/坚果/火锅/汤类/海鲜/鱼虾/牛肉/羊肉/鸡肉/猪肉/蔬菜/蛋类/其他
    source = Column(String(10), nullable=False, default="system")  # system/custom
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)  # 自定义食物归属用户
    portion_unit = Column(String(20))  # 一份维度，如"1 碗"
    portion_grams = Column(Integer)  # 一份 g 数
    portion_calories = Column(Integer, nullable=False)  # 一份热量
    calories_per_100g = Column(Integer, nullable=False)  # 每 100g 热量
    calorie_level = Column(String(4))  # 热量等级：低/中/高/超高
    suitable_meals = Column(String(50), default="breakfast,lunch,dinner")  # 适合餐次：breakfast,lunch,dinner 组合
    protein = Column(DECIMAL(6, 2), default=0)
    carbs = Column(DECIMAL(6, 2), default=0)
    fat = Column(DECIMAL(6, 2), default=0)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


class Exercise(Base):
    """健身动作库"""
    __tablename__ = "exercises"
    __table_args__ = (
        Index("idx_exercise_target_muscle", "target_muscle"),
        Index("idx_exercise_type_equipment", "exercise_type", "equipment"),
        Index("idx_exercise_difficulty", "difficulty"),
        Index("idx_exercise_name", "name_cn"),
    )

    exercise_id = Column(Integer, primary_key=True, autoincrement=True)
    name_cn = Column(String(100), nullable=False)  # 动作名称（中文）
    name_en = Column(String(150))  # 动作名称（英文）
    difficulty = Column(String(10))  # 初级/中级/专家级
    force_type = Column(String(10))  # 推/拉/静力
    mechanics = Column(String(20))  # 复合动作/孤立动作/无
    equipment = Column(String(30))  # 所需器械
    exercise_type = Column(String(20))  # 力量训练/力量举/增强式训练/奥林匹克举重/大力士/有氧运动/拉伸
    target_muscle = Column(String(30), nullable=False)  # 目标肌肉
    helper_muscles = Column(String(200), default="")  # 辅助肌肉，逗号分隔
    instructions = Column(Text, nullable=False)  # 动作说明，JSON 数组字符串
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserPinnedExercise(Base):
    """用户收藏的健身动作"""
    __tablename__ = "user_pinned_exercises"
    __table_args__ = (
        Index("idx_pinned_user", "user_id"),
        Index("idx_pinned_exercise", "exercise_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id"), nullable=False)
    sort_order = Column(Integer, default=0)  # 排序，越小越靠前
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="pinned_exercises")
    exercise = relationship("Exercise")


class PlanExerciseItem(Base):
    """训练计划-动作项（支持库动作和自定义动作）"""
    __tablename__ = "plan_exercise_items"
    __table_args__ = (
        Index("idx_plan_item_plan", "plan_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("training_plans.plan_id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id"), nullable=True)  # 库动作引用，可为空
    custom_name = Column(String(100), default="")  # 自定义动作名称
    sets = Column(Integer, default=3)
    reps = Column(Integer, default=10)
    weight = Column(DECIMAL(5, 2), default=None)
    duration = Column(Integer, default=None)
    notes = Column(Text, default=None)
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("TrainingPlan", back_populates="plan_exercise_items")
    exercise = relationship("Exercise")