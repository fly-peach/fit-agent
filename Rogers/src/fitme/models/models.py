"""FitMe Database Models"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Date, Time, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(10), default=None)
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
    reminder_time = Column(Time, default="07:00:00")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="settings")


class HealthMetric(Base):
    """健康指标记录表"""
    __tablename__ = "health_metrics"
    __table_args__ = (
        Index("idx_user_date", "user_id", "measure_date"),
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
        Index("idx_user_date", "user_id", "scheduled_date"),
        Index("idx_user_status", "user_id", "status"),
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
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="training_plans")
    records = relationship("TrainingRecord", back_populates="plan")


class TrainingRecord(Base):
    """训练完成记录表"""
    __tablename__ = "training_records"
    __table_args__ = (
        Index("idx_user_date", "user_id", "completed_at"),
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
        Index("idx_user_date", "user_id", "meal_date"),
        Index("idx_user_type", "user_id", "meal_type"),
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