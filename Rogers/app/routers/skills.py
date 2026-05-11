"""Skill 管理 API 路由。

重构为使用轻量 SkillManager，委托官方 AgentScope Toolkit API 处理技能注册和 prompt 生成。
"""
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from fastapi.responses import FileResponse

from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from src.agents.harness.workspace.user_workspace import ensure_user_workspace
from src.agents.harness.skills.skill_manager import SkillManager
from src.agents.harness.templates.templates import get_skills_template_path

logger = logging.getLogger("fitagent")

router = APIRouter(prefix="/api/agent/skills", tags=["skills"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_skill_manager(authorization: str | None) -> SkillManager:
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")
    user_dir = ensure_user_workspace(user_id)
    template_skills_dir = get_skills_template_path()
    return SkillManager(user_dir, skills_dir=template_skills_dir)


# ---------------------------------------------------------------------------
# 技能 CRUD API
# ---------------------------------------------------------------------------

@router.get("")
async def list_skills(authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    return sm.list_skills()


@router.get("/{name}")
async def get_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    detail = sm.get_skill_detail(name)
    if detail is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return detail


@router.get("/{name}/files/{file_path:path}")
async def get_skill_file(
    name: str,
    file_path: str,
    authorization: str | None = Header(default=None),
):
    sm = _get_skill_manager(authorization)
    content = sm.read_skill_file(name, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill file not found")
    return {"content": content}


@router.put("/{name}/enable")
async def enable_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.enable_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "ok", "name": name, "enabled": True}


@router.put("/{name}/disable")
async def disable_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.disable_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "ok", "name": name, "enabled": False}


@router.put("/{name}")
async def update_skill(
    name: str,
    body: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    """更新技能配置（enabled / channels / priority / auto_update）。"""
    sm = _get_skill_manager(authorization)
    allowed_keys = {"enabled", "channels", "priority", "auto_update"}
    updates = {k: v for k, v in body.items() if k in allowed_keys}
    if not updates:
        raise HTTPException(status_code=400, detail="No valid config fields provided")
    if not sm.update_config(name, **updates):
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "ok", "name": name, **updates}


# ---------------------------------------------------------------------------
# ZIP 导出
# ---------------------------------------------------------------------------

@router.get("/{name}/export")
async def export_skill(
    name: str,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
):
    """导出技能为 ZIP 文件"""
    sm = _get_skill_manager(authorization)
    if sm.get_skill_config(name) is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / f"{name}.zip"

    try:
        sm.export_skill_to_zip(name, zip_path)
        background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"{name}.zip",
        )
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error("Failed to export skill: %s", exc)
        raise HTTPException(status_code=500, detail="Export failed")
