import re
import threading
from datetime import date, datetime, timezone
from typing import Any,Literal

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import ImageBlock, Msg, TextBlock
from agentscope.model import OpenAIChatModel
from agentscope.tool import ToolResponse, Toolkit
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import uuid4

from app.agent.guard.approval_service import ApprovalService
from app.agent.guard.tool_guard import ToolGuard
from app.agent.schemas.agent import (
    AgentApproveData,
    AgentApproveRequest,
    AgentChatData,
    AgentChatRequest,
    Attachment,
    ChatMessage,
    PendingActionItem,
    ToolEventItem,
)
from app.agent.runtime.react_agent import RogersReActRuntime
from app.agent.runtime.stream_parser import format_sse_event
from app.agent.runtime.stream_tracker import StreamTracker
from app.agent.memory import AutoContextConfig, AutoContextMemory, AutoContextStorage, CompressionDispatcher, TokenCounter
from app.agent.memory.memory_manager import MemoryManager
from app.agent.tools import (
    analyze_body_composition,
    analyze_food_image,
    analyze_scale_image,
    get_dashboard_summary,
    get_health_metrics,
    get_nutrition_history,
    get_user_profile,
    get_workout_history,
    summarize_text,
    update_daily_metrics,
    update_nutrition,
    update_workout_plan,
    view_image,
    view_image_base64,
)
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.agent_memory_repository import AgentMemoryRepository
from app.repositories.agent_compression_event_repository import AgentCompressionEventRepository
from app.repositories.agent_offload_repository import AgentOffloadRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.body_composition_repository import BodyCompositionRepository
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.repositories.daily_workout_plan_repository import DailyWorkoutPlanRepository
from app.repositories.user_repository import UserRepository
from app.services.dashboard_service import DashboardService

_STREAM_TRACKER = StreamTracker()


def _format_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def get_weather(city: str) -> ToolResponse:
    return ToolResponse(content=[TextBlock(type="text", text=f"{city} is sunny, 25°C.")])


def _stream_worker(*, user_id: int, payload_data: dict, session_id: str, run_id: str, protocol: str) -> None:
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user is None:
            _STREAM_TRACKER.append(
                run_id=run_id,
                event="error",
                sequence_number=1,
                data={"message": "用户不存在", "session_id": session_id, "run_id": run_id},
            )
            _STREAM_TRACKER.mark_done(run_id=run_id)
            return
        service = AgentService(db)
        service._produce_stream(
            current_user=user, payload_data=payload_data, session_id=session_id, run_id=run_id, protocol=protocol
        )
    finally:
        try:
            _STREAM_TRACKER.mark_done(run_id=run_id)
        finally:
            db.close()


class AgentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AgentRepository(db)
        self.daily_metrics_repo = DailyMetricsRepository(db)
        self.daily_workout_repo = DailyWorkoutPlanRepository(db)
        self.daily_nutrition_repo = DailyNutritionRepository(db)
        self.user_repo = UserRepository(db)
        self.body_composition_repo = BodyCompositionRepository(db)
        self.memory_repo = AgentMemoryRepository(db)
        self.offload_repo = AgentOffloadRepository(db)
        self.compression_event_repo = AgentCompressionEventRepository(db)
        self.memory_manager = MemoryManager(self.memory_repo)
        self.auto_context_memory = AutoContextMemory(
            config=AutoContextConfig(),
            storage=AutoContextStorage(
                message_repo=self.repo,
                offload_repo=self.offload_repo,
                compression_repo=self.compression_event_repo,
            ),
            dispatcher=CompressionDispatcher(),
            token_counter=TokenCounter(),
        )
        self.runtime = RogersReActRuntime()
        self.tool_guard = ToolGuard()
        self.approval_service = ApprovalService(
            repo=self.repo,
            daily_metrics_repo=self.daily_metrics_repo,
            daily_workout_repo=self.daily_workout_repo,
            daily_nutrition_repo=self.daily_nutrition_repo,
            memory_repo=self.memory_repo,
        )
        self.dashboard_service = DashboardService(db)

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "你是 Rogers 健身平台 AI 教练。优先根据用户数据与长期偏好给出简洁建议。"
            "涉及数据写入时，调用对应的 update 工具（如 update_daily_metrics、update_workout_plan、update_nutrition）。"
            "重要约束：所有写入工具都有 approved 参数，默认值为 false。你不得主动将 approved 设为 true，"
            "只需正常调用工具并传入数据即可，系统会自动创建待审批记录并等待用户确认。"
        )

    def _ensure_session(self, *, user_id: int, session_id: str | None) -> str:
        if session_id:
            existing = self.repo.get_session(session_id=session_id, user_id=user_id)
            if existing:
                return existing.id
        new_id = f"sess_{uuid4().hex[:16]}"
        self.repo.create_session(session_id=new_id, user_id=user_id)
        return new_id

    @staticmethod
    def _extract_history(messages: list[ChatMessage]) -> tuple[list[ChatMessage], str]:
        if not messages:
            return [], ""
        latest_user = ""
        for msg in reversed(messages):
            if msg.role == "user" and msg.content.strip():
                latest_user = msg.content.strip()
                break
        if not latest_user:
            return messages, ""
        history = messages[:-1] if messages[-1].role == "user" and messages[-1].content.strip() == latest_user else messages
        return history, latest_user

    def _compress_history(
        self,
        *,
        history: list[ChatMessage],
        session_id: str,
        user_id: int,
        run_id: str,
    ) -> list[ChatMessage]:
        compressed, _events = self.auto_context_memory.compress_messages(
            messages=history,
            session_id=session_id,
            user_id=user_id,
            run_id=run_id,
        )
        return compressed

    @staticmethod
    def _build_prompt(history: list[ChatMessage], user_text: str) -> str:
        if not history:
            return user_text
        recent = history[-10:]
        lines: list[str] = []
        for item in recent:
            role = "用户" if item.role == "user" else "助手"
            text = item.content.strip()
            if text:
                lines.append(f"{role}: {text}")
        context = "\n".join(lines).strip()
        if not context:
            return user_text
        return f"以下是对话历史，请结合上下文回答用户的最后问题。\n{context}\n\n用户最新问题：{user_text}"

    @staticmethod
    def _build_multimodal_msg(user_text: str, attachments: list[Attachment]) -> Msg:
        content: list[Any] = []
        if user_text.strip():
            content.append(TextBlock(type="text", text=user_text.strip()))
        for att in attachments:
            if att.type == "image" and att.base64:
                data_url = f"data:{att.mime_type or 'image/jpeg'};base64,{att.base64}"
                content.append(
                    ImageBlock(
                        type="image",
                        source={"type": "url", "url": data_url},
                    )
                )
        if not content:
            content.append(TextBlock(type="text", text="???????"))
        return Msg(name="user", content=content, role="user")

    def _build_agentscope_agent(self, *, thinking: bool, current_user: User, session_id: str) -> ReActAgent:
        model_kwargs: dict[str, Any] = {
            "model_name": settings.model,
            "api_key": settings.dashscope_coding_api_key,
        }
        # Qwen 模型的思考功能通过 extra_body 传递
        if thinking:
            model_kwargs["generate_kwargs"] = {"extra_body": {"enable_thinking": True}}
        if settings.dashscope_coding_url:
            model_kwargs["client_kwargs"] = {"base_url": settings.dashscope_coding_url}

        async def tool_get_user_profile() -> ToolResponse:
            return await get_user_profile(user_repo=self.user_repo, user_id=current_user.id)

        async def tool_get_health_metrics(days: int = 7) -> ToolResponse:
            return await get_health_metrics(repo=self.daily_metrics_repo, user_id=current_user.id, days=days)

        async def tool_get_workout_history(days: int = 7) -> ToolResponse:
            return await get_workout_history(repo=self.daily_workout_repo, user_id=current_user.id, days=days)

        async def tool_get_nutrition_history(days: int = 7) -> ToolResponse:
            return await get_nutrition_history(repo=self.daily_nutrition_repo, user_id=current_user.id, days=days)

        async def tool_get_dashboard_summary() -> ToolResponse:
            return await get_dashboard_summary(service=self.dashboard_service, user=current_user)

        async def tool_analyze_body_composition(height_cm: float = 175.0, actual_age: int = 30) -> ToolResponse:
            return await analyze_body_composition(
                body_repo=self.body_composition_repo,
                user_id=current_user.id,
                height_cm=height_cm,
                actual_age=actual_age,
            )

        def tool_update_daily_metrics(record_date: str, data: dict, approved: bool = False) -> ToolResponse:
            if approved:
                return ToolResponse(
                    content=[TextBlock(type="text", text="⚠️ 此参数应由系统设置，AI 不应主动设置 approved=true")],
                )
            action = self.repo.create_pending_action(
                action_id=f"act_{uuid4().hex[:12]}",
                session_id=session_id,
                user_id=current_user.id,
                tool_name="update_daily_metrics",
                summary=f"更新 {record_date} 的身体指标",
                payload={"record_date": record_date, "data": data},
            )
            return ToolResponse(
                content=[TextBlock(type="text", text=f"⏸️ 操作已挂起：等待审批（{action.summary}）")],
            )

        def tool_update_workout_plan(record_date: str, plan: dict, approved: bool = False) -> ToolResponse:
            if approved:
                return ToolResponse(
                    content=[TextBlock(type="text", text="⚠️ 此参数应由系统设置，AI 不应主动设置 approved=true")],
                )
            action = self.repo.create_pending_action(
                action_id=f"act_{uuid4().hex[:12]}",
                session_id=session_id,
                user_id=current_user.id,
                tool_name="update_workout_plan",
                summary=f"更新 {record_date} 的训练计划",
                payload={"record_date": record_date, "data": plan},
            )
            return ToolResponse(
                content=[TextBlock(type="text", text=f"⏸️ 操作已挂起：等待审批（{action.summary}）")],
            )

        def tool_update_nutrition(record_date: str, data: dict, approved: bool = False) -> ToolResponse:
            if approved:
                return ToolResponse(
                    content=[TextBlock(type="text", text="⚠️ 此参数应由系统设置，AI 不应主动设置 approved=true")],
                )
            action = self.repo.create_pending_action(
                action_id=f"act_{uuid4().hex[:12]}",
                session_id=session_id,
                user_id=current_user.id,
                tool_name="update_nutrition",
                summary=f"更新 {record_date} 的营养摄入",
                payload={"record_date": record_date, "data": data},
            )
            return ToolResponse(
                content=[TextBlock(type="text", text=f"⏸️ 操作已挂起：等待审批（{action.summary}）")],
            )

        tool_functions = {
            "get_weather": get_weather,
            "summarize_text": summarize_text,
            "get_user_profile": tool_get_user_profile,
            "get_health_metrics": tool_get_health_metrics,
            "get_workout_history": tool_get_workout_history,
            "get_nutrition_history": tool_get_nutrition_history,
            "get_dashboard_summary": tool_get_dashboard_summary,
            "analyze_body_composition": tool_analyze_body_composition,
            "view_image": view_image,
            "view_image_base64": view_image_base64,
            "analyze_food_image": analyze_food_image,
            "analyze_scale_image": analyze_scale_image,
            "update_daily_metrics": tool_update_daily_metrics,
            "update_workout_plan": tool_update_workout_plan,
            "update_nutrition": tool_update_nutrition,
        }

        toolkit = Toolkit()
        for tool_name, tool_func in tool_functions.items():
            toolkit.register_tool_function(tool_func)

        return ReActAgent(
            name="RogersChatAgent",
            sys_prompt=self._build_system_prompt(),
            model=OpenAIChatModel(**model_kwargs),
            formatter=OpenAIChatFormatter(promote_tool_result_images=True),
            toolkit=toolkit,
        )

    def _build_trend_reply(self, *, user: User) -> str:
        metrics = self.daily_metrics_repo.list_by_user(user_id=user.id, from_date=date.today() - __import__("datetime").timedelta(days=6), to_date=date.today(), skip=0, limit=7)
        if not metrics:
            return "最近7天还没有记录到身体数据。你可以先在\"每日数据\"里补录体重、体脂率和 BMI。"
        weights = [m.weight for m in metrics if m.weight is not None]
        fat_rates = [m.body_fat_rate for m in metrics if m.body_fat_rate is not None]
        parts: list[str] = []
        if len(weights) >= 2:
            delta_w = round(weights[-1] - weights[0], 2)
            trend = "下降" if delta_w < 0 else "上升" if delta_w > 0 else "持平"
            parts.append(f"体重近7天{trend}{abs(delta_w)}kg（起始 {weights[0]}kg -> 当前 {weights[-1]}kg）")
        if len(fat_rates) >= 2:
            delta_f = round(fat_rates[-1] - fat_rates[0], 2)
            trend = "下降" if delta_f < 0 else "上升" if delta_f > 0 else "持平"
            parts.append(f"体脂率近7天{trend}{abs(delta_f)}%（起始 {fat_rates[0]}% -> 当前 {fat_rates[-1]}%）")
        if not parts:
            return "目前已有记录，但有效趋势点还不足 2 个。建议连续记录 3-5 天后再看趋势。"
        suggestion = "建议：保持稳定作息，每周至少 3 次训练，并将蛋白质摄入分配到三餐。"
        return "；".join(parts) + "。 " + suggestion

    def _build_tool_event(
        self, *, tool_name: str, phase: Literal['started', 'completed', 'failed'], summary: str, payload_preview: dict | None = None
    ) -> ToolEventItem:
        return ToolEventItem(
            event_id=f"evt_{uuid4().hex[:12]}",
            tool_name=tool_name,
            phase=phase,
            summary=summary,
            payload_preview=payload_preview,
            created_at=datetime.now(timezone.utc),
        )

    def _llm_general_reply(self, *, user_message: str, memory_context: str) -> str | None:
        return self.runtime.invoke_general_reply(
            user_message=user_message,
            memory_context=memory_context,
            system_prompt=self._build_system_prompt(),
        )

    def chat(self, *, current_user: User, payload: AgentChatRequest) -> AgentChatData:
        session_id = self._ensure_session(user_id=current_user.id, session_id=payload.session_id)
        history, msg = self._extract_history(payload.messages)
        history = self._compress_history(
            history=history,
            session_id=session_id,
            user_id=current_user.id,
            run_id=f"sync_{uuid4().hex[:10]}",
        )
        msg = msg.strip()
        guard_result = self.tool_guard.inspect_user_message(msg)
        if guard_result.decision == "deny":
            self.repo.create_message(session_id=session_id, user_id=current_user.id, role="user", content=msg or "[空消息]")
            self.repo.create_message(
                session_id=session_id,
                user_id=current_user.id,
                role="assistant",
                content=f"检测到高风险请求：{guard_result.reason}。如需继续，请改为普通健康数据查询或审批写入。",
            )
            return AgentChatData(
                session_id=session_id,
                response=f"检测到高风险请求：{guard_result.reason}。如需继续，请改为普通健康数据查询或审批写入。",
                pending_actions=[],
                tool_events=[],
                memory_hits=[],
            )
        memory_saved = self.memory_manager.maybe_store_user_memory(user_id=current_user.id, message=msg)
        memory_hits = self.memory_manager.search(user_id=current_user.id, query=msg, top_k=settings.agent_memory_top_k)
        memory_context = self.memory_manager.build_context(
            user_id=current_user.id, query=msg, top_k=settings.agent_memory_top_k
        )

        self.repo.create_message(session_id=session_id, user_id=current_user.id, role="user", content=msg or "[空消息]")

        lower = msg.lower()
        pending_items: list[PendingActionItem] = []
        tool_events: list[ToolEventItem] = []

        if any(k in msg for k in ["趋势", "分析", "体重", "体脂"]):
            reply = self._build_trend_reply(user=current_user)
        elif any(k in lower for k in ["训练建议", "计划", "怎么练"]):
            reply = "本周建议：1) 力量训练 3 次（推/拉/腿）；2) 中等强度有氧 2 次，每次 30 分钟；3) 每天 8000 步以上。"
        else:
            llm_reply = self._llm_general_reply(user_message=msg, memory_context=memory_context)
            reply = llm_reply or "我可以帮你做三件事：趋势分析、训练建议、数据修改（需审批）。你可以说\"帮我分析最近7天体重趋势\"。"

        if memory_saved:
            reply += "\n\n我已记住你刚才提供的长期偏好/事实，后续建议会参考它。"

        self.repo.create_message(session_id=session_id, user_id=current_user.id, role="assistant", content=reply)
        return AgentChatData(
            session_id=session_id,
            response=reply,
            pending_actions=pending_items,
            tool_events=tool_events,
            memory_hits=memory_hits,
        )

    def list_pending(self, *, current_user: User) -> list[PendingActionItem]:
        rows = self.repo.list_pending_actions(user_id=current_user.id, limit=50)
        return [
            PendingActionItem(
                action_id=r.id,
                tool_name=r.tool_name,
                summary=r.summary,
                status=r.status,
                payload=r.payload,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def list_sessions(self, *, current_user: User) -> list[dict]:
        rows = self.repo.list_sessions(user_id=current_user.id, limit=100)
        return [{"session_id": r.id, "title": r.title, "updated_at": r.updated_at} for r in rows]

    def list_history(self, *, current_user: User, session_id: str, format: str = "plain") -> list[dict]:
        session = self.repo.get_session(session_id=session_id, user_id=current_user.id)
        if session is None:
            return []
        if format == "runtime":
            rows = self.repo.list_events(session_id=session_id, user_id=current_user.id, limit=500)
            return [r.payload for r in rows]
        rows = self.repo.list_messages(session_id=session_id, user_id=current_user.id, limit=200)
        return [
            {
                "role": r.role,
                "content": r.content,
                "reasoning": r.reasoning,
                "tool_uses": r.tool_uses,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    def delete_session(self, *, current_user: User, session_id: str) -> bool:
        return self.repo.delete_session(session_id=session_id, user_id=current_user.id)

    def _llm_general_reply_stream(self, *, user_message: str, memory_context: str):
        has_output = False
        for chunk in self.runtime.stream_general_reply(
            user_message=user_message,
            memory_context=memory_context,
            system_prompt=self._build_system_prompt(),
        ):
            has_output = True
            yield chunk
        if not has_output:
            yield "LLM调用发生异常，请稍后重试。"

    def chat_stream(
        self,
        *,
        current_user: User,
        payload: AgentChatRequest,
        reconnect: bool = False,
        run_id: str | None = None,
        last_seq: int = 0,
        protocol: str = "modern",
    ):
        session_id = self._ensure_session(user_id=current_user.id, session_id=payload.session_id)
        if reconnect:
            if not run_id:
                yield format_sse_event(
                    "error",
                    {"message": "reconnect=true 时必须提供 run_id", "session_id": session_id, "run_id": ""},
                )
                yield format_sse_event(
                    "done",
                    {"session_id": session_id, "run_id": "", "sequence_number": last_seq, "memory_hits": []},
                )
                return
            yield from self._yield_tracked(run_id=run_id, last_seq=last_seq)
            return

        next_run_id = _STREAM_TRACKER.create_run(session_id=session_id, user_id=current_user.id)
        payload_data = payload.model_dump()
        thread = threading.Thread(
            target=_stream_worker,
            kwargs={
                "user_id": current_user.id,
                "payload_data": payload_data,
                "session_id": session_id,
                "run_id": next_run_id,
                "protocol": protocol,
            },
            daemon=True,
        )
        thread.start()
        yield from self._yield_tracked(run_id=next_run_id, last_seq=last_seq)

    def _yield_tracked(self, *, run_id: str, last_seq: int):
        cursor = last_seq
        while True:
            batch = _STREAM_TRACKER.replay_from(run_id=run_id, last_seq=cursor)
            for item in batch:
                cursor = max(cursor, item.sequence_number)
                yield format_sse_event(item.event, item.data)
            if _STREAM_TRACKER.is_done(run_id=run_id):
                if not batch:
                    break
                continue
            if not batch:
                waited = _STREAM_TRACKER.wait_next(run_id=run_id, last_seq=cursor, timeout_seconds=15.0)
                for item in waited:
                    cursor = max(cursor, item.sequence_number)
                    yield format_sse_event(item.event, item.data)

    def _produce_stream(
        self, *, current_user: User, payload_data: dict, session_id: str, run_id: str, protocol: str
    ) -> None:
        seq = 0

        def emit(event: str, data: dict) -> None:
            nonlocal seq
            seq += 1
            data_with_meta = {
                **data,
                "run_id": run_id,
                "session_id": session_id,
                "sequence_number": seq,
                "created_at": _format_iso(datetime.now(timezone.utc)),
            }
            _STREAM_TRACKER.append(run_id=run_id, event=event, sequence_number=seq, data=data_with_meta)
            try:
                self.repo.create_event(
                    event_id=str(data_with_meta.get("id") or f"evt_{uuid4().hex[:12]}"),
                    session_id=session_id,
                    user_id=current_user.id,
                    run_id=run_id,
                    event_type=event,
                    sequence_number=seq,
                    payload=data_with_meta,
                )
            except Exception:
                pass

        payload = AgentChatRequest.model_validate(payload_data)
        history, msg = self._extract_history(payload.messages)
        history = self._compress_history(
            history=history,
            session_id=session_id,
            user_id=current_user.id,
            run_id=run_id,
        )
        msg = msg.strip()
        guard_result = self.tool_guard.inspect_user_message(msg)
        emit("message", {"type": "session", "session_id": session_id})
        if guard_result.decision == "deny":
            emit("message", {"type": "error", "message": f"检测到高风险请求：{guard_result.reason}。已阻止执行。"})
            emit("message", {"type": "done", "session_id": session_id, "memory_hits": []})
            return

        if payload.thinking:
            emit("message", {"type": "reasoning", "delta": "正在分析用户输入、历史记忆与可调用工具。\n"})

        memory_saved = self.memory_manager.maybe_store_user_memory(user_id=current_user.id, message=msg)
        if memory_saved and payload.thinking:
            emit("message", {"type": "reasoning", "delta": "发现可提取的长期记忆并已保存。\n"})

        memory_hits = self.memory_manager.search(user_id=current_user.id, query=msg, top_k=settings.agent_memory_top_k)
        memory_context = self.memory_manager.build_context(user_id=current_user.id, query=msg, top_k=settings.agent_memory_top_k)

        self.repo.create_message(session_id=session_id, user_id=current_user.id, role="user", content=msg or "[空消息]")

        lower = msg.lower()
        pending_items: list[PendingActionItem] = []
        tool_events: list[ToolEventItem] = []
        full_reply = ""
        full_reasoning_collected = ""  # 收集完整思考内容
        tool_uses_collected: list[dict] = []  # 收集工具调用记录

        prompt = self._build_prompt(history, msg)
        has_attachments = len(payload.attachments) > 0
        has_reasoning = False
        sent_tool_uses: set[str] = set()
        prev_reasoning = ""
        prev_text = ""

        try:
            agent = self._build_agentscope_agent(
                thinking=payload.thinking,
                current_user=current_user,
                session_id=session_id,
            )
            agent.set_msg_queue_enabled(True)
            import asyncio

            async def run_agent():
                if has_attachments:
                    user_msg = self._build_multimodal_msg(msg, payload.attachments)
                else:
                    user_msg = Msg("user", prompt, "user")
                return await agent(user_msg)

            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                task = loop.create_task(run_agent())
                while True:
                    if task.done() and (agent.msg_queue is None or agent.msg_queue.empty()):
                        break
                    if agent.msg_queue is None:
                        continue
                    try:
                        queue_item = loop.run_until_complete(asyncio.wait_for(agent.msg_queue.get(), timeout=0.2))
                    except asyncio.TimeoutError:
                        continue
                    msg_obj, _last, _speech = queue_item
                    blocks = msg_obj.get_content_blocks() or []
                    full_reasoning = "".join(
                        b.get("thinking", "")
                        for b in blocks
                        if isinstance(b.get("thinking"), str) and b.get("thinking")
                    )
                    if payload.thinking and full_reasoning:
                        delta = full_reasoning[len(prev_reasoning) :] if full_reasoning.startswith(prev_reasoning) else full_reasoning
                        prev_reasoning = full_reasoning
                        if delta:
                            has_reasoning = True
                            full_reasoning_collected += delta  # 收集思考内容
                            emit("message", {"type": "reasoning", "delta": delta})

                    full_text = "".join(
                        b.get("text", "") for b in blocks if isinstance(b.get("text"), str) and b.get("text")
                    )
                    if full_text:
                        delta = full_text[len(prev_text) :] if full_text.startswith(prev_text) else full_text
                        prev_text = full_text
                        if delta:
                            full_reply += delta
                            emit("message", {"type": "token", "delta": delta})

                    for block in msg_obj.get_content_blocks("tool_use") or []:
                        tool_name = block.get("name")
                        tool_input = block.get("input", {})
                        tool_output = block.get("output")
                        key = f"{tool_name}::{tool_input}"
                        if key in sent_tool_uses:
                            continue
                        sent_tool_uses.add(key)
                        tool_payload = {
                            "name": tool_name,
                            "input": tool_input,
                            "output": tool_output,
                        }
                        tool_uses_collected.append(tool_payload)  # 收集工具调用
                        # 将工具调用信息整合到 reasoning 中
                        if tool_output is not None:
                            tool_info = f"\n\n[工具调用] {tool_name}\n输入: {tool_input}\n输出: {tool_output}\n"
                        else:
                            tool_info = f"\n\n[工具调用] {tool_name}\n输入: {tool_input}\n"
                        full_reasoning_collected += tool_info
                        if payload.thinking:
                            emit("message", {"type": "reasoning", "delta": tool_info})

                        if str(tool_name) in {"update_daily_metrics", "update_workout_plan", "update_nutrition"}:
                            action_id = f"act_{uuid4().hex[:12]}"
                            tool_type_map = {
                                "update_daily_metrics": "身体指标",
                                "update_workout_plan": "训练计划",
                                "update_nutrition": "营养摄入",
                            }
                            action = self.repo.create_pending_action(
                                action_id=action_id,
                                session_id=session_id,
                                user_id=current_user.id,
                                tool_name=str(tool_name),
                                summary=f"更新 {tool_input.get('record_date', '未知日期')} 的 {tool_type_map.get(str(tool_name), '数据')}",
                                payload=tool_input,
                            )
                            pending = PendingActionItem(
                                action_id=action.id,
                                tool_name=action.tool_name,
                                summary=action.summary,
                                status=action.status,
                                payload=action.payload,
                                created_at=action.created_at,
                            )
                            pending_items.append(pending)
                            emit("message", {"type": "approval", "payload": pending.model_dump()})

                        tool_events.append(
                            self._build_tool_event(
                                tool_name=str(tool_name or "tool"),
                                phase="completed",
                                summary="工具调用完成",
                                payload_preview={"input": tool_input, "output": tool_output},
                            )
                        )

                reply = loop.run_until_complete(task)
                answer = (reply.get_text_content() or "").strip()
            finally:
                agent.set_msg_queue_enabled(False)
                loop.close()

            if payload.thinking and not has_reasoning:
                emit("message", {"type": "reasoning", "delta": "当前模型/参数未返回可展示的思考内容。\n"})
            if answer and not full_reply:
                full_reply = answer
                emit("message", {"type": "token", "delta": answer})
            if not answer and not full_reply:
                full_reply = "抱歉，这次没有生成有效回答，请重试。"
                emit("message", {"type": "token", "delta": full_reply})
        except Exception as exc:
            full_reply = f"请求失败：{exc}"
            emit("message", {"type": "error", "message": full_reply})

        if memory_saved:
            suffix = "\n\n我已记住你刚才提供的长期偏好/事实，后续建议会参考它。"
            full_reply += suffix
            for i in range(0, len(suffix), 24):
                emit("message", {"type": "token", "delta": suffix[i : i + 24]})

        self.repo.create_message(
            session_id=session_id,
            user_id=current_user.id,
            role="assistant",
            content=full_reply,
            reasoning=full_reasoning_collected if full_reasoning_collected else None,
            tool_uses=tool_uses_collected if tool_uses_collected else None,
        )
        final_data = AgentChatData(
            session_id=session_id,
            response=full_reply,
            pending_actions=pending_items,
            tool_events=tool_events,
            memory_hits=memory_hits,
        ).model_dump()
        emit("message", {"type": "done", **final_data})

    def approve(self, *, current_user: User, payload: AgentApproveRequest) -> AgentApproveData:
        return self.approval_service.approve(current_user=current_user, payload=payload)

    def compression_status(self, *, current_user: User, session_id: str) -> dict:
        history = self.repo.list_messages(session_id=session_id, user_id=current_user.id, limit=1000)
        as_messages = [ChatMessage(role=m.role if m.role in ("user", "assistant") else "assistant", content=m.content) for m in history]
        return self.auto_context_memory.status(
            session_id=session_id,
            user_id=current_user.id,
            current_messages=as_messages,
        )

    def compression_events(self, *, current_user: User, session_id: str, limit: int = 100) -> list[dict]:
        events = self.compression_event_repo.list_by_session(session_id=session_id, user_id=current_user.id, limit=limit)
        return [
            {
                "id": e.id,
                "run_id": e.run_id,
                "strategy_level": e.strategy_level,
                "strategy_name": e.strategy_name,
                "messages_before": e.messages_before,
                "messages_after": e.messages_after,
                "tokens_before": e.tokens_before,
                "tokens_after": e.tokens_after,
                "compression_ratio": e.compression_ratio,
                "affected_message_ids": e.affected_message_ids,
                "created_at": _format_iso(e.created_at),
            }
            for e in events
        ]

    def original_history(self, *, current_user: User, session_id: str) -> list[dict]:
        history = self.repo.list_messages(session_id=session_id, user_id=current_user.id, limit=1000)
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "is_compressed": bool(m.is_compressed),
                "compression_strategy": m.compression_strategy,
                "offload_id": m.offload_id,
                "compressed_summary": m.compressed_summary,
                "created_at": _format_iso(m.created_at),
            }
            for m in history
        ]

    def load_offload_content(self, *, current_user: User, offload_id: str) -> dict:
        item = self.offload_repo.get(offload_id=offload_id, user_id=current_user.id)
        if item is None:
            raise ValueError("offload 内容不存在")
        updated = self.offload_repo.mark_loaded(item)
        return {
            "id": updated.id,
            "session_id": updated.session_id,
            "message_id": updated.message_id,
            "content_type": updated.content_type,
            "content": updated.content,
            "compressed_summary": updated.compressed_summary,
            "load_count": updated.load_count,
            "created_at": _format_iso(updated.created_at),
            "loaded_at": _format_iso(updated.loaded_at) if updated.loaded_at else None,
        }