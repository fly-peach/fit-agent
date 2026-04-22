"""FitAgent Solution 适配器 — 通过 fixtures 隔离 DB，包装为 AgentScope Solution。"""
import asyncio
from typing import Callable

from agentscope.evaluate import SolutionOutput

from app.agent.service.agent_service import AgentService
from app.agent.schemas.agent import AgentChatRequest, ChatMessage
from app.harness.fixtures import isolated_db_session, get_or_create_test_user


class FitAgentSolution:
    """FitAgent 适配器 - 通过 fixtures 隔离 DB"""

    def __init__(self):
        self.agent = None

    async def solve(self, task_input: str, context: list[str] = None) -> SolutionOutput:
        """执行单个任务，返回标准化输出"""
        with isolated_db_session() as db:
            service = AgentService(db)
            user = get_or_create_test_user(db)

            messages = []
            if context:
                for i, msg in enumerate(context):
                    role = "user" if i % 2 == 0 else "assistant"
                    messages.append(ChatMessage(role=role, content=msg))
            messages.append(ChatMessage(role="user", content=task_input))

            request = AgentChatRequest(messages=messages, thinking=True)
            result = await asyncio.to_thread(
                service.chat,
                current_user=user,
                payload=request,
            )

            trajectory = self._extract_trajectory(result)

            return SolutionOutput(
                success=True,
                output=result.response,
                trajectory=trajectory,
                metadata={
                    "task_input": task_input,
                    "session_id": result.session_id,
                    "pending_actions": [a.model_dump() for a in result.pending_actions],
                    "memory_hits": result.memory_hits,
                    "was_blocked": False,
                },
            )

    def _extract_trajectory(self, result) -> list[dict]:
        """从结果中提取工具调用轨迹"""
        trajectory = []
        if hasattr(result, "tool_events") and result.tool_events:
            for event in result.tool_events:
                trajectory.append({
                    "tool_name": event.tool_name,
                    "phase": event.phase,
                    "input": event.payload_preview.get("input") if event.payload_preview else None,
                    "output": event.payload_preview.get("output") if event.payload_preview else None,
                })
        if hasattr(result, "pending_actions") and result.pending_actions:
            for action in result.pending_actions:
                trajectory.append({
                    "tool_name": action.tool_name,
                    "phase": "pending",
                    "input": action.payload,
                })
        return trajectory


async def fit_agent_solution(task, pre_hook: Callable = None) -> SolutionOutput:
    """标准 Solution 函数，供 Evaluator 调用"""
    if pre_hook:
        pre_hook()
    solution = FitAgentSolution()
    context = task.metadata.get("context") if task.metadata else None
    return await solution.solve(task_input=task.input, context=context)
