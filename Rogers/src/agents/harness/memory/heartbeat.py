"""Heartbeat — 定时以 HEARTBEAT.md 为查询运行 agent。

心跳机制让 agent 能主动、周期性地执行任务（如记忆维护、用户状态检查），
而不是被动等待用户输入。参考 CoPaw 的 heartbeat 模式。

用法：
    from src.agents.agent import create_user_agent
    agent = create_user_agent(user_id)
    await run_heartbeat_once(agent=agent, agent_id="default")
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages

from src.agents.config import HeartbeatConfig

logger = logging.getLogger(__name__)

HEARTBEAT_FILENAME = "HEARTBEAT.md"

# 解析 "30m", "1h", "2h30m", "90s" 格式的 interval 字符串
_EVERY_PATTERN = re.compile(
    r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$",
    re.IGNORECASE,
)

# 5 字段 cron 表达式：minute hour day month day_of_week
_CRON_FIELD_PATTERN = re.compile(r"^[\d\*\-/,]+$")


def is_cron_expression(every: str) -> bool:
    """判断 *every* 是否是 5 字段 cron 表达式。"""
    parts = (every or "").strip().split()
    if len(parts) != 5:
        return False
    return all(_CRON_FIELD_PATTERN.match(p) for p in parts)


def parse_heartbeat_every(every: str) -> int:
    """将 interval 字符串（如 '30m', '1h'）转为总秒数。

    注意：cron 表达式应通过 ``is_cron_expression`` 预先判断。
    """
    every = (every or "").strip()
    if not every:
        return 30 * 60  # 默认 30 分钟
    m = _EVERY_PATTERN.match(every)
    if not m:
        logger.warning("heartbeat every=%r invalid, using 30m", every)
        return 30 * 60
    hours = int(m.group("hours") or 0)
    minutes = int(m.group("minutes") or 0)
    seconds = int(m.group("seconds") or 0)
    total = hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else 30 * 60


def _in_active_hours(active_hours: Any) -> bool:
    """检查当前时间是否在活跃时段 [start, end] 内。"""
    if (
        not active_hours
        or not hasattr(active_hours, "start")
        or not hasattr(active_hours, "end")
    ):
        return True
    try:
        start_parts = active_hours.start.strip().split(":")
        end_parts = active_hours.end.strip().split(":")
        start_t = time(
            int(start_parts[0]),
            int(start_parts[1]) if len(start_parts) > 1 else 0,
        )
        end_t = time(
            int(end_parts[0]),
            int(end_parts[1]) if len(end_parts) > 1 else 0,
        )
    except (ValueError, IndexError, AttributeError):
        return True

    # 使用用户本地时区（兜底 UTC）
    try:
        now = datetime.now(ZoneInfo("Asia/Shanghai")).time()
    except (ZoneInfoNotFoundError, KeyError):
        now = datetime.now(timezone.utc).time()

    if start_t <= end_t:
        return start_t <= now <= end_t
    return now >= start_t or now <= end_t


async def run_heartbeat_once(
    *,
    agent: Any,
    agent_id: Optional[str] = None,
    workspace_dir: Optional[Path] = None,
    heartbeat_cfg: Optional[HeartbeatConfig] = None,
) -> None:
    """执行一次心跳。

    流程：
    1. 检查活跃时段
    2. 读取 HEARTBEAT.md
    3. 通过 ``agent(Msg(...))`` 让 agent 处理

    Args:
        agent: ``ReActAgent`` 实例（由 ``create_user_agent`` 创建）
        agent_id: Agent ID，用于加载配置
        workspace_dir: 工作区目录（读取 HEARTBEAT.md）
        heartbeat_cfg: 心跳配置（可选，不传则从 config 加载）
    """
    # 从配置加载心跳设置
    if heartbeat_cfg is None:
        from src.agents.config import load_agent_config
        ac = load_agent_config(agent_id or "default")
        heartbeat_cfg = getattr(ac, "heartbeat", HeartbeatConfig())

    if not _in_active_hours(getattr(heartbeat_cfg, "active_hours", None)):
        logger.debug("heartbeat skipped: outside active hours")
        return

    # 确定 HEARTBEAT.md 路径
    if workspace_dir:
        hb_path = Path(workspace_dir) / HEARTBEAT_FILENAME
    elif agent_id:
        from src.agents.harness.workspace.user_workspace import get_user_workspace
        hb_path = get_user_workspace(int(agent_id)) / HEARTBEAT_FILENAME
    else:
        logger.warning("heartbeat skipped: no workspace_dir or agent_id")
        return

    if not hb_path.is_file():
        logger.debug("heartbeat skipped: no file at %s", hb_path)
        return

    query_text = hb_path.read_text(encoding="utf-8").strip()
    if not query_text:
        logger.debug("heartbeat skipped: empty HEARTBEAT.md")
        return

    # 构建 Msg 并调用 agent
    msg = Msg(name="user", content=query_text, role="user")

    logger.info(
        "heartbeat executing for agent %s: %d chars",
        agent_id, len(query_text),
    )

    hb_cfg = heartbeat_cfg or HeartbeatConfig()
    target = (hb_cfg.target or "").strip().lower()
    if target == "last":
        logger.info(
            "heartbeat target=last requested for agent %s, "
            "falling back to silent execution",
            agent_id,
        )

    try:
        # 通过 stream_printing_messages 流式消费 agent 输出
        async for _msg, _last, *_ in stream_printing_messages(
            agents=[agent],
            coroutine_task=agent(msg),
        ):
            # 静默模式：不主动推送结果到客户端
            pass
        logger.info("heartbeat completed for agent %s", agent_id)
    except asyncio.CancelledError:
        logger.info("heartbeat cancelled for agent %s", agent_id)
        raise
    except Exception:
        logger.exception("heartbeat failed for agent %s", agent_id)
