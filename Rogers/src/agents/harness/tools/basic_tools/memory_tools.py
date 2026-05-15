"""Agent 用户记忆工具函数

提供 record_user_fact() 和 get_user_memory() 两个工具函数，
让 Agent 可以在对话中主动记录和查询用户的画像数据。

数据直接写入 fituser.db 的 user_memory_profile 表（EAV 模式），
绕过 HTTP API。
"""

import json
import logging

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from src.agents.harness.memory.user_profile import (
    upsert_user_fact,
    delete_user_fact,
    get_user_facts,
)

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"food", "exercise", "health", "goal", "achievement", "personality", "note"}


async def record_user_fact(
    category: str,
    key: str,
    value: str,
    user_id: int = 0,
    confidence: float = 1.0,
    source: str = "explicit",
) -> ToolResponse:
    """记录或更新一条用户画像事实。

    Args:
        category: 分类 (food/exercise/health/goal/achievement/personality/note)
        key: 属性名，如 favorite_foods
        value: 属性值
        user_id: 用户 ID（由工具系统自动注入）
        confidence: 置信度 0.0~1.0，默认 1.0
        source: 数据来源 (explicit/inferred/extracted)，默认 explicit
    """
    if category not in VALID_CATEGORIES:
        return ToolResponse(content=[
            TextBlock(type="text", text=f"错误: 无效分类 '{category}'，可用: {', '.join(sorted(VALID_CATEGORIES))}")
        ])

    if not user_id:
        return ToolResponse(content=[
            TextBlock(type="text", text="错误: 无法获取用户ID，请先登录")
        ])

    try:
        fact_id = upsert_user_fact(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
        )
        logger.info("User fact recorded: user_id=%s category=%s key=%s id=%s",
                     user_id, category, key, fact_id)
        return ToolResponse(content=[
            TextBlock(type="text", text=f"已记录用户画像: [{category}] {key} = {value} (id={fact_id})")
        ])
    except Exception as e:
        logger.exception("Failed to record user fact")
        return ToolResponse(content=[
            TextBlock(type="text", text=f"记录失败: {e}")
        ])


async def delete_user_fact_tool(
    key: str,
    user_id: int = 0,
) -> ToolResponse:
    """删除（软删除）一条用户画像事实。

    Args:
        key: 属性名
        user_id: 用户 ID（由工具系统自动注入）
    """
    if not user_id:
        return ToolResponse(content=[
            TextBlock(type="text", text="错误: 无法获取用户ID，请先登录")
        ])

    try:
        ok = delete_user_fact(user_id=user_id, key=key)
        if ok:
            return ToolResponse(content=[
                TextBlock(type="text", text=f"已删除用户画像: key={key}")
            ])
        else:
            return ToolResponse(content=[
                TextBlock(type="text", text=f"未找到 key={key} 的记录")
            ])
    except Exception as e:
        logger.exception("Failed to delete user fact")
        return ToolResponse(content=[
            TextBlock(type="text", text=f"删除失败: {e}")
        ])


async def get_user_memory(
    category: str = "",
    user_id: int = 0,
) -> ToolResponse:
    """获取用户的所有画像数据。

    Args:
        category: 可选，按分类过滤 (food/exercise/health/goal/achievement/personality/note)
        user_id: 用户 ID（由工具系统自动注入）
    """
    if not user_id:
        return ToolResponse(content=[
            TextBlock(type="text", text="错误: 无法获取用户ID，请先登录")
        ])

    try:
        facts = get_user_facts(
            user_id=user_id,
            category=category if category else None,
        )
        if not facts:
            return ToolResponse(content=[
                TextBlock(type="text", text="暂无用户画像数据")
            ])

        text = json.dumps(facts, ensure_ascii=False, indent=2)
        return ToolResponse(content=[TextBlock(type="text", text=text)])
    except Exception as e:
        logger.exception("Failed to get user memory")
        return ToolResponse(content=[
            TextBlock(type="text", text=f"查询失败: {e}")
        ])
