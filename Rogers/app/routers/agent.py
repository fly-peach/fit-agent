import json
import logging
import base64
import uuid
import datetime
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages
from src.agents.agent import create_user_agent
from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from fastapi import APIRouter, HTTPException, Header, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.agents.harness.context import agent_context, NotAuthenticatedError, get_user_id_from_token
from src.agents.harness.workspace.user_workspace import get_user_workspace, ensure_user_workspace
from src.agents.harness.tools.basic.read_data import get_db as harness_get_db
from src.fitme.utils.database import get_user_db, UserSessionLocal, async_agent_memory_engine
from src.agents.harness.memory.fitagent_memory import FitAgentSQLMemory
from src.fitme.models import UserImage
from src.agents.harness.chats.crud import (
    get_session as get_session_crud,
    create_session as create_session_crud,
)

logger = logging.getLogger("fitagent")

# ContextVar to carry the JWT token from middleware to query_func
_auth_token: ContextVar[str | None] = ContextVar("auth_token", default=None)

# 创建 AgentApp
agent_app = AgentApp(
    app_name="MyAssistant",
    app_description="A helpful assistant agent",
)


def _get_user_id_from_auth(authorization: str | None) -> int:
    """从 Authorization header 提取并验证用户 ID。"""
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        return get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

# ---------------------------------------------------------------------------
# Image URL → base64 conversion for vision models
# ---------------------------------------------------------------------------

def _resolve_images_to_base64(msgs: Any, db: Session) -> Any:
    """将消息中相对路径的图片 URL（如 /api/agent/images/123）替换为 base64。

    视觉模型无法访问本地 URL，需要将图片数据内嵌到消息中。
    """
    if isinstance(msgs, Msg):
        _convert_msg_content(msgs, db)
        return msgs

    if isinstance(msgs, list):
        for msg in msgs:
            if isinstance(msg, Msg):
                _convert_msg_content(msg, db)
        return msgs

    return msgs


def _convert_msg_content(msg: Msg, db: Session) -> None:
    """转换单条消息内容中的图片 URL 为 base64。"""
    content = getattr(msg, "content", None)
    if not content or not isinstance(content, list):
        return

    for i, block in enumerate(content):
        if not isinstance(block, dict):
            continue
        if block.get("type") != "image":
            continue
        source = block.get("source", {})
        if source.get("type") != "url":
            continue
        url = source.get("url", "")
        if not url or not url.startswith("/"):
            continue  # 已经是完整 URL 或无效

        # 从数据库加载图片
        image_id = _extract_image_id(url)
        if image_id is None:
            continue
        image = db.query(UserImage).filter(UserImage.image_id == image_id).first()
        if not image:
            continue

        # 替换为 base64
        content[i] = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": image.content_type or "image/jpeg",
                "data": base64.b64encode(image.data).decode(),
            },
        }


def _extract_image_id(url: str) -> int | None:
    """从 /api/agent/images/123 提取 image_id。"""
    prefix = "/api/agent/images/"
    if url.startswith(prefix):
        try:
            return int(url[len(prefix):].rstrip("/"))
        except (ValueError, IndexError):
            return None
    return None


def _msg_content_to_ui_text(msg: Msg) -> str:
    """将 Msg.content 提取为纯文本（用于前端展示）。"""
    content = msg.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "image":
                    texts.append("[图片]")
        return "\n".join(texts)
    return str(content) if content else ""


def _make_ui_message(msg: Msg, role: str, msg_status: str = "finished") -> str:
    """将 Msg 转换为 IAgentScopeRuntimeWebUIMessage 格式的 JSON 字符串。"""
    text = _msg_content_to_ui_text(msg)
    ui_msg = {
        "id": str(uuid.uuid4()),
        "role": role,
        "cards": [{"code": "markdown", "data": text}],
        "msgStatus": msg_status,
    }
    return json.dumps(ui_msg, ensure_ascii=False)


def _fmt_api_error(brief: str, detail: str) -> str:
    """将 API 错误格式化为用户友好的 Markdown 消息。

    简要放在外层，详细报错放在 <details> 折叠块中。
    """
    return (
        f"❌ {brief}\n\n"
        f"<details>\n"
        f"<summary>查看详细错误</summary>\n\n"
        f"```\n{detail}\n```\n"
        f"</details>"
    )


