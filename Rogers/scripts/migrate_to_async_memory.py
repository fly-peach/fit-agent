"""
数据迁移脚本：将旧 chat_messages 表中的消息迁移到 AsyncSQLAlchemyMemory。

背景：
- 旧系统：消息存储在 chat_messages 表（UI 格式 JSON）
- 新系统：消息通过 AsyncSQLAlchemyMemory 存储为 Msg 对象

本脚本读取旧 chat_messages 表，将其作为 Msg 对象写入新表。
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate")


async def migrate_chat_messages():
    """将 chat_messages 表数据迁移到 AsyncSQLAlchemyMemory。"""
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

    from src.fitme.utils.database import UserSessionLocal, async_agent_memory_engine
    from src.agents.harness.memory.fitagent_memory import FitAgentSQLMemory
    from agentscope.message import Msg

    # 1. 读取所有需要迁移的 session
    db = UserSessionLocal()
    try:
        sessions = db.execute(
            "SELECT DISTINCT session_id FROM chat_messages ORDER BY session_id"
        ).fetchall()
        session_ids = [row[0] for row in sessions]
    finally:
        db.close()

    if not session_ids:
        logger.info("没有找到需要迁移的 chat_messages 数据")
        return

    logger.info(f"找到 {len(session_ids)} 个会话需要迁移")

    total_migrated = 0

    for session_id in session_ids:
        # 2. 读取旧消息
        db = UserSessionLocal()
        try:
            rows = db.execute(
                "SELECT cm.id, cm.session_id, cm.role, cm.content, cm.created_at "
                "FROM chat_messages cm "
                "WHERE cm.session_id = :sid "
                "ORDER BY cm.created_at ASC",
                {"sid": session_id},
            ).fetchall()

            # 找出这个 session 属于哪个 user
            user_row = db.execute(
                "SELECT user_id FROM chat_sessions WHERE id = :sid",
                {"sid": session_id},
            ).fetchone()
            if not user_row:
                logger.warning(f"会话 {session_id} 没有对应的 chat_sessions 记录，跳过")
                continue
            user_id = str(user_row[0])
        finally:
            db.close()

        # 3. 写入 AsyncSQLAlchemyMemory
        memory = FitAgentSQLMemory(
            engine_or_session=async_agent_memory_engine,
            user_id=user_id,
            session_id=session_id,
        )

        try:
            for row in rows:
                msg_id, sid, role, content_json, created_at = row

                # 从旧的 UI 格式 JSON 提取文本
                try:
                    ui_data = json.loads(content_json)
                    cards = ui_data.get("cards", [])
                    text_parts = []
                    for card in cards:
                        if isinstance(card, dict):
                            data = card.get("data", "")
                            if data:
                                text_parts.append(str(data))
                    text = "\n".join(text_parts) if text_parts else content_json
                except (json.JSONDecodeError, TypeError):
                    text = content_json if content_json else ""

                if not text:
                    continue

                msg = Msg(name=role, content=text, role=role)
                # 手动设置 ID 以保持一致性
                msg.id = str(msg_id)

                await memory.add(msg)
                total_migrated += 1

            logger.info(f"  会话 {session_id} (user={user_id}): 迁移 {len(rows)} 条消息")
        finally:
            await memory.close()

    logger.info(f"迁移完成！共迁移 {total_migrated} 条消息到 {len(session_ids)} 个会话")


if __name__ == "__main__":
    asyncio.run(migrate_chat_messages())
