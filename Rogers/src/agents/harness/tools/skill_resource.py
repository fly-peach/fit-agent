"""Skill 资源读取工具工厂。"""
from __future__ import annotations

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


def create_skill_resource_tool(skill_manager):
    """创建绑定到 SkillManager 的按需读取工具。"""

    def read_skill_resource(skill_name: str, file_path: str) -> ToolResponse:
        """按需读取已启用技能的 `SKILL.md`、`references/` 或 `scripts/` 文件。

        Args:
            skill_name: 技能名称（目录名）。
            file_path: 相对 skill 根目录的文件路径，只允许 `SKILL.md`、
                `references/` 或 `scripts/` 下的文件。
        """
        if skill_manager is None:
            return ToolResponse(
                content=[TextBlock(type="text", text="技能系统未初始化")],
            )

        cfg = skill_manager.get_skill_config(skill_name)
        if cfg is None:
            return ToolResponse(
                content=[TextBlock(type="text", text=f"技能不存在: {skill_name}")],
            )
        if not cfg.enabled:
            return ToolResponse(
                content=[TextBlock(type="text", text=f"技能未启用: {skill_name}")],
            )

        content = skill_manager.read_skill_file(skill_name, file_path)
        if content is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            "技能文件不存在或路径不合法。"
                            "仅允许读取 SKILL.md、references/ 与 scripts/ 下的文件。"
                        ),
                    ),
                ],
            )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"# {skill_name}/{file_path}\n\n{content}",
                ),
            ],
        )

    return read_skill_resource