@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest | None = None,
    **_kwargs,
):
    """处理用户查询 — 使用 AsyncSQLAlchemyMemory 持久化对话历史。

    相比旧版（JSONSession + 手动 add_message）的改进：
    - 消息由 ``AsyncSQLAlchemyMemory`` 自动持久化到 ``agent_memory.db``
    - 无需手动 ``add_message()`` 和 ``_make_ui_message()``
    - 无需 ``load_session_state()`` / ``save_session_state()``
    - Msg 对象直存直读，无需格式转换
    """
    assert request is not None, "request is required"
    session_id = request.session_id or "default"

    # 通过 ContextVar 获取 middleware 设置的 token
    token = _auth_token.get() or ""
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        yield Msg(name="Rogers", content="请先登录后再使用助手。", role="assistant"), True
        return

    # 只校验 session 是否存在，不再自动创建（由前端 POST /sessions 负责创建）
    # 若 session 不存在则提示用户先创建对话
    db = UserSessionLocal()
    try:
        existing = get_session_crud(db, user_id, session_id)
        if existing is None:
            yield Msg(
                name="Rogers",
                content="❌ 会话不存在，请先点击「新建对话」创建会话后再发送消息。",
                role="assistant",
            ), True
            return
    finally:
        db.close()

    # 创建 FitAgentSQLMemory — 扩展自 AsyncSQLAlchemyMemory
    # 使用独立数据库 agent_memory.db 避免与主库 users 表冲突
    db_memory = FitAgentSQLMemory(
        engine_or_session=async_agent_memory_engine,
        user_id=str(user_id),
        session_id=session_id,
    )

    # 每次创建全新的 agent 实例，传入 DB 记忆后端
    try:
        agent = create_user_agent(user_id, db_memory=db_memory)
    except ValueError as e:
        msg = str(e)
        if "API Key" in msg:
            brief = "请先在「Agent 配置」页面设置 API Key"
        else:
            brief = "Agent 初始化失败"
        await db_memory.close()
        yield Msg(name="Rogers", content=_fmt_api_error(brief, msg), role="assistant"), True
        return

    agent.set_console_output_enabled(False)
    memory_manager = getattr(agent, "_memory_manager", None)

    async with agent_context(user_id):
        try:
            if memory_manager is not None:
                await memory_manager.start()

            # 将消息中的本地图片 URL 转换为 base64，让视觉模型能看到图片
            with harness_get_db() as db:
                msgs = _resolve_images_to_base64(msgs, db)

            async for msg, last, *_ in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(msgs),
            ):
                yield msg, last

        finally:
            if memory_manager is not None:
                await memory_manager.close()
            await db_memory.close()


router = APIRouter(prefix="/api/agent", tags=["agent"])


# ---------------------------------------------------------------------------
# Per-user agent configuration management
# ---------------------------------------------------------------------------

# 使用统一配置
from src.fitme.core.config import settings
from src.agents.harness.templates.templates import get_template_path, get_soul_template_path

# 默认配置路径
DEFAULT_AGENT_JSON = settings.AGENT_DB_DIR / "agent.json"


def _get_default_config() -> dict:
    """获取默认配置（不含敏感信息）。"""
    import json
    if DEFAULT_AGENT_JSON.exists():
        with open(DEFAULT_AGENT_JSON, encoding="utf-8") as f:
            config = json.load(f)
        # 清除配置文件中的 API Key，仅从环境变量读取
        if "models" in config:
            for model_key in config["models"]:
                if "api_key" in config["models"][model_key]:
                    config["models"][model_key]["api_key"] = ""
        return config
    return {}


def _mask_api_key(api_key: str) -> str:
    """遮蔽 API Key，只显示前8位和后4位。"""
    if not api_key or len(api_key) < 12:
        return api_key
    return api_key[:8] + "****" + api_key[-4:]


class AgentConfigUpdate(BaseModel):
    agents_md: str | None = None
    soul_md: str | None = None
    api_key: str | None = None
    model_name: str | None = None


class AgentConfigResponse(BaseModel):
    agents_md: str
    soul_md: str
    api_key_masked: str
    model_name: str
    is_custom_api_key: bool  # 是否使用自定义 API Key


class DefaultConfigResponse(BaseModel):
    agents_md: str
    soul_md: str
    model_name: str


class AgentStatusResponse(BaseModel):
    """AI 助手的配置状态。"""
    ready: bool
    config_ok: bool
    api_key_configured: bool
    api_key_masked: str = ""
    model: str = ""
    model_configured: bool = False
    message: str = ""


