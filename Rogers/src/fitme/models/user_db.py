"""FitMe User Database Models - User Specific Data

This database contains:
- User accounts and settings
- User health metrics
- User training plans
- User diet records
- User custom exercises and foods
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Date, Time, Boolean, Text, ForeignKey, Index, LargeBinary, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import time

Base = declarative_base()


class User(Base):
    """用户表 - User DB"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    # id 作为 user_id 的别名列，用于兼容 AsyncSQLAlchemyMemory
    id = Column(Integer, nullable=True)
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
    """用户设置表 - User DB"""
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
    auto_approve_db_write = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="settings")


class HealthMetric(Base):
    """健康指标记录表 - User DB"""
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
    """训练计划表 - User DB"""
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
    """训练完成记录表 - User DB"""
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
    """饮食记录表 - User DB"""
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
    """连续记录统计表 - User DB"""
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
    """每日饮食统计汇总表 - User DB"""
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


class UserImage(Base):
    """用户图片存储表 - User DB"""
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


class UserPinnedExercise(Base):
    """用户收藏的健身动作 - User DB

    Note: exercise_id references base_db.exercises.exercise_id
    """
    __tablename__ = "user_pinned_exercises"
    __table_args__ = (
        Index("idx_pinned_user", "user_id"),
        Index("idx_pinned_exercise", "exercise_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    exercise_id = Column(Integer, nullable=False)  # References base_db.exercises.exercise_id
    sort_order = Column(Integer, default=0)  # 排序，越小越靠前
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="pinned_exercises")


class PlanExerciseItem(Base):
    """训练计划-动作项 - User DB

    Note: exercise_id references base_db.exercises.exercise_id (optional)
    """
    __tablename__ = "plan_exercise_items"
    __table_args__ = (
        Index("idx_plan_item_plan", "plan_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("training_plans.plan_id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, nullable=True)  # References base_db.exercises.exercise_id, can be null
    custom_name = Column(String(100), default="")  # 自定义动作名称
    sets = Column(Integer, default=3)
    reps = Column(Integer, default=10)
    weight = Column(DECIMAL(5, 2), default=None)
    duration = Column(Integer, default=None)
    notes = Column(Text, default=None)
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("TrainingPlan", back_populates="plan_exercise_items")


class CustomFoodItem(Base):
    """用户自定义食物 - User DB

    This replaces the source='custom' entries from the original food_items table
    """
    __tablename__ = "custom_food_items"
    __table_args__ = (
        Index("idx_custom_food_user", "user_id"),
        Index("idx_custom_food_name", "name"),
    )

    food_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)
    portion_unit = Column(String(20))
    portion_grams = Column(Integer)
    portion_calories = Column(Integer, nullable=False)
    calories_per_100g = Column(Integer, nullable=False)
    calorie_level = Column(String(4))
    suitable_meals = Column(String(50), default="breakfast,lunch,dinner")
    protein = Column(DECIMAL(6, 2), default=0)
    carbs = Column(DECIMAL(6, 2), default=0)
    fat = Column(DECIMAL(6, 2), default=0)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


class CustomExerciseItem(Base):
    """用户自定义健身动作 - User DB"""
    __tablename__ = "custom_exercise_items"
    __table_args__ = (
        Index("idx_custom_exercise_user", "user_id"),
        Index("idx_custom_exercise_name", "name_cn"),
    )

    exercise_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name_cn = Column(String(100), nullable=False)
    name_en = Column(String(150))
    difficulty = Column(String(10))
    force_type = Column(String(10))
    mechanics = Column(String(20))
    equipment = Column(String(30))
    exercise_type = Column(String(20))
    target_muscle = Column(String(30), nullable=False)
    helper_muscles = Column(String(200), default="")
    instructions = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


# ============================================================================
# Event listeners to sync id with user_id for AsyncSQLAlchemyMemory compatibility
# ============================================================================

@event.listens_for(User, "before_insert")
def sync_id_before_insert(mapper, connection, target):
    """在插入 User 前，将 id 设置为与 user_id 相同（虽然 user_id 是自增，需在 after_insert 处理）"""
    pass


@event.listens_for(User, "after_insert")
def sync_id_after_insert(mapper, connection, target):
    """在 User 插入后，同步 id = user_id"""
    if target.user_id and not target.id:
        connection.execute(
            User.__table__.update()
            .where(User.__table__.c.user_id == target.user_id)
            .values(id=target.user_id)
        )


class TrainingResultSnapshot(Base):
    """训练成果快照表 - User DB

    存储 Agent 生成的训练成果 HTML 卡片
    """
    __tablename__ = "training_result_snapshots"
    __table_args__ = (
        Index("idx_training_result_user", "user_id"),
        Index("idx_training_result_period", "user_id", "period_start", "period_end"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)  # 关联的 Agent 会话
    card_html = Column(Text, nullable=False)  # Agent 生成的完整 HTML 卡片
    stats_json = Column(Text, nullable=True)  # 统计数据 JSON（列表预览用）
    title = Column(String(200), nullable=False)  # 快照标题（如"2024年5月第三周训练成果"）
    period_type = Column(String(20), nullable=True)  # 周期类型："week" | "month" | "custom"
    period_start = Column(Date, nullable=True)  # 统计周期开始
    period_end = Column(Date, nullable=True)  # 统计周期结束
    thumbnail = Column(Text, nullable=True)  # 缩略图/封面图（可选，Base64或URL）
    is_active = Column(Boolean, default=True, nullable=False)  # 软删除
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")


