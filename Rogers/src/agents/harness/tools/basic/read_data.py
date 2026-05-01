"""Agent 数据读取工具

用户登录后由 AgentContext 设置 user_id 和 db session，
工具自动从 contextvars 获取，无需手动传入。
"""

# mypy: disable-error-code="operator, arg-type, call-arg"
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date
from decimal import Decimal

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock
from sqlalchemy.orm import Session

from src.fitme.models import (
    HealthMetric,
    TrainingPlan,
    DietMeal,
    User,
    UserSettings,
    StreakStats,
    DailyDietSummary,
    RecommendedTraining,
    RecommendedFood,
)

# 由 AgentContext 在用户登录后设置，工具函数内部使用
_current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)
_current_db: ContextVar[Session | None] = ContextVar("current_db", default=None)


@contextmanager
def get_db():
    """获取当前数据库 session。

    优先使用 AgentContext 设置的共享 session；
    未设置时会创建一个临时 session，退出时自动关闭。
    """
    db = _current_db.get()
    if db is not None:
        yield db
        return
    from src.fitme.utils.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_user() -> int | None:
    """获取当前登录用户 ID，返回 None 表示未登录。"""
    return _current_user_id.get()


def _fmt_val(v) -> str:
    """格式化可能为 None 或 Decimal 的值。"""
    if v is None:
        return "无数据"
    if isinstance(v, Decimal):
        return str(float(v))
    return str(v)


def _tool_resp(text: str) -> ToolResponse:
    """将字符串包装为 ToolResponse。"""
    return ToolResponse(content=[TextBlock(type="text", text=text)])


# =========================================================================
# 工具函数
# =========================================================================
def get_user_profile() -> ToolResponse:
    """获取当前用户基本信息。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            return _tool_resp("用户不存在")
        lines = [
            f"用户名：{user.name}",
            f"邮箱：{user.email}",
            f"注册时间：{user.created_at}",
        ]
        if user.role:
            lines.append(f"角色：{user.role}")
        return _tool_resp("\n".join(lines))


def get_health_summary() -> ToolResponse:
    """获取用户最新健康指标（体重、体脂、BMI）。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        latest = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id
        ).order_by(HealthMetric.measure_date.desc()).first()
        if not latest:
            return _tool_resp("暂无健康数据，请记录你的身体指标")
        lines = [
            f"最新健康指标（{latest.measure_date}）",
            f"  体重：{_fmt_val(latest.weight)} kg",
            f"  身高：{_fmt_val(latest.height)} cm",
            f"  体脂率：{_fmt_val(latest.body_fat)}%",
            f"  BMI：{_fmt_val(latest.bmi)}（{latest.bmi_status}）",
        ]
        return _tool_resp("\n".join(lines))


def get_health_history(limit: int = 7) -> ToolResponse:
    """获取近期健康指标变化趋势。

    Args:
        limit: 返回最近 N 条记录，默认 7 条。
    """
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        records = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id
        ).order_by(HealthMetric.measure_date.desc()).limit(limit).all()
        if not records:
            return _tool_resp("暂无历史记录")
        lines = [f"最近 {len(records)} 条健康指标："]
        for r in records:
            lines.append(
                f"  {r.measure_date} | 体重 {_fmt_val(r.weight)}kg | "
                f"体脂 {_fmt_val(r.body_fat)}% | BMI {_fmt_val(r.bmi)}"
            )
        return _tool_resp("\n".join(lines))


def get_training_today() -> ToolResponse:
    """获取今日训练计划。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        today = date.today()
        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date == today
        ).all()
        if not plans:
            return _tool_resp("今天没有训练计划，好好休息吧！")
        lines = ["今天的训练计划："]
        for p in plans:
            lines.append(
                f"  {p.plan_name} | {p.plan_type} | "
                f"预计 {p.estimated_duration}分钟 | 强度 {p.target_intensity} | "
                f"状态 {p.status}"
            )
            if p.note:
                lines.append(f"    备注：{p.note}")
        return _tool_resp("\n".join(lines))


def get_training_weekly() -> ToolResponse:
    """获取本周训练统计和安排。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= week_start
        ).order_by(TrainingPlan.scheduled_date).all()
        completed = [p for p in plans if p.status == "completed"]
        pending = [p for p in plans if p.status == "pending"]
        streak = db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
        streak_days = streak.training_streak if streak else 0
        lines = [
            f"本周训练统计",
            f"  连续训练 {streak_days} 天",
            f"  已完成 {len(completed)} 项",
            f"  待完成 {len(pending)} 项",
        ]
        days_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        if plans:
            lines.append("")
            lines.append("  安排：")
            for p in plans:
                day_name = days_names[p.scheduled_date.weekday()]
                status_tag = "已完成" if p.status == "completed" else "待完成"
                lines.append(
                    f"    {day_name} {status_tag} {p.plan_name} | "
                    f"{p.plan_type} | {p.estimated_duration}分钟"
                )
        return _tool_resp("\n".join(lines))


def get_training_recommendations(limit: int = 5) -> ToolResponse:
    """获取推荐的训练计划。"""
    with get_db() as db:
        plans = db.query(RecommendedTraining).filter(
            RecommendedTraining.is_active == True
        ).limit(limit).all()
        if not plans:
            return _tool_resp("暂无推荐训练")
        lines = ["推荐训练计划："]
        for p in plans:
            lines.append(
                f"  {p.plan_name} | {p.plan_type} | "
                f"{p.duration}分钟 | {p.intensity} | "
                f"消耗 ~{p.calories_burned}kcal"
            )
            if p.description:
                lines.append(f"    {p.description}")
            if p.target_body_type:
                lines.append(f"    适合：{p.target_body_type}")
        return _tool_resp("\n".join(lines))


