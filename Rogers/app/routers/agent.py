import logging
import base64
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
from src.fitme.utils.database import get_user_db
from src.fitme.models import UserImage

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


@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest | None = None,
    **_kwargs,
):
    """处理用户查询。"""
    assert request is not None, "request is required"
    session_id = request.session_id or "default"

    # 通过 ContextVar 获取 middleware 设置的 token
    token = _auth_token.get() or ""
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        yield Msg(name="Rogers", content="请先登录后再使用助手。", role="assistant"), True
        return

    # 每次创建全新的 agent 实例，确保用户间完全独立
    agent = create_user_agent(user_id)
    agent.set_console_output_enabled(False)
    memory_manager = getattr(agent, "_memory_manager", None)

    async with agent_context(user_id):
        try:
            if memory_manager is not None:
                await memory_manager.start()

            await agent_app.state.session.load_session_state(
                session_id=session_id,
                user_id=str(user_id),
                agent=agent,
            )

            # 将消息中的本地图片 URL 转换为 base64，让视觉模型能看到图片
            with harness_get_db() as db:
                msgs = _resolve_images_to_base64(msgs, db)

            async for msg, last, *_ in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(msgs),
            ):
                yield msg, last

            await agent_app.state.session.save_session_state(
                session_id=session_id,
                user_id=str(user_id),
                agent=agent,
            )
        finally:
            if memory_manager is not None:
                await memory_manager.close()


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
    model_name = "qwen3.5-flash"

    if user_config_path.exists():
        with open(user_config_path, encoding="utf-8") as f:
            user_config = json.load(f)
        model_config = user_config.get("model", {})
        if isinstance(model_config, dict):
            user_api_key = model_config.get("api_key", "")
            model_name = model_config.get("model_name", "qwen3.5-flash")

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

    # 只有在有模型配置更新时才写入
    if body.api_key is not None or body.model_name is not None:
        with open(user_config_path, "w", encoding="utf-8") as f:
            json.dump(user_config, f, indent=2, ensure_ascii=False)

    return {"status": "ok"}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    authorization: str | None = Header(default=None),
):
    """删除指定 session 文件。"""
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', session_id):
        raise HTTPException(status_code=400, detail="session_id 仅支持字母、数字、下划线、短横线")
    user_id = _get_user_id_from_auth(authorization)

    user_dir = get_user_workspace(user_id)
    session_file = user_dir / "sessions" / f"{session_id}.json"

    if session_file.exists():
        session_file.unlink()
        return {"status": "ok"}

    raise HTTPException(status_code=404, detail="Session not found")


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
