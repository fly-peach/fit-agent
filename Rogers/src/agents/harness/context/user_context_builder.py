"""用户上下文构建模块

从 fituser.db 查询用户健康数据摘要 + 用户记忆画像（user_memory_profile），
拼接为约 200 字的完整画像上下文字符串，在新会话时注入 Agent。
"""

from datetime import date, timedelta, datetime

from src.fitme.utils.database import UserDBContext
from src.fitme.models import HealthMetric, TrainingRecord, DailyDietSummary, StreakStats
from src.agents.harness.memory.user_profile import get_user_facts_by_category


def build_user_context(user_id: int) -> str:
    """构建用户完整画像上下文。

    Args:
        user_id: 用户 ID

    Returns:
        格式化的画像字符串，包含健康数据、目标、偏好、成就等。
    """
    health = _build_health_summary(user_id)
    memory = _build_memory_summary(user_id)

    if health and memory:
        return health + " | " + memory
    return health or memory


def _build_health_summary(user_id: int) -> str:
    """构建健康数据摘要（约 50 字）。"""
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    week_ago_dt = datetime.combine(week_ago, datetime.min.time())
    month_ago_dt = datetime.combine(month_ago, datetime.min.time())

    with UserDBContext() as db:
        latest = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id,
        ).order_by(HealthMetric.measure_date.desc()).first()

        week_trainings = int(db.query(TrainingRecord).filter(
            TrainingRecord.user_id == user_id,
            TrainingRecord.completed_at >= week_ago_dt,
        ).count())

        week_diet = db.query(DailyDietSummary).filter(
            DailyDietSummary.user_id == user_id,
            DailyDietSummary.summary_date >= week_ago,
        ).all()
        avg_calories = (
            round(sum(float(d.total_calories or 0) for d in week_diet) / len(week_diet))
            if week_diet else None
        )

        month_metrics = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id,
            HealthMetric.measure_date >= month_ago,
        ).order_by(HealthMetric.measure_date.asc()).all()
        weight_change = None
        if len(month_metrics) >= 2:
            weight_change = round(
                float(month_metrics[-1].weight) - float(month_metrics[0].weight), 1
            )

        month_trainings = int(db.query(TrainingRecord).filter(
            TrainingRecord.user_id == user_id,
            TrainingRecord.completed_at >= month_ago_dt,
        ).count())

        streak = db.query(StreakStats).filter(
            StreakStats.user_id == user_id,
        ).first()

    parts = []

    if latest and latest.weight:
        parts.append(f"当前体重{float(latest.weight)}kg")

    week_items = []
    if week_trainings:
        week_items.append(f"训练{week_trainings}次")
    if avg_calories:
        week_items.append(f"日均摄入{avg_calories}千卡")
    if week_items:
        parts.append("近1周" + "，".join(week_items))

    month_items = []
    if weight_change is not None:
        month_items.append(f"体重{weight_change:+.1f}kg")
    if month_trainings:
        month_items.append(f"训练{month_trainings}次")
    if streak and streak.diet_streak:
        month_items.append(f"饮食达标{int(streak.diet_streak)}天")
    if month_items:
        parts.append("近1月" + "，".join(month_items))

    return "；".join(parts) if parts else ""


def _build_memory_summary(user_id: int) -> str:
    """从 user_memory_profile 构建用户画像摘要。"""
    try:
        facts = get_user_facts_by_category(user_id, [
            "goal", "food", "exercise", "health", "achievement",
            "personality", "note",
        ])
    except Exception:
        return ""

    sections = []

    goals = facts.get("goal", [])
    if goals:
        items = _format_facts(goals)
        sections.append("目标：" + "；".join(items))

    prefs = []
    for cat in ("food", "exercise"):
        for f in facts.get(cat, []):
            prefs.append(f"{f['key']}={f['value']}")
    if prefs:
        sections.append("偏好：" + "；".join(prefs))

    health_facts = facts.get("health", [])
    if health_facts:
        items = _format_facts(health_facts)
        sections.append("健康：" + "；".join(items))

    achievements = facts.get("achievement", [])
    if achievements:
        items = _format_facts(achievements)
        sections.append("成就：" + "；".join(items))

    personality = facts.get("personality", [])
    if personality:
        items = _format_facts(personality)
        sections.append("特点：" + "；".join(items))

    notes = facts.get("note", [])
    if notes:
        items = _format_facts(notes)
        sections.append("备注：" + "；".join(items))

    return "。".join(sections) if sections else ""


def _format_facts(facts: list[dict]) -> list[str]:
    """将事实列表格式化为简短的文本片段。"""
    result = []
    for f in facts:
        val = str(f["value"])
        if len(val) > 60:
            val = val[:57] + "..."
        key = f["key"]
        result.append(f"{key}={val}")
    return result
