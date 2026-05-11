"""AgentScope Runtime 沙箱工具管理器。

使用 AgentScope Runtime SandboxService 为 Agent 提供安全的代码执行和 shell 环境。
通过 sandbox_tool_adapter 将沙箱方法注册到 AgentScope Toolkit。

官方文档：https://runtime.agentscope.io/zh/sandbox/sandbox_service.html
"""
from __future__ import annotations

import logging
from typing import Any

from agentscope.tool import Toolkit
from agentscope_runtime.engine.services.sandbox import SandboxService
from agentscope_runtime.adapters.agentscope.tool import sandbox_tool_adapter

logger = logging.getLogger(__name__)


class SandboxToolManager:
    """管理沙箱服务的创建、连接和工具注册。

    生命周期：
        manager = SandboxToolManager()
        await manager.start()
        manager.register_sandbox_tools(toolkit, session_id, user_id)
        # ... Agent 使用工具 ...
        await manager.release(session_id, user_id)
        await manager.stop()

    特性：
    - 使用 BaseSandbox（支持 run_ipython_cell 和 run_shell_command）
    - 嵌入式模式（Docker），不依赖远程沙箱服务
    - 按 session_id + user_id 复用沙箱实例
    - 通过 sandbox_tool_adapter 自动转换返回值为 ToolResponse
    """

    def __init__(self, base_url: str | None = None, bearer_token: str | None = None):
        """
        Args:
            base_url: 远程沙箱服务地址。None 表示使用本地 Docker 嵌入式模式。
            bearer_token: 远程沙箱服务的认证令牌。
        """
        self._service: SandboxService | None = None
        self._base_url = base_url
        self._bearer_token = bearer_token
        self._started = False

    async def start(self) -> None:
        """启动沙箱服务。"""
        if self._started:
            return
        self._service = SandboxService(
            base_url=self._base_url,
            bearer_token=self._bearer_token,
        )
        await self._service.start()
        self._started = True
        logger.info("沙箱服务已启动 (base_url=%s)", self._base_url or "本地嵌入式")

    async def stop(self) -> None:
        """停止沙箱服务，释放所有资源。"""
        if self._service is not None and self._started:
            await self._service.stop()
            self._started = False
            logger.info("沙箱服务已停止")

    async def connect(
        self,
        session_id: str,
        user_id: str | int,
    ) -> Any:
        """连接或创建沙箱。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID

        Returns:
            BaseSandbox 实例（支持 run_ipython_cell / run_shell_command）
        """
        if not self._started:
            raise RuntimeError("沙箱服务未启动，请先调用 start()")

        sandboxes = self._service.connect(
            session_id=session_id,
            user_id=str(user_id),
            sandbox_types=["base"],
        )
        return sandboxes[0]

    async def release(self, session_id: str, user_id: str | int) -> None:
        """释放指定会话的沙箱资源。"""
        if self._service is not None and self._started:
            self._service.release(session_id=session_id, user_id=str(user_id))
            logger.info("已释放沙箱 session=%s user=%s", session_id, user_id)

    def register_tools(
        self,
        toolkit: Toolkit,
        sandbox: Any,
    ) -> None:
        """将沙箱工具注册到 AgentScope Toolkit。

        注册的工具：
        - run_ipython_cell: 在沙箱中执行 Python 代码
        - run_shell_command: 在沙箱中执行 shell 命令

        Args:
            toolkit: AgentScope Toolkit 实例
            sandbox: 沙箱连接实例（来自 self.connect()）
        """
        tools_to_register = [
            sandbox.run_ipython_cell,
            sandbox.run_shell_command,
        ]

        for tool in tools_to_register:
            adapted = sandbox_tool_adapter(tool)
            toolkit.register_tool_function(adapted)
            logger.debug("已注册沙箱工具: %s", tool.__name__)
