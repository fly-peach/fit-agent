"""记忆优化工具函数。

注意：传统的每日定时记忆优化已被心跳机制取代。
Heartbeat 通过 HEARTBEAT.md 让 agent 自主执行记忆维护（更新 MEMORY.md 等），
比固定的 cron 任务更灵活和智能化。

如果需要在特定场景下单次调用优化，可以使用 ``optimize_memory_for_user()``。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, date

from src.agents.harness.memory.long_term_memory import LongTermMemory
from src.agents.harness.memory.memory_optimizer import MemoryOptimizer
from src.agents.harness.workspace.user_workspace import get_user_workspace
from src.agents.harness.chats.crud import get_messages
from src.agents.harness.chats.models import ChatSession
from src.fitme.utils.database import UserSessionLocal

logger = logging.getLogger(__name__)


async def optimize_memory_for_user(user_id: int) -> bool:
    """对单个用户执行当日聊天记录 → 记忆优化。

    流程：
    1. 从数据库拉取该用户今日的所有聊天消息
    2. 拼成可读文本追加到当日日志
    3. 调用 MemoryOptimizer 执行 LLM 优化
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_date = date.today()

    user_dir = get_user_workspace(user_id)
    ltm = LongTermMemory(user_dir)
    ltm.init_memory_file()

    # 从数据库收集今日聊天消息
    db = UserSessionLocal()
    try:
        # 查询该用户今日的所有消息
        today_start = datetime.combine(today_date, datetime.min.time())
        today_end = today_start + timedelta(days=1)

        # 先获取用户的所有会话
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .all()
        )

        today_lines: list[str] = []
        for s in sessions:
            messages = get_messages(db, s.id)
            for m in messages:
                # 过滤今日消息
                if m.created_at is None:
                    continue
                if not (today_start <= m.created_at < today_end):
                    continue

                try:
                    msg_data = json.loads(m.content)
                    text = ""
                    if "cards" in msg_data:
                        for card in msg_data["cards"]:
                            d = card.get("data", "")
                            if isinstance(d, str):
                                text += d + "\n"
                    if text.strip():
                        today_lines.append(
                            f"**{m.role.upper()}**: {text.strip()}"
                        )
                except Exception:
                    pass

        if not today_lines:
            logger.info(
                "No chat messages for user %s today (%s), skipping",
                user_id, today_str,
            )
            return False
    finally:
        db.close()

    # 追加到当日日志
    log_content = "\n".join(today_lines)
    ltm.append_daily_log(date=today_str, content=log_content)

    # 使用 LLM 优化长期记忆
    from src.agents.agent import create_user_agent

    try:
        agent = create_user_agent(user_id)
        model = getattr(agent, "model", None)
        if model is None:
            logger.warning(
                "No model for user %s, skip memory optimization",
                user_id,
            )
            return False

        # 读取自定义优化提示词
        cfg = ltm.load_config()
        custom_prompt = cfg.get("heartbeat", {}).get("prompt", "") or ""

        optimizer = MemoryOptimizer(ltm, model)
        result = await optimizer.optimize(
            date=today_str,
            custom_prompt=custom_prompt,
        )

        if result.get("success"):
            logger.info(
                "Memory optimized for user %s, backup: %s",
                user_id, result.get("backup_path", "none"),
            )
            return True
        else:
            logger.warning(
                "Memory optimize failed for user %s: %s",
                user_id, result.get("reason", "unknown"),
            )
            return False
    except Exception:
        logger.exception(
            "Memory optimize error for user %s on %s",
            user_id, today_str,
        )
        return False


async def _get_active_user_ids() -> list[int]:
    """获取所有有对话记录的用户 ID。"""
    db = UserSessionLocal()
    try:
        result = (
            db.query(ChatSession.user_id)
            .distinct()
            .all()
        )
        return [row[0] for row in result]
    except Exception:
        logger.exception("Failed to get active user IDs")
        return []
    finally:
        db.close()


# schedule functions removed — heartbeat replaces nightly cron maintenance
