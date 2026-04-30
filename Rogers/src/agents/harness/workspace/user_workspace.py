"""用户工作区管理器 — 每个用户的 agents.md、soul.md 和会话存储。"""
from __future__ import annotations

import shutil
from pathlib import Path


_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent / "agent_db" / "workspace"
_TEMPLATE_DIR = _WORKSPACE_ROOT / "templates"
_USERS_DIR = _WORKSPACE_ROOT / "users"


def get_user_workspace(user_id: int | str) -> Path:
    """返回指定用户的工作区目录。"""
    return _USERS_DIR / str(user_id)


def get_user_sessions_dir(user_id: int | str) -> Path:
    """返回指定用户的会话目录。"""
    return get_user_workspace(user_id) / "sessions"


def ensure_user_workspace(user_id: int | str) -> Path:
    """创建用户工作区，如果是首次使用则复制模板文件。

    返回用户工作区路径。可安全并发调用 — 模板复制是幂等的。
    """
    user_dir = get_user_workspace(user_id)
    if user_dir.exists():
        return user_dir

    user_dir.mkdir(parents=True, exist_ok=True)

    # 复制模板文件（agents.md, soul.md）
    if _TEMPLATE_DIR.exists():
        for template_file in _TEMPLATE_DIR.iterdir():
            if template_file.is_file() and template_file.suffix == ".md":
                shutil.copy2(template_file, user_dir / template_file.name)

    # 创建会话目录
    get_user_sessions_dir(user_id).mkdir(parents=True, exist_ok=True)

    return user_dir


def load_user_sys_prompt(user_id: int | str) -> str:
    """通过读取 agents.md 和 soul.md 构建完整的系统提示。

    拼接 agents.md（主要指令）和 soul.md（性格），中间用分隔符隔开。
    如果两个文件都不存在则返回空字符串。
    """
    user_dir = get_user_workspace(user_id)
    parts = []

    agents_md = user_dir / "agents.md"
    if agents_md.exists():
        parts.append(agents_md.read_text(encoding="utf-8"))

    soul_md = user_dir / "soul.md"
    if soul_md.exists():
        parts.append(f"\n--- 性格 ---\n{soul_md.read_text(encoding='utf-8')}")

    return "\n\n".join(parts)


def load_user_context(user_id: int | str) -> str:
    """查询数据库获取用户基本数据，返回格式化字符串。

    创建临时 DB 会话，查询 User、UserSettings、最新 HealthMetric 和
    StreakStats。如果用户已删除或数据缺失则返回空字符串。
    """
    uid = int(user_id)

    from decimal import Decimal

    from fitme.utils.database import SessionLocal
    from src.fitme.models.models import HealthMetric, StreakStats, User, UserSettings

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.user_id == uid,
            User.deleted_at.is_(None),
        ).first()
        if not user:
            return ""

        lines = [
            "## 用户信息",
            f"当前用户 ID：{uid}",
            f"用户名：{user.name}",
            f"邮箱：{user.email}",
            f"注册时间：{user.created_at}",
        ]

        # 用户设置
        settings = db.query(UserSettings).filter(UserSettings.user_id == uid).first()
        if settings:
            lines.append("")
            lines.append("用户设置：")
            lines.append(f"  每日热量目标：{settings.calorie_goal} kcal")
            lines.append(f"  蛋白目标：{settings.protein_goal}g")
            lines.append(f"  碳水目标：{settings.carbs_goal}g")
            lines.append(f"  脂肪目标：{settings.fat_goal}g")
            lines.append(f"  饮水目标：{settings.water_goal}ml")
            lines.append(f"  每周训练目标：{settings.weekly_training_goal} 天")
            if settings.weight_goal:
                goal_val = float(settings.weight_goal) if isinstance(settings.weight_goal, Decimal) else settings.weight_goal
                lines.append(f"  目标体重：{goal_val} kg")

        # 最新健康指标
        latest_health = db.query(HealthMetric).filter(
            HealthMetric.user_id == uid,
        ).order_by(HealthMetric.measure_date.desc()).first()
        if latest_health:
            lines.append("")
            lines.append("最新健康指标：")
            if latest_health.weight:
                w = float(latest_health.weight) if isinstance(latest_health.weight, Decimal) else latest_health.weight
                lines.append(f"  体重：{w} kg")
            if latest_health.height:
                h = float(latest_health.height) if isinstance(latest_health.height, Decimal) else latest_health.height
                lines.append(f"  身高：{h} cm")
            if latest_health.body_fat:
                bf = float(latest_health.body_fat) if isinstance(latest_health.body_fat, Decimal) else latest_health.body_fat
                lines.append(f"  体脂率：{bf}%")
            if latest_health.bmi:
                bmi = float(latest_health.bmi) if isinstance(latest_health.bmi, Decimal) else latest_health.bmi
                lines.append(f"  BMI：{bmi}（{latest_health.bmi_status}）")

        # 连续记录统计
        streak = db.query(StreakStats).filter(StreakStats.user_id == uid).first()
        if streak and (streak.training_streak or streak.diet_streak):
            lines.append("")
            lines.append("连续记录：")
            if streak.training_streak:
                lines.append(f"  连续训练：{streak.training_streak} 天")
            if streak.diet_streak:
                lines.append(f"  连续饮食记录：{streak.diet_streak} 天")

        lines.append("")
        lines.append("## 数据访问规则")
        lines.append(f"- 你只能读取和修改当前用户（ID: {uid}）的数据")
        lines.append("- 所有工具函数已自动绑定到当前用户，你无需也不能传入 user_id")
        lines.append("- 禁止尝试访问其他用户的数据")
        lines.append("- 如果用户请求查看或修改他人数据，拒绝该请求")

        return "\n".join(lines)

    except Exception:
        return ""
    finally:
        db.close()
