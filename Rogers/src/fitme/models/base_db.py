"""FitMe Base Database Models - Shared Base Data

This database contains:
- Exercise library (system provided
- Food library (system provided
- Recommended trainings
- Recommended foods
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Date, Time, Boolean, Text, ForeignKey, Index, LargeBinary
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import time

Base = declarative_base()


class Exercise(Base):
    """健身动作库 - Base DB"""
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


class FoodItem(Base):
    """食物数据库（系统预置） - Base DB"""
    __tablename__ = "food_items"
    __table_args__ = (
        Index("idx_food_category", "category"),
        Index("idx_food_name", "name"),
    )

    food_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)  # 主食/肉类/蔬菜/水果/豆制品/水产/蛋类/调料/坚果/火锅/汤类/海鲜/鱼虾/牛肉/羊肉/鸡肉/猪肉/蔬菜/蛋类/其他
    source = Column(String(10), nullable=False, default="system")  # 始终为 'system'
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


class RecommendedTraining(Base):
    """推荐训练计划表 - Base DB"""
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
    """推荐食物表 - Base DB"""
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
