"""Skill 管理 API 路由。"""
import logging
import os
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Header, UploadFile
from pydantic import BaseModel

from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from src.agents.harness.workspace.user_workspace import get_user_workspace
from src.agents.harness.skills.skill_manager import SkillManager
from src.agents.agent import agent_cache

logger = logging.getLogger("fitagent")

router = APIRouter(prefix="/api/agent/skills", tags=["skills"])


class SkillResponse(BaseModel):
    name: str
    version: str
    description: str
    enabled: bool
    path: str
    tags: List[str] = []


class SkillDetailResponse(SkillResponse):
    content: str


def _get_skill_manager(authorization: str | None) -> SkillManager:
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")
    user_dir = get_user_workspace(user_id)
    return SkillManager(user_dir)


@router.get("", response_model=List[SkillResponse])
async def list_skills(authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    skills = sm.list_skills()
    return [
        SkillResponse(
            name=s.name, version=s.version, description=s.description,
            enabled=s.enabled, path=s.path, tags=s.tags,
        )
        for s in skills
    ]


@router.get("/{name}", response_model=SkillDetailResponse)
async def get_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    skill = sm.get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillDetailResponse(
        name=skill.name, version=skill.version, description=skill.description,
        enabled=skill.enabled, path=skill.path, tags=skill.tags, content=skill.content,
    )


@router.put("/{name}/enable")
async def enable_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.enable_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    await _evict_user_agent(authorization)
    return {"status": "ok", "name": name, "enabled": True}


@router.put("/{name}/disable")
async def disable_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.disable_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    await _evict_user_agent(authorization)
    return {"status": "ok", "name": name, "enabled": False}


@router.post("/upload")
async def upload_skill(
    file: UploadFile,
    authorization: str | None = Header(default=None),
):
    sm = _get_skill_manager(authorization)

    if not file.content_type or "zip" not in file.content_type.lower():
        raise HTTPException(status_code=400, detail="仅支持 ZIP 文件")

    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        content = await file.read()
        if len(content) > 200 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="技能包不能超过 200MB")
        tf.write(content)
        tf.flush()
        try:
            skill_name = sm.install_skill_from_zip(tf.name)
        finally:
            os.unlink(tf.name)

    return {"status": "ok", "name": skill_name}


@router.delete("/{name}")
async def delete_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.delete_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    await _evict_user_agent(authorization)
    return {"status": "ok", "name": name}


async def _evict_user_agent(authorization: str | None):
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
        await agent_cache.evict(user_id)
    except NotAuthenticatedError:
        pass
