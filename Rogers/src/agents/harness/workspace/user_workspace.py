"""用户工作区管理器 — 管理 Agent 配置文件和系统提示词。

从数据库加载提示词模板，不再依赖本地文件系统。
"""
from __future__ import annotations

import re
from pathlib import Path
from src.agents.harness.templates.templates import get_template_path
from src.agents.harness.workspace.prompt_templates import (
    get_user_prompt_templates,
    get_or_create_prompt_templates,
)


# 模板目录通过统一模块获取
_TEMPLATE_DIR = get_template_path()


# ---------------------------------------------------------------------------
# PromptBuilder — 从数据库加载提示词，支持条件区块
# ---------------------------------------------------------------------------

class PromptBuilder:
    """从数据库提示词构建系统提示，支持条件区块。

    条件区块使用 HTML 注释标记：
    - ``<!-- memory:start -->`` / ``<!-- memory:end -->``

    当对应的功能启用时，区块内的内容会包含在提示中（标记被移除）；
    禁用时，整个区块会被移除。
    """

    MEMORY_PATTERN = re.compile(
        r"<!-- memory:start -->.*?<!-- memory:end -->",
        re.DOTALL,
    )

    def __init__(
        self,
        agents_md: str = "",
        soul_md: str = "",
        memory_prompt_enabled: bool = True,
    ):
        self.agents_md = agents_md
        self.soul_md = soul_md
        self.memory_prompt_enabled = memory_prompt_enabled

    def build(self) -> str:
        """处理条件区块后拼接返回。"""
        parts = []

        if self.agents_md:
            content = self._process_memory_section(self.agents_md)
            parts.append(content)

        if self.soul_md:
            parts.append(
                f"\n--- 性格 ---\n{self.soul_md}",
            )

        return "\n\n".join(parts)

    def _process_memory_section(self, content: str) -> str:
        """处理 memory 条件区块。"""
        if "<!-- memory:start -->" not in content:
            return content

        if self.memory_prompt_enabled:
            content = content.replace("<!-- memory:start -->", "")
            content = content.replace("<!-- memory:end -->", "")
            return content.strip()
        else:
            return self.MEMORY_PATTERN.sub("", content).strip()


def _get_user_prompt_templates_from_db(user_id: int):
    """从数据库获取用户提示词模板。"""
    from src.fitme.utils.database import UserSessionLocal

    db = UserSessionLocal()
    try:
        return get_user_prompt_templates(db, user_id)
    finally:
        db.close()


def get_user_workspace(user_id: int | str) -> Path:
    """返回默认目录（保留兼容性，不再实际使用）。

    Deprecated: 不再依赖本地文件系统。
    """
    from src.fitme.utils.agent_directory import get_default_agent_directory
    return Path(get_default_agent_directory())


def ensure_user_workspace(user_id: int | str) -> Path:
    """确保数据库中有提示词模板（不再创建本地目录）。

    返回默认目录路径（保留兼容性）。
    """
    from src.fitme.utils.database import UserSessionLocal
    from src.fitme.utils.agent_directory import get_default_agent_directory

    db = UserSessionLocal()
    try:
        get_or_create_prompt_templates(db, int(user_id))
    finally:
        db.close()

    return Path(get_default_agent_directory())


def load_user_sys_prompt(
    user_id: int | str,
    memory_prompt_enabled: bool = True,
) -> str:
    """通过数据库加载提示词并构建系统提示。

    支持条件区块：
    - ``<!-- memory:start -->`` — 根据 memory_prompt_enabled 决定是否包含

    Args:
        user_id: 用户 ID
        memory_prompt_enabled: 是否包含记忆引导区块

    Returns:
        拼接后的系统提示字符串
    """
    from src.fitme.utils.database import UserSessionLocal

    db = UserSessionLocal()
    try:
        templates = get_user_prompt_templates(db, int(user_id))
        if templates:
            builder = PromptBuilder(
                agents_md=templates.agents_md,
                soul_md=templates.soul_md,
                memory_prompt_enabled=memory_prompt_enabled,
            )
            return builder.build()
        return ""
    finally:
        db.close()


def load_user_context(user_id: int | str) -> str:
    """查询数据库获取用户基本数据，返回格式化字符串。

    创建临时 DB 会话，查询 User、UserSettings、最新 HealthMetric 和
    StreakStats。如果用户已删除或数据缺失则返回空字符串。
    """
    uid = int(user_id)

    from decimal import Decimal

    from src.fitme.utils.database import SessionLocal
    from src.fitme.models.user_db import User, UserSettings, HealthMetric, StreakStats

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
