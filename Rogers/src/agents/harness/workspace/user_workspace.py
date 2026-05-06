"""用户工作区管理器 — 每个用户的 agents.md、soul.md、技能与会话存储。

新架构：用户数据存储在用户本地目录（由 user_agent_config 配置），
不再使用服务器端的 users/{user_id} 结构。
"""
from __future__ import annotations

import shutil
from pathlib import Path
from src.fitme.core.config import settings
from ..skills.skill_manager import SkillManager
from ..templates.templates import get_template_path, get_skills_template_path


# 模板目录通过统一模块获取
_TEMPLATE_DIR = get_template_path()
_SKILLS_TEMPLATE_DIR = get_skills_template_path()


def _get_user_local_dir(user_id: int) -> Path:
    """获取用户的本地 Agent 工作目录。

    优先从数据库读取用户配置的路径，如果未配置则使用默认目录。
    """
    try:
        from src.fitme.utils.database import UserSessionLocal
        from src.fitme.crud import agent_config as agent_crud
        from src.fitme.utils.agent_directory import get_default_agent_directory

        db = UserSessionLocal()
        try:
            config = agent_crud.get_user_agent_config(db, user_id)
            if config and config.local_working_dir:
                return Path(config.local_working_dir).resolve()
            return Path(get_default_agent_directory())
        finally:
            db.close()
    except Exception:
        from src.fitme.utils.agent_directory import get_default_agent_directory
        return Path(get_default_agent_directory())


def _sync_skill_manifest(user_dir: Path) -> None:
    """根据当前工作区技能目录刷新 manifest。"""
    SkillManager(user_dir).reconcile_manifest()


def get_user_workspace(user_id: int | str) -> Path:
    """返回指定用户的工作区目录。

    新架构：直接在用户本地目录操作，不再有 users/{user_id} 子目录。
    """
    return _get_user_local_dir(int(user_id))


def get_user_sessions_dir(user_id: int | str) -> Path:
    """返回指定用户的会话目录。"""
    return get_user_workspace(user_id) / "workspace" / "sessions"


def ensure_user_workspace(user_id: int | str) -> Path:
    """创建用户工作区，如果是首次使用则复制模板文件。

    返回用户工作区路径。可安全并发调用 — 模板复制是幂等的。
    即使工作区已存在，也会检查并补充缺失的模板技能。

    注意：不再使用 users/{user_id} 子目录，直接在用户本地目录操作。
    """
    user_dir = get_user_workspace(user_id)
    first_time = not user_dir.exists()

    user_dir.mkdir(parents=True, exist_ok=True)

    # 复制模板文件（agents.md, soul.md）- 仅首次创建时复制
    if first_time and _TEMPLATE_DIR.exists():
        for template_file in _TEMPLATE_DIR.iterdir():
            if template_file.is_file() and template_file.suffix == ".md":
                shutil.copy2(template_file, user_dir / template_file.name)

    # 复制默认技能（从 templates/skills/ 目录）
    # 每次都检查并补充缺失的模板技能（幂等操作）
    if _SKILLS_TEMPLATE_DIR.exists():
        user_skills_dir = user_dir / "workspace" / "skills"
        user_skills_dir.mkdir(parents=True, exist_ok=True)
        for skill_dir in _SKILLS_TEMPLATE_DIR.iterdir():
            if skill_dir.is_dir():
                dest = user_skills_dir / skill_dir.name
                if not dest.exists():
                    shutil.copytree(skill_dir, dest)

    # 创建会话目录
    get_user_sessions_dir(user_id).mkdir(parents=True, exist_ok=True)

    # 创建记忆目录
    (user_dir / "workspace" / "memory").mkdir(parents=True, exist_ok=True)

    _sync_skill_manifest(user_dir)

    return user_dir


def restock_template_skills(user_id: int | str) -> list[str]:
    """重新补充缺失的模板技能。

    从 templates/skills/ 复制缺失的模板技能到用户工作区。
    不会覆盖用户已修改的技能。

    Returns:
        新补充的技能名称列表
    """
    user_dir = get_user_workspace(user_id)
    user_skills_dir = user_dir / "workspace" / "skills"
    user_skills_dir.mkdir(parents=True, exist_ok=True)

    restocked = []
    if _SKILLS_TEMPLATE_DIR.exists():
        for skill_dir in _SKILLS_TEMPLATE_DIR.iterdir():
            if skill_dir.is_dir():
                dest = user_skills_dir / skill_dir.name
                if not dest.exists():
                    shutil.copytree(skill_dir, dest)
                    restocked.append(skill_dir.name)

    _sync_skill_manifest(user_dir)
    return restocked


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

    from src.fitme.utils.database import SessionLocal
    from src.fitme.models import HealthMetric, StreakStats, User, UserSettings

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
        user_settings = db.query(UserSettings).filter(UserSettings.user_id == uid).first()
        if user_settings:
            lines.append("")
            lines.append("用户设置：")
            lines.append(f"  每日热量目标：{user_settings.calorie_goal} kcal")
            lines.append(f"  蛋白目标：{user_settings.protein_goal}g")
            lines.append(f"  碳水目标：{user_settings.carbs_goal}g")
            lines.append(f"  脂肪目标：{user_settings.fat_goal}g")
            lines.append(f"  饮水目标：{user_settings.water_goal}ml")
            lines.append(f"  每周训练目标：{user_settings.weekly_training_goal} 天")
            if user_settings.weight_goal:
                goal_val = float(user_settings.weight_goal) if isinstance(user_settings.weight_goal, Decimal) else user_settings.weight_goal
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


# 向后兼容：保留旧的路径常量引用（指向默认目录）
_WORKSPACE_ROOT = settings.AGENT_DB_DIR / "workspace"
_USERS_DIR = _WORKSPACE_ROOT / "users"
