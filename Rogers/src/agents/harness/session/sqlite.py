"""
Harness Session SQLite

SQLite 会话管理（替换 fakeredis RedisSession）
基于 AgentScope SessionBase 实现，会话状态持久化到 SQLite。
与 AgentScope 的 stop_chat / 任务管理完全兼容。
"""
from __future__ import annotations

import json
import sqlite3
import logging
from pathlib import Path

from agentscope.session import SessionBase
from agentscope.module import StateModule

logger = logging.getLogger(__name__)


class SqliteSession(SessionBase):
    """基于 SQLite 的会话状态管理。

    持久化到 fituser.db 的 ``agent_sessions`` 表，
    服务重启不丢失。
    """

    def __init__(self, db_path: str | Path) -> None:
        """初始化 SQLite 会话。

        Args:
            db_path: SQLite 数据库文件路径（复用 fituser.db）
        """
        self.db_path = str(db_path)

    # ── SessionBase 接口实现 ──────────────────────────────────────────────

    async def save_session_state(
        self,
        session_id: str, user_id: str = "",
        **state_modules_mapping: StateModule,
    ) -> None:
        """保存会话状态到 SQLite。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            **state_modules_mapping: 状态模块映射（如 agent=agent_instance）
        """
        state_data = {
            name: module.state_dict()
            for name, module in state_modules_mapping.items()
        }
        json_data = json.dumps(state_data, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id TEXT,
                    user_id TEXT DEFAULT '',
                    state_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, user_id)
                )""",
            )
            conn.execute(
                """INSERT INTO agent_sessions (session_id, user_id, state_data, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(session_id, user_id) DO UPDATE SET
                       state_data = excluded.state_data,
                       updated_at = CURRENT_TIMESTAMP""",
                (session_id, user_id, json_data),
            )
            conn.commit()

        logger.info(
            "Saved session state for session_id=%s user_id=%s", session_id, user_id,
        )

    async def load_session_state(
        self,
        session_id: str, user_id: str = "",
        allow_not_exist: bool = True,
        **state_modules_mapping: StateModule,
    ) -> None:
        """从 SQLite 加载会话状态。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            allow_not_exist: 会话不存在时是否静默跳过
            **state_modules_mapping: 状态模块映射
        """
        if not Path(self.db_path).exists():
            if allow_not_exist:
                logger.info("DB %s not found, skip loading session", self.db_path)
                return
            raise FileNotFoundError(f"Database {self.db_path} does not exist")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT state_data FROM agent_sessions WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            row = cursor.fetchone()

            if row is None:
                if allow_not_exist:
                    logger.info(
                        "Session %s not found for user %s, skip loading",
                        session_id, user_id,
                    )
                    return
                raise ValueError(
                    f"Session {session_id} not found for user {user_id}"
                )

            state_data = json.loads(row[0])
            for name, module in state_modules_mapping.items():
                if name in state_data:
                    module.load_state_dict(state_data[name])

            logger.info(
                "Loaded session state for session_id=%s user_id=%s", session_id, user_id,
            )
