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
# 配置管理（必须先于 /{name} 定义，避免被 {name} 拦截）
# ---------------------------------------------------------------------------

@router.get("/config")
async def get_skill_config(authorization: str | None = Header(default=None)):
    """获取技能系统配置（基于 skill-config.json）。"""
    sm = _get_skill_manager(authorization)
    sm.ensure_scanned()
    return {
        "version": "1.0.0",
        "initialized": sm.config_path.exists(),
        "initialized_at": None,
        "last_synced_at": None,
        "default_skills_enabled": list(sm._configs.keys()),
        "skill_packages": {
            name: cfg.to_dict()
            for name, cfg in sm._configs.items()
        },
        "global_settings": {},
    }


@router.get("/config/sync-status")
async def get_sync_status(authorization: str | None = Header(default=None)):
    """获取技能同步状态。"""
    sm = _get_skill_manager(authorization)
    sm.ensure_scanned()
    return {
        "initialized": sm.config_path.exists(),
        "initialized_at": None,
        "last_synced_at": None,
        "total_skill_packages": len(sm._configs),
        "total_scanned_skills": len(sm._skill_dirs),
        "enabled_skills": sm.get_enabled_skill_names("all"),
    }


@router.post("/config/initialize")
async def initialize_skill_config(
    body: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    """初始化技能配置。"""
    sm = _get_skill_manager(authorization)
    sm.ensure_scanned()
    return {
        "version": "1.0.0",
        "initialized": True,
        "initialized_at": None,
        "last_synced_at": None,
        "default_skills_enabled": body.get("default_skill_names", []),
        "skill_packages": {
            name: cfg.to_dict()
            for name, cfg in sm._configs.items()
        },
        "global_settings": {},
    }


@router.post("/config/sync")
async def sync_skill_config(
    body: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    """同步技能配置。"""
    sm = _get_skill_manager(authorization)
    sm.ensure_scanned()
    return {
        "version": "1.0.0",
        "initialized": sm.config_path.exists(),
        "initialized_at": None,
        "last_synced_at": None,
        "default_skills_enabled": sm.get_enabled_skill_names("all"),
        "skill_packages": {
            name: cfg.to_dict()
            for name, cfg in sm._configs.items()
        },
        "global_settings": {},
    }


@router.put("/config/packages/{pkg_name}")
async def update_skill_package(
    pkg_name: str,
    body: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    """更新技能包配置。"""
    sm = _get_skill_manager(authorization)
    allowed_keys = {"enabled", "auto_update", "priority", "config"}
    updates = {k: v for k, v in body.items() if k in allowed_keys}
    if not updates:
        raise HTTPException(status_code=400, detail="No valid config fields provided")
    sm.update_config(pkg_name, **updates)
    sm.ensure_scanned()
    return {
        "version": "1.0.0",
        "initialized": sm.config_path.exists(),
        "initialized_at": None,
        "last_synced_at": None,
        "default_skills_enabled": sm.get_enabled_skill_names("all"),
        "skill_packages": {
            name: cfg.to_dict()
            for name, cfg in sm._configs.items()
        },
        "global_settings": {},
    }


@router.delete("/config/reset")
async def reset_skill_config(authorization: str | None = Header(default=None)):
    """重置技能配置。"""
    sm = _get_skill_manager(authorization)
    if sm.config_path.exists():
        sm.config_path.unlink()
    sm.scan_skills()
    return {
        "version": "1.0.0",
        "initialized": True,
        "initialized_at": None,
        "last_synced_at": None,
        "default_skills_enabled": sm.get_enabled_skill_names("all"),
        "skill_packages": {
            name: cfg.to_dict()
            for name, cfg in sm._configs.items()
        },
        "global_settings": {},
    }


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


# ---------------------------------------------------------------------------
# 子技能
# ---------------------------------------------------------------------------

@router.get("/{name}/sub-skills")
async def list_sub_skills(
    name: str,
    authorization: str | None = Header(default=None),
):
    """列出指定技能下的子技能。"""
    sm = _get_skill_manager(authorization)
    return sm.list_sub_skills(name)
