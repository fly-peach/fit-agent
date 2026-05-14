"""Agent 技能管理模块

使用 AgentScope 的 register_agent_skill API 注册 fitme 的 CLI skills。
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 技能模板目录（相对于本文件的路径）
_SKILLS_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "skills"


def get_skills_base_dir() -> str:
    """获取 skills 基础目录（模板目录）。

    AgentScope 的 register_agent_skill 会扫描该目录下的 SKILL.md，
    将技能名称、描述、目录路径注册到 Toolkit 的 self.skills 中，
    之后可通过 ``get_agent_skill_prompt()`` 获取技能提示词。
    """
    skills_dir = str(_SKILLS_TEMPLATES_DIR / "fitme-skills")
    if not os.path.isdir(skills_dir):
        logger.warning("Skills directory not found: %s", skills_dir)
    return skills_dir


def register_all_skills(toolkit, include_skills: list[str] | None = None) -> None:
    """注册指定的 fitme CLI skills 到给定的 Toolkit 实例。

    遍历 skills 目录下的子技能目录，对每个包含 SKILL.md 的目录
    调用 ``register_agent_skill()``。

    Args:
        toolkit: AgentScope 的 Toolkit 实例。
        include_skills: 要注册的技能名称列表（如 ['fitme-diet', 'fitme-user']），
                       None 表示注册所有技能。
    """
    base_dir = get_skills_base_dir()

    if not os.path.isdir(base_dir):
        logger.warning("Skills base directory does not exist: %s", base_dir)
        return

    # 注册主技能（fitme-skills 本身的 SKILL.md）
    main_skill_md = os.path.join(base_dir, "SKILL.md")
    if os.path.isfile(main_skill_md):
        try:
            toolkit.register_agent_skill(base_dir)
            logger.info("Registered main skill: %s", base_dir)
        except Exception as e:
            logger.warning("Failed to register main skill: %s", e)
    else:
        logger.warning("Main SKILL.md not found: %s", main_skill_md)

    # 注册子技能（fitme-skills 下的各子目录）
    for entry in sorted(os.listdir(base_dir)):
        child_path = os.path.join(base_dir, entry)
        if os.path.isdir(child_path):
            skill_md = os.path.join(child_path, "SKILL.md")
            if os.path.isfile(skill_md):
                # 检查是否在允许列表中
                if include_skills is not None and entry not in include_skills:
                    logger.info("Skipping sub-skill: %s (not in include list)", entry)
                    continue
                try:
                    toolkit.register_agent_skill(child_path)
                    logger.info("Registered sub-skill: %s", entry)
                except Exception as e:
                    logger.warning("Failed to register sub-skill '%s': %s", entry, e)
