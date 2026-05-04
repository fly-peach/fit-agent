"""Dream 记忆优化器

使用 LLM 对长期记忆进行去重、合并、提炼高价值信息。
参考 QwenPaw 的 Dream 优化模式。
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("fitagent")

DREAM_OPTIMIZE_PROMPT = """你是一个记忆优化专家。请帮助用户整理和优化他们的长期记忆。

任务：
1. 阅读用户的历史交互日志和当前长期记忆
2. 去除重复和过时的信息
3. 合并相似主题的内容
4. 提炼高价值的关键信息
5. 保持记忆精简但完整

要求：
- 保持用户画像、目标、偏好等关键信息
- 移除已经完成或不再相关的信息
- 突出最近的进展和变化
- 用清晰的结构组织内容

请输出优化后的 MEMORY.md 内容，格式与输入相同。
"""


class MemoryOptimizer:
    """Dream 记忆优化器。"""

    def __init__(self, long_term_memory, model=None):
        self.ltm = long_term_memory
        self.model = model

    async def optimize(self, date: str | None = None) -> dict:
        """对指定日期进行记忆优化。

        Args:
            date: 要优化的日志日期，默认今天

        Returns:
            优化结果字典
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        daily_log = self.ltm.get_daily_log(date)
        current_memory = self.ltm.load_memory()

        if not daily_log:
            return {"success": False, "reason": f"No daily log found for {date}"}

        if not self.model:
            return {"success": False, "reason": "Model not available for optimization"}

        try:
            from agentscope.message import Msg

            prompt = f"""当前长期记忆：
{current_memory}

当日交互日志（{date}）：
{daily_log}

请输出优化后的 MEMORY.md 内容。"""

            messages = [
                Msg("system", DREAM_OPTIMIZE_PROMPT, "system"),
                Msg("user", prompt, "user"),
            ]

            response = await self.model(messages)

            optimized_content = ""
            if hasattr(response, "content"):
                content = response.content
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            optimized_content += block.get("text", "")
                elif isinstance(content, str):
                    optimized_content = content
            elif isinstance(response, str):
                optimized_content = response

            if not optimized_content:
                return {"success": False, "reason": "Optimization returned empty content"}

            backup_path = self.ltm.create_backup(date)
            self.ltm.save_memory(optimized_content)

            return {
                "success": True,
                "date": date,
                "backup_path": str(backup_path) if backup_path else None,
                "content_length": len(optimized_content),
            }

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {"success": False, "reason": str(e)}