@router.get("/config/status", response_model=AgentStatusResponse)
async def check_agent_status(
    authorization: str | None = Header(default=None),
):
    """检测 AI 助手的配置状态。

    供前端在发送消息前调用，检查 API Key 和模型是否已配置。
    未配置时返回 friendly message 供前端展示。
    """
    import json
    try:
        user_id = _get_user_id_from_auth(authorization)
    except HTTPException:
        return AgentStatusResponse(
            ready=False, config_ok=False, api_key_configured=False,
            message="请先登录",
        )

    user_dir = ensure_user_workspace(user_id)
    user_config_path = user_dir / "agent.json"
    api_key = ""
    model_name = ""

    if user_config_path.exists():
        try:
            user_config = json.loads(user_config_path.read_text(encoding="utf-8"))
            m = user_config.get("model", {})
            if isinstance(m, dict):
                api_key = (m.get("api_key") or "").strip()
                model_name = (m.get("model_name") or "").strip()
        except Exception:
            pass

    if not api_key:
        return AgentStatusResponse(
            ready=False, config_ok=False, api_key_configured=False,
            api_key_masked="", model=model_name, model_configured=bool(model_name),
            message="请先在「Agent 配置」页面设置 API Key",
        )
    if not model_name:
        return AgentStatusResponse(
            ready=False, config_ok=False, api_key_configured=True,
            api_key_masked=_mask_api_key(api_key), model="", model_configured=False,
            message="请先在「Agent 配置」页面选择模型",
        )
    return AgentStatusResponse(
            ready=True, config_ok=True, api_key_configured=True,
            api_key_masked=_mask_api_key(api_key), model=model_name, model_configured=True,
            message="AI 助手准备就绪",
        )


@router.get("/config", response_model=AgentConfigResponse)
async def get_agent_config(
    authorization: str | None = Header(default=None),
):
    """获取当前用户的 agent 配置。未配置时返回默认值。"""
    import json
    user_id = _get_user_id_from_auth(authorization)

    user_dir = ensure_user_workspace(user_id)
    agents_md = (user_dir / "agents.md").read_text(encoding="utf-8") if (user_dir / "agents.md").exists() else ""
    soul_md = (user_dir / "soul.md").read_text(encoding="utf-8") if (user_dir / "soul.md").exists() else ""

    # 加载用户级 agent.json
    user_config_path = user_dir / "agent.json"
    user_api_key = ""
    model_name = "qwen-turbo"

    if user_config_path.exists():
        with open(user_config_path, encoding="utf-8") as f:
            user_config = json.load(f)
        model_config = user_config.get("model", {})
        if isinstance(model_config, dict):
            user_api_key = model_config.get("api_key", "")
            model_name = model_config.get("model_name", "qwen-turbo")

    # API Key 只从用户配置读取，不再从环境变量读取
    is_custom_api_key = bool(user_api_key)

    return AgentConfigResponse(
        agents_md=agents_md,
        soul_md=soul_md,
        api_key_masked=_mask_api_key(user_api_key),
        model_name=model_name,
        is_custom_api_key=is_custom_api_key,
    )


@router.get("/defaults", response_model=DefaultConfigResponse)
async def get_default_config():
    """获取默认的 agent 配置。"""
    default_config = _get_default_config()

    # 从 agents 配置中获取默认 sys_prompt
    agents_md = ""
    soul_md = ""
    model_name = "qwen-turbo"

    if "agents" in default_config and "default" in default_config["agents"]:
        agent_cfg = default_config["agents"]["default"]
        agents_md = agent_cfg.get("sys_prompt", "")

    if "models" in default_config and "primary" in default_config["models"]:
        model_cfg = default_config["models"]["primary"]
        model_name = model_cfg.get("model_name", "qwen-turbo")

    # 从模板文件读取默认的 soul.md
    soul_template = get_soul_template_path()
    if soul_template.exists():
        soul_md = soul_template.read_text(encoding="utf-8")

    return DefaultConfigResponse(
        agents_md=agents_md,
        soul_md=soul_md,
        model_name=model_name,
    )


