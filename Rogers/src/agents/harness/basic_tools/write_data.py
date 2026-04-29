"""Agent 数据写入工具

用户登录后由 AgentContext 设置 user_id 和 db session，
工具自动从 contextvars 获取。
"""

from datetime import date, datetime, time as dt_time

from .read_data import get_db, require_user

from fitme.models import (
    HealthMetric,
    TrainingPlan,
    TrainingRecord,
    DietMeal,
    User,
    UserSettings,
)


def _resolve_user() -> int | None:
    """解析当前用户，失败返回 None。"""
    return require_user()


# =========================================================================
# 工具函数
# =========================================================================

def update_profile(**kwargs) -> str:
    """更新用户基本信息。

    可传入 name, avatar 等字段。
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return "⚠️ 用户不存在"
        changes = []
        if "name" in kwargs and kwargs["name"]:
            user.name = kwargs["name"]
            changes.append(f"姓名 → {kwargs['name']}")
        if "avatar" in kwargs and kwargs["avatar"]:
            user.avatar = kwargs["avatar"]
            changes.append(f"头像 → {kwargs['avatar']}")
        if not changes:
            return "⚠️ 没有需要更新的字段"
        db.commit()
        return f"✅ 已更新用户信息：{'；'.join(changes)}"
    finally:
        if get_db.__module__ is None:  # 判断是否为临时 session
            pass
        # 简单判断：非 context 注入的 session 需要 close
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def add_health_metric(weight: float | None = None, height: float | None = None,
                      body_fat: float | None = None, measure_date: str | None = None) -> str:
    """添加一条新的健康指标记录。

    Args:
        weight: 体重 (kg)
        height: 身高 (cm)
        body_fat: 体脂率 (%)
        measure_date: 测量日期 (YYYY-MM-DD)，默认今天
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        if weight is None and height is None and body_fat is None:
            return "⚠️ 请至少提供一项指标（体重、身高、体脂）"
        from decimal import Decimal
        measure_dt = date.fromisoformat(measure_date) if measure_date else date.today()

        bmi = None
        bmi_status = None
        if weight and height:
            bmi = round(float(weight) / ((float(height) / 100) ** 2), 2)
            if bmi < 18.5:
                bmi_status = "under"
            elif bmi > 25:
                bmi_status = "over"
            else:
                bmi_status = "normal"

        metric = HealthMetric(
            user_id=user_id,
            weight=Decimal(str(weight)) if weight else None,
            height=Decimal(str(height)) if height else None,
            body_fat=Decimal(str(body_fat)) if body_fat else None,
            bmi=Decimal(str(bmi)) if bmi else None,
            bmi_status=bmi_status,
            measure_date=measure_dt,
        )
        db.add(metric)
        db.commit()

        lines = [f"✅ 已记录健康指标（{measure_dt}）："]
        if weight:
            lines.append(f"  体重：{weight} kg")
        if height:
            lines.append(f"  身高：{height} cm")
        if body_fat:
            lines.append(f"  体脂率：{body_fat}%")
        if bmi:
            lines.append(f"  BMI：{bmi}（{bmi_status}）")
        return "\n".join(lines)
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def add_training_plan(plan_name: str, plan_type: str,
                      scheduled_date: str | None = None,
                      estimated_duration: int = 60,
                      target_intensity: str = "medium",
                      note: str | None = None) -> str:
    """创建一条训练计划。

    Args:
        plan_name: 计划名称
        plan_type: 类型 (strength / cardio / flexibility)
        scheduled_date: 计划日期 (YYYY-MM-DD)，默认明天
        estimated_duration: 预计时长（分钟）
        target_intensity: 目标强度 (low / medium / high)
        note: 备注
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        if not plan_name:
            return "⚠️ 请提供训练计划名称"
        if plan_type not in ("strength", "cardio", "flexibility"):
            return "⚠️ 计划类型需为 strength / cardio / flexibility 之一"
        sched_dt = date.fromisoformat(scheduled_date) if scheduled_date else date.today()

        plan = TrainingPlan(
            user_id=user_id,
            plan_name=plan_name,
            plan_type=plan_type,
            target_intensity=target_intensity,
            estimated_duration=estimated_duration,
            scheduled_date=sched_dt,
            day_of_week=(sched_dt.weekday() + 1) % 7 + 1,
            note=note,
            status="pending",
        )
        db.add(plan)
        db.commit()

        return (
            f"✅ 已创建训练计划：{plan_name}\n"
            f"  类型：{plan_type} | 时长：{estimated_duration}分钟 | "
            f"强度：{target_intensity}\n"
            f"  日期：{sched_dt}"
        )
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def complete_training(plan_id: int, actual_duration: int | None = None,
                      actual_intensity: str | None = None,
                      calories_burned: int | None = None,
                      note: str | None = None) -> str:
    """完成一个训练计划，标记为已完成并记录实际数据。

    Args:
        plan_id: 训练计划 ID
        actual_duration: 实际时长（分钟）
        actual_intensity: 实际强度 (low / medium / high)
        calories_burned: 消耗卡路里
        note: 备注
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not plan:
            return f"⚠️ 训练计划 #{plan_id} 不存在"
        plan.status = "completed"
        db.add(TrainingRecord(
            plan_id=plan_id,
            user_id=user_id,
            actual_duration=actual_duration,
            actual_intensity=actual_intensity,
            calories_burned=calories_burned,
            completed_at=datetime.now(),
            note=note,
        ))
        db.commit()
        lines = [f"✅ 已完成训练：{plan.plan_name}"]
        if actual_duration:
            lines.append(f"  实际时长：{actual_duration}分钟")
        if actual_intensity:
            lines.append(f"  实际强度：{actual_intensity}")
        if calories_burned:
            lines.append(f"  消耗：{calories_burned} kcal")
        return "\n".join(lines)
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def delete_training_plan(plan_id: int) -> str:
    """删除一个训练计划。"""
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not plan:
            return f"⚠️ 训练计划 #{plan_id} 不存在"
        plan_name = plan.plan_name
        db.delete(plan)
        db.commit()
        return f"✅ 已删除训练计划：{plan_name}"
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def add_meal(meal_type: str, meal_name: str, calories: int,
             protein: float = 0, carbs: float = 0, fat: float = 0,
             water: int = 0, meal_time_str: str | None = None,
             note: str | None = None) -> str:
    """添加饮食记录。

    Args:
        meal_type: 类型 (breakfast / lunch / dinner / snack)
        meal_name: 食物名称
        calories: 热量 (kcal)
        protein: 蛋白质 (g)
        carbs: 碳水化合物 (g)
        fat: 脂肪 (g)
        water: 饮水量 (ml)
        meal_time_str: 进食时间 (HH:MM)，默认当前时间
        note: 备注
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        valid_types = ("breakfast", "lunch", "dinner", "snack")
        if meal_type not in valid_types:
            return f"⚠️ 饮食类型需为 {' / '.join(valid_types)} 之一"
        if not meal_name:
            return "⚠️ 请提供食物名称"
        if calories <= 0:
            return "⚠️ 热量需大于 0"

        now = datetime.now()
        if meal_time_str:
            mt = dt_time.fromisoformat(meal_time_str)
        else:
            mt = now.time()

        meal = DietMeal(
            user_id=user_id,
            meal_type=meal_type,
            meal_name=meal_name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            water=water,
            meal_date=date.today(),
            meal_time=mt,
            note=note,
        )
        db.add(meal)
        db.commit()

        return (
            f"✅ 已记录饮食：{meal_name}（{meal_type}）\n"
            f"  热量：{calories} kcal | 蛋白 {protein}g | "
            f"碳水 {carbs}g | 脂肪 {fat}g | 水 {water}ml"
        )
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def update_meal(meal_id: int, **kwargs) -> str:
    """更新一条饮食记录。

    可传入 meal_name, calories, protein, carbs, fat, water 等字段。
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        meal = db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if not meal:
            return f"⚠️ 饮食记录 #{meal_id} 不存在"
        changes = []
        if "meal_name" in kwargs and kwargs["meal_name"]:
            meal.meal_name = kwargs["meal_name"]
            changes.append(f"名称 → {kwargs['meal_name']}")
        if "calories" in kwargs and kwargs["calories"]:
            meal.calories = kwargs["calories"]
            changes.append(f"热量 → {kwargs['calories']} kcal")
        if "protein" in kwargs:
            meal.protein = kwargs["protein"]
            changes.append(f"蛋白 → {kwargs['protein']}g")
        if "carbs" in kwargs:
            meal.carbs = kwargs["carbs"]
            changes.append(f"碳水 → {kwargs['carbs']}g")
        if "fat" in kwargs:
            meal.fat = kwargs["fat"]
            changes.append(f"脂肪 → {kwargs['fat']}g")
        if "water" in kwargs:
            meal.water = kwargs["water"]
            changes.append(f"水 → {kwargs['water']}ml")
        if not changes:
            return "⚠️ 没有需要更新的字段"
        db.commit()
        return f"✅ 已更新饮食记录 #{meal_id}：{'；'.join(changes)}"
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def delete_meal(meal_id: int) -> str:
    """删除一条饮食记录。"""
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        meal = db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if not meal:
            return f"⚠️ 饮食记录 #{meal_id} 不存在"
        meal_name = meal.meal_name
        db.delete(meal)
        db.commit()
        return f"✅ 已删除饮食记录：{meal_name}"
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()


