"""HeartbeatManager — 心跳定时任务调度器。

基于 APScheduler 实现，管理 heartbeat 定时任务的启动、停止、动态重调度。
参考 CoPaw 的 ``CronManager`` 设计。

用法：
    manager = HeartbeatManager(agent=my_agent, agent_id="default")
    await manager.start()   # 启动调度
    await manager.stop()    # 停止调度
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.agents.config import (
    HeartbeatConfig,
)

from .heartbeat import (
    is_cron_expression,
    parse_heartbeat_every,
    run_heartbeat_once,
)

HEARTBEAT_JOB_ID = "_heartbeat"
logger = logging.getLogger(__name__)


class HeartbeatManager:
    """管理 agent 的心跳定时任务。"""

    def __init__(
        self,
        agent: Any,
        agent_id: Optional[str] = None,
        workspace_dir: Optional[Path] = None,
        timezone: str = "Asia/Shanghai",
    ):
        """初始化心跳管理器。

        Args:
            agent: ``ReActAgent`` 实例
            agent_id: Agent ID
            workspace_dir: 工作区目录
            timezone: 调度时区
        """
        self._agent = agent
        self._agent_id = agent_id or "default"
        self._workspace_dir = workspace_dir
        self._scheduler = AsyncIOScheduler(timezone=timezone)
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self, hb_config: Optional[HeartbeatConfig] = None) -> None:
        """启动心跳调度器。

        Args:
            hb_config: 心跳配置，不传则从 config 加载
        """
        async with self._lock:
            if self._started:
                return

            if hb_config is None:
                hb_config = self._load_config()

            if getattr(hb_config, "enabled", False):
                trigger = self._build_trigger(hb_config.every)
                self._scheduler.add_job(
                    self._callback,
                    trigger=trigger,
                    id=HEARTBEAT_JOB_ID,
                    replace_existing=True,
                )
                logger.info(
                    "Heartbeat job scheduled for agent %s: every=%s",
                    self._agent_id,
                    hb_config.every,
                )

            self._scheduler.start()
            self._started = True
            logger.info("HeartbeatManager started for agent %s", self._agent_id)

    async def stop(self) -> None:
        """停止心跳调度器。"""
        async with self._lock:
            if not self._started:
                return
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("HeartbeatManager stopped for agent %s", self._agent_id)

    def is_running(self) -> bool:
        """调度器是否正在运行。"""
        return self._started

    def get_next_run_time(self):
        """获取下次心跳执行时间。"""
        job = self._scheduler.get_job(HEARTBEAT_JOB_ID)
        return job.next_run_time if job else None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_config(self) -> HeartbeatConfig:
        """从配置加载心跳设置。"""
        from src.agents.config import load_agent_config
        try:
            ac = load_agent_config(self._agent_id)
            return getattr(ac, "heartbeat", HeartbeatConfig())
        except Exception:
            return HeartbeatConfig()

    def _build_trigger(self, every: str):
        """根据 every 字符串构建 APScheduler trigger。

        支持：
        - interval 字符串：'30m', '1h', '2h30m', '90s'
        - cron 表达式：'0 */6 * * *'
        """
        if is_cron_expression(every):
            return CronTrigger.from_crontab(every)
        seconds = parse_heartbeat_every(every)
        return IntervalTrigger(seconds=seconds)

    async def _callback(self) -> None:
        """心跳回调：执行一次 heartbeat。"""
        try:
            await run_heartbeat_once(
                agent=self._agent,
                agent_id=self._agent_id,
                workspace_dir=self._workspace_dir,
            )
        except asyncio.CancelledError:
            logger.info("heartbeat cancelled for agent %s", self._agent_id)
            raise
        except Exception:
            logger.exception(
                "heartbeat run failed for agent %s", self._agent_id,
            )