@router.put("/config")
async def update_agent_config(
    body: AgentConfigUpdate,
    authorization: str | None = Header(default=None),
):
    """更新当前用户的 agent 配置。"""
    import json
    user_id = _get_user_id_from_auth(authorization)

    user_dir = ensure_user_workspace(user_id)

    if body.agents_md is not None:
        (user_dir / "agents.md").write_text(body.agents_md, encoding="utf-8")
    if body.soul_md is not None:
        (user_dir / "soul.md").write_text(body.soul_md, encoding="utf-8")

    # 更新用户级 agent.json（模型配置）
    user_config_path = user_dir / "agent.json"
    user_config = {}
    if user_config_path.exists():
        with open(user_config_path, encoding="utf-8") as f:
            user_config = json.load(f)

    # 确保 model 字段存在
    if "model" not in user_config or not isinstance(user_config.get("model"), dict):
        user_config["model"] = {}

    # 移除 base_url（不需要自定义，总是使用 DashScope 默认值）
    if "base_url" in user_config["model"]:
        del user_config["model"]["base_url"]

    # 只有在提供了新的 api_key 且不是占位符时才更新
    # 空字符串表示清除自定义 api_key
    if body.api_key is not None:
        if body.api_key.strip() == "" or body.api_key.startswith("sk-****"):
            # 清除自定义 api_key
            if "api_key" in user_config["model"]:
                del user_config["model"]["api_key"]
        else:
            # 设置新的自定义 api_key
            user_config["model"]["api_key"] = body.api_key

    if body.model_name is not None:
        user_config["model"]["model_name"] = body.model_name

    # 写入配置（总是写入以确保清理了 base_url）
    with open(user_config_path, "w", encoding="utf-8") as f:
        json.dump(user_config, f, indent=2, ensure_ascii=False)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Session management — included from agents.harness.chats.router
# ---------------------------------------------------------------------------

from src.agents.harness.chats.router import router as chat_router
router.include_router(chat_router)

# ---------------------------------------------------------------------------
# Image upload / retrieval / deletion
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_image(
    file: UploadFile,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """上传图片，存入数据库，返回 URL。"""
    user_id = _get_user_id_from_auth(authorization)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过 10MB")

    image = UserImage(
        user_id=user_id,
        file_name=file.filename or "image",
        content_type=file.content_type,
        file_size=len(data),
        data=data,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return {"url": f"/api/agent/images/{image.image_id}"}


@router.get("/images/{image_id}")
async def get_image(
    image_id: int,
    db: Session = Depends(get_user_db),
):
    """从数据库读取图片并返回。"""
    image = db.query(UserImage).filter(UserImage.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    return Response(
        content=image.data,
        media_type=image.content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """删除图片。"""
    user_id = _get_user_id_from_auth(authorization)
    image = db.query(UserImage).filter(
        UserImage.image_id == image_id,
        UserImage.user_id == user_id,
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    db.delete(image)
    db.commit()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------

class SessionUpdateRequest(BaseModel):
    name: str | None = None
    pinned: bool | None = None


class SessionResponse(BaseModel):
    id: str
    name: str
    updated_at: str | None = None


@router.get("/sessions")
async def list_sessions(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """获取用户的所有会话。"""
    user_id = _get_user_id_from_auth(authorization)
    from src.agents.harness.chats.crud import get_sessions
    
    sessions = get_sessions(db, user_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "pinned": bool(s.pinned),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """获取指定会话详情。"""
    user_id = _get_user_id_from_auth(authorization)
    from src.agents.harness.chats.crud import get_session
    
    session = get_session(db, user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "id": session.id,
        "name": session.name,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


@router.post("/sessions")
async def create_session_endpoint(
    request: SessionUpdateRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """创建新会话。"""
    user_id = _get_user_id_from_auth(authorization)
    from src.agents.harness.chats.crud import create_session, get_sessions
    
    session_id = str(uuid.uuid4())
    new_session = create_session(db, user_id, session_id, name=request.name)
    
    # 返回更新后的所有会话列表
    sessions = get_sessions(db, user_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "pinned": bool(s.pinned),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


@router.put("/sessions/{session_id}")
async def update_session_endpoint(
    session_id: str,
    request: SessionUpdateRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """更新会话名称或置顶状态。"""
    user_id = _get_user_id_from_auth(authorization)
    from src.agents.harness.chats.crud import update_session, get_sessions
    
    session = update_session(db, user_id, session_id, 
                             name=request.name, pinned=request.pinned)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 返回更新后的所有会话列表
    sessions = get_sessions(db, user_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "pinned": bool(s.pinned),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(
    session_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_user_db),
):
    """删除会话。"""
    user_id = _get_user_id_from_auth(authorization)
    from src.agents.harness.chats.crud import delete_session, get_sessions
    
    success = delete_session(db, user_id, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 返回删除后的所有会话列表
    sessions = get_sessions(db, user_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "pinned": bool(s.pinned),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]