def get_diet_today() -> ToolResponse:
    """获取今日饮食记录和统计。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        meals = db.query(DietMeal).filter(
            DietMeal.user_id == user_id,
            DietMeal.meal_date == date.today()
        ).order_by(DietMeal.meal_time).all()
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        total_calories = sum(m.calories for m in meals)
        total_protein = sum(float(m.protein or 0) for m in meals)
        total_carbs = sum(float(m.carbs or 0) for m in meals)
        total_fat = sum(float(m.fat or 0) for m in meals)
        total_water = sum(m.water or 0 for m in meals)
        goal = settings_obj.calorie_goal if settings_obj else 2000
        lines = [
            f"今天已摄入 {total_calories} kcal（目标 {goal} kcal，剩余 {goal - total_calories} kcal）",
            f"  蛋白 {total_protein:.1f}g | 碳水 {total_carbs:.1f}g | 脂肪 {total_fat:.1f}g | 水 {total_water}ml",
        ]
        if meals:
            lines.append("")
            lines.append("  饮食记录：")
            for m in meals:
                lines.append(
                    f"    {m.meal_type} {m.meal_name} | "
                    f"{m.calories}kcal | {m.meal_time}"
                )
        else:
            lines.append("  还没有记录今天的饮食")
        return _tool_resp("\n".join(lines))


def get_diet_weekly_trend() -> ToolResponse:
    """获取本周饮食趋势。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        summaries = db.query(DailyDietSummary).filter(
            DailyDietSummary.user_id == user_id,
            DailyDietSummary.summary_date >= week_start
        ).order_by(DailyDietSummary.summary_date).all()
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        goal = settings_obj.calorie_goal if settings_obj else 2000
        if not summaries:
            return _tool_resp("本周暂无饮食统计")
        lines = ["本周饮食趋势："]
        days_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for s in summaries:
            day_name = days_names[s.summary_date.weekday()]
            pct = int(s.total_calories / goal * 100) if goal > 0 else 0
            protein_ok = "达标" if s.protein_goal_met else "未达标"
            water_ok = "达标" if s.water_goal_met else "未达标"
            lines.append(
                f"  {day_name}：{s.total_calories}kcal ({pct}% 目标) | "
                f"蛋白{protein_ok} | 水{water_ok}"
            )
        return _tool_resp("\n".join(lines))


def get_food_recommendations(limit: int = 5) -> ToolResponse:
    """获取推荐食物。"""
    with get_db() as db:
        foods = db.query(RecommendedFood).filter(
            RecommendedFood.is_active == True
        ).limit(limit).all()
        if not foods:
            return _tool_resp("暂无推荐食物")
        lines = ["推荐食物："]
        for f in foods:
            lines.append(
                f"  {f.food_name} | {f.calories}kcal | "
                f"蛋白 {f.protein}g | 碳水 {f.carbs}g | 脂肪 {f.fat}g"
            )
            if f.reason:
                lines.append(f"    {f.reason}")
            if f.suitable_time:
                lines.append(f"    适合时间：{f.suitable_time}")
        return _tool_resp("\n".join(lines))


def get_user_settings() -> ToolResponse:
    """获取用户设置（热量目标、运动目标等）。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        s = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not s:
            return _tool_resp("暂无用户设置")
        lines = [
            "用户设置",
            f"  每日热量目标：{s.calorie_goal} kcal",
            f"  蛋白目标：{s.protein_goal}g",
            f"  碳水目标：{s.carbs_goal}g",
            f"  脂肪目标：{s.fat_goal}g",
            f"  饮水目标：{s.water_goal}ml",
            f"  每周训练目标：{s.weekly_training_goal} 天",
        ]
        if s.weight_goal:
            lines.append(f"  目标体重：{_fmt_val(s.weight_goal)} kg")
        return _tool_resp("\n".join(lines))


def get_full_overview() -> ToolResponse:
    """获取用户综合概览（健康+训练+饮食）。"""
    user_id = require_user()
    if user_id is None:
        return _tool_resp("请先登录")
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id, User.deleted_at.is_(None)).first()
        profile = f"用户名：{user.name} | 邮箱：{user.email}" if user else "未知用户"

        latest = db.query(HealthMetric).filter(HealthMetric.user_id == user_id).order_by(HealthMetric.measure_date.desc()).first()
        health = f"最新指标（{latest.measure_date}）：体重 {latest.weight}kg, BMI {_fmt_val(latest.bmi)}" if latest else "暂无健康数据"

        today = date.today()
        plans = db.query(TrainingPlan).filter(TrainingPlan.user_id == user_id, TrainingPlan.scheduled_date == today).all()
        training = f"今天 {len(plans)} 个训练计划" if plans else "今天无训练"

        meals = db.query(DietMeal).filter(DietMeal.user_id == user_id, DietMeal.meal_date == today).all()
        total_cal = sum(m.calories for m in meals)
        diet = f"今天已摄入 {total_cal} kcal" if meals else "今天未记录饮食"

        return _tool_resp(f"{profile}\n{health}\n{training}\n{diet}")