def update_settings(**kwargs) -> str:
    """更新用户设置（目标值等）。

    可传入 calorie_goal, protein_goal, carbs_goal, fat_goal,
    water_goal, weight_goal, weekly_training_goal 等。
    """
    user_id = _resolve_user()
    if user_id is None:
        return "⚠️ 请先登录"
    db = get_db()
    try:
        s = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not s:
            return "⚠️ 暂无用户设置，请先初始化设置"
        field_map = {
            "calorie_goal": ("calorie_goal", int),
            "protein_goal": ("protein_goal", int),
            "carbs_goal": ("carbs_goal", int),
            "fat_goal": ("fat_goal", int),
            "water_goal": ("water_goal", int),
            "weight_goal": ("weight_goal", float),
            "weekly_training_goal": ("weekly_training_goal", int),
        }
        changes = []
        for key, (field, _) in field_map.items():
            if key in kwargs and kwargs[key] is not None:
                old_val = getattr(s, field)
                setattr(s, field, kwargs[key])
                changes.append(f"{key} {old_val} → {kwargs[key]}")
        if not changes:
            return "⚠️ 没有需要更新的设置项"
        db.commit()
        return f"✅ 已更新设置：{'；'.join(changes)}"
    finally:
        from .read_data import _current_db
        if _current_db.get() is None:
            db.close()
