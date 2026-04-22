from __future__ import annotations

import asyncio
import asyncio
from datetime import date, datetime, timezone

from app.agent.schemas.agent import AgentApproveData, AgentApproveRequest
from app.models.user import User
from app.repositories.agent_memory_repository import AgentMemoryRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.repositories.daily_workout_plan_repository import DailyWorkoutPlanRepository
from app.agent.tools.write_tools import update_daily_metrics, update_nutrition, update_workout_plan
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


class ApprovalService:
    def __init__(
        self,
        *,
        repo: AgentRepository,
        daily_metrics_repo: DailyMetricsRepository,
        daily_workout_repo: DailyWorkoutPlanRepository,
        daily_nutrition_repo: DailyNutritionRepository,
        memory_repo: AgentMemoryRepository,
    ) -> None:
        self.repo = repo
        self.daily_metrics_repo = daily_metrics_repo
        self.daily_workout_repo = daily_workout_repo
        self.daily_nutrition_repo = daily_nutrition_repo
        self.memory_repo = memory_repo

    def approve(self, *, current_user: User, payload: AgentApproveRequest) -> AgentApproveData:
        action = self.repo.get_pending_action(action_id=payload.action_id, user_id=current_user.id)
        if action is None:
            return AgentApproveData(action_id=payload.action_id, status="not_found", result="待审批操作不存在")
        if action.status != "pending":
            return AgentApproveData(action_id=action.id, status=action.status, result="该操作已处理")

        if payload.decision == "reject":
            action.status = "rejected"
            action.result_message = "用户已拒绝该操作"
            action.executed_at = datetime.now(timezone.utc)
            self.repo.save_pending_action(action)
            return AgentApproveData(action_id=action.id, status=action.status, result=action.result_message)

        data = payload.edited_data if payload.decision == "edit" and payload.edited_data else action.payload
        record_date = data["record_date"]
        result = "未执行"
        if action.tool_name == "update_daily_metrics":
            resp = asyncio.run(
                update_daily_metrics(
                    repo=self.daily_metrics_repo,
                    user_id=current_user.id,
                    record_date=record_date,
                    data=data["data"],
                    approved=True,
                )
            )
            result = "\n".join([b.text for b in (resp.content or []) if isinstance(b, TextBlock) and getattr(b, "text", None)]) or "???"
        elif action.tool_name == "update_workout_plan":
            resp = asyncio.run(
                update_workout_plan(
                    repo=self.daily_workout_repo,
                    user_id=current_user.id,
                    record_date=record_date,
                    plan=data["data"],
                    approved=True,
                )
            )
            result = "\n".join([b.text for b in (resp.content or []) if isinstance(b, TextBlock) and getattr(b, "text", None)]) or "???"
        elif action.tool_name == "update_nutrition":
            resp = asyncio.run(
                update_nutrition(
                    repo=self.daily_nutrition_repo,
                    user_id=current_user.id,
                    record_date=record_date,
                    data=data["data"],
                    approved=True,
                )
            )
            result = "\n".join([b.text for b in (resp.content or []) if isinstance(b, TextBlock) and getattr(b, "text", None)]) or "???"

        action.status = "executed"
        action.result_message = result
        action.executed_at = datetime.now(timezone.utc)
        action.payload = data
        self.repo.save_pending_action(action)
        try:
            self.memory_repo.create(
                user_id=current_user.id,
                memory_type="fact",
                content=f"已执行操作：{result}",
                tags=["approval", action.tool_name],
                source="approval",
                source_ref=action.id,
                importance=4,
            )
        except Exception:
            pass
        return AgentApproveData(action_id=action.id, status=action.status, result=result)
