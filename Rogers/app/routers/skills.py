"""Skill 管理 API 路由。"""
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, UploadFile, Depends
from pydantic import BaseModel, Field

from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from src.agents.harness.workspace.user_workspace import get_user_workspace, restock_template_skills, ensure_user_workspace
from src.agents.harness.skills.skill_manager import SkillManager
from src.agents.harness.skills.skill_config import (
    SkillSystemConfig, SkillPackageConfig
)

logger = logging.getLogger("fitagent")

router = APIRouter(prefix="/api/agent/skills", tags=["skills"])


class SkillResponse(BaseModel):
    name: str
    version: str
    description: str
    enabled: bool
    path: str
    tags: List[str] = []
    channels: List[str] = []
    source: str = "workspace"


class SkillDetailResponse(SkillResponse):
    content: str
    body: str
    references: List[str] = []
    scripts: List[str] = []
    config: dict[str, Any] = Field(default_factory=dict)


class SkillPackageConfigResponse(BaseModel):
    name: str
    enabled: bool = True
    auto_update: bool = True
    priority: int = 0
    config: dict[str, Any] = Field(default_factory=dict)


class SkillSystemConfigResponse(BaseModel):
    version: str
    initialized: bool
    initialized_at: str | None = None
    last_synced_at: str | None = None
    default_skills_enabled: List[str] = Field(default_factory=list)
    skill_packages: dict[str, SkillPackageConfigResponse] = Field(default_factory=dict)
    global_settings: dict[str, Any] = Field(default_factory=dict)


class SkillSyncStatusResponse(BaseModel):
    initialized: bool
    initialized_at: str | None = None
    last_synced_at: str | None = None
    total_skill_packages: int
    total_scanned_skills: int
    enabled_skills: List[str]


class InitializeConfigRequest(BaseModel):
    default_skill_names: List[str] = Field(default_factory=list)


class UpdateSkillPackageRequest(BaseModel):
    enabled: bool | None = None
    auto_update: bool | None = None
    priority: int | None = None
    config: dict[str, Any] | None = None


class SyncConfigRequest(BaseModel):
    direction: str = "two-way"  # "two-way", "to-config", "from-config"


def _get_skill_manager(authorization: str | None) -> SkillManager:
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")
    user_dir = ensure_user_workspace(user_id)
    return SkillManager(user_dir)


# ===== 技能基本管理 API =====

@router.get("", response_model=List[SkillResponse])
async def list_skills(authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    skills = sm.list_skills()
    return [
        SkillResponse(
            name=s.name, version=s.version, description=s.description,
            enabled=s.enabled, path=s.path, tags=s.tags,
            channels=s.channels, source=s.source,
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
        body=skill.body,
        references=skill.references,
        scripts=skill.scripts,
        channels=skill.channels,
        config=skill.config,
        source=skill.source,
    )


@router.get("/{name}/files/{file_path:path}")
async def get_skill_file(
    name: str,
    file_path: str,
    authorization: str | None = Header(default=None),
):
    sm = _get_skill_manager(authorization)
    content = sm.load_skill_file(name, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill file not found")
    return {"content": content}


@router.put("/{name}/enable")
async def enable_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.enable_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    # 同步到配置
    sm.sync_to_config()
    return {"status": "ok", "name": name, "enabled": True}


@router.put("/{name}/disable")
async def disable_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.disable_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    # 同步到配置
    sm.sync_to_config()
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
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            os.unlink(tf.name)

    # 同步新安装的技能到配置
    sm.sync_to_config()
    return {"status": "ok", "name": skill_name}


@router.delete("/{name}")
async def delete_skill(name: str, authorization: str | None = Header(default=None)):
    sm = _get_skill_manager(authorization)
    if not sm.delete_skill(name):
        raise HTTPException(status_code=404, detail="Skill not found")
    # 同步到配置
    sm.sync_to_config()
    return {"status": "ok", "name": name}


# ===== 技能配置管理 API =====

@router.get("/config", response_model=SkillSystemConfigResponse)
async def get_skill_config(authorization: str | None = Header(default=None)):
    """获取技能系统配置"""
    sm = _get_skill_manager(authorization)
    config = sm.get_config()
    return SkillSystemConfigResponse(
        version=config.version,
        initialized=config.initialized,
        initialized_at=config.initialized_at,
        last_synced_at=config.last_synced_at,
        default_skills_enabled=config.default_skills_enabled,
        skill_packages={
            name: SkillPackageConfigResponse(
                name=pkg.name,
                enabled=pkg.enabled,
                auto_update=pkg.auto_update,
                priority=pkg.priority,
                config=pkg.config
            )
            for name, pkg in config.skill_packages.items()
        },
        global_settings=config.global_settings
    )


@router.get("/config/sync-status", response_model=SkillSyncStatusResponse)
async def get_sync_status(authorization: str | None = Header(default=None)):
    """获取配置同步状态"""
    sm = _get_skill_manager(authorization)
    status = sm.get_sync_status()
    return SkillSyncStatusResponse(**status)


@router.post("/config/initialize", response_model=SkillSystemConfigResponse)
async def initialize_config(
    request: InitializeConfigRequest,
    authorization: str | None = Header(default=None)
):
    """初始化技能配置系统"""
    sm = _get_skill_manager(authorization)
    config = sm.initialize_skill_config(request.default_skill_names)
    return SkillSystemConfigResponse(
        version=config.version,
        initialized=config.initialized,
        initialized_at=config.initialized_at,
        last_synced_at=config.last_synced_at,
        default_skills_enabled=config.default_skills_enabled,
        skill_packages={
            name: SkillPackageConfigResponse(
                name=pkg.name,
                enabled=pkg.enabled,
                auto_update=pkg.auto_update,
                priority=pkg.priority,
                config=pkg.config
            )
            for name, pkg in config.skill_packages.items()
        },
        global_settings=config.global_settings
    )


@router.post("/config/sync", response_model=SkillSystemConfigResponse)
async def sync_config(
    request: SyncConfigRequest,
    authorization: str | None = Header(default=None)
):
    """同步技能配置

    direction:
        - "two-way": 双向同步（默认）
        - "to-config": 仅将技能状态同步到配置
        - "from-config": 仅从配置同步到技能状态
    """
    sm = _get_skill_manager(authorization)

    if request.direction == "from-config":
        sm.sync_from_config()
    elif request.direction == "to-config":
        sm.sync_to_config()
    else:
        # 双向同步
        sm.sync_to_config()
        sm.sync_from_config()

    config = sm.get_config()
    return SkillSystemConfigResponse(
        version=config.version,
        initialized=config.initialized,
        initialized_at=config.initialized_at,
        last_synced_at=config.last_synced_at,
        default_skills_enabled=config.default_skills_enabled,
        skill_packages={
            name: SkillPackageConfigResponse(
                name=pkg.name,
                enabled=pkg.enabled,
                auto_update=pkg.auto_update,
                priority=pkg.priority,
                config=pkg.config
            )
            for name, pkg in config.skill_packages.items()
        },
        global_settings=config.global_settings
    )


@router.put("/config/packages/{name}", response_model=SkillSystemConfigResponse)
async def update_skill_package_config(
    name: str,
    request: UpdateSkillPackageRequest,
    authorization: str | None = Header(default=None)
):
    """更新单个技能包的配置"""
    sm = _get_skill_manager(authorization)

    config = sm.config_manager.update_skill_package(
        name=name,
        enabled=request.enabled,
        auto_update=request.auto_update,
        priority=request.priority,
        config=request.config
    )

    # 如果启用状态有变化，同步到技能
    if request.enabled is not None:
        if request.enabled:
            sm.enable_skill(name)
        else:
            sm.disable_skill(name)

    return SkillSystemConfigResponse(
        version=config.version,
        initialized=config.initialized,
        initialized_at=config.initialized_at,
        last_synced_at=config.last_synced_at,
        default_skills_enabled=config.default_skills_enabled,
        skill_packages={
            name: SkillPackageConfigResponse(
                name=pkg.name,
                enabled=pkg.enabled,
                auto_update=pkg.auto_update,
                priority=pkg.priority,
                config=pkg.config
            )
            for name, pkg in config.skill_packages.items()
        },
        global_settings=config.global_settings
    )


@router.delete("/config/reset", response_model=SkillSystemConfigResponse)
async def reset_skill_config(authorization: str | None = Header(default=None)):
    """重置技能配置到初始状态"""
    sm = _get_skill_manager(authorization)
    config = sm.reset_config()
    return SkillSystemConfigResponse(
        version=config.version,
        initialized=config.initialized,
        initialized_at=config.initialized_at,
        last_synced_at=config.last_synced_at,
        default_skills_enabled=config.default_skills_enabled,
        skill_packages={
            name: SkillPackageConfigResponse(
                name=pkg.name,
                enabled=pkg.enabled,
                auto_update=pkg.auto_update,
                priority=pkg.priority,
                config=pkg.config
            )
            for name, pkg in config.skill_packages.items()
        },
        global_settings=config.global_settings
    )


@router.post("/restock-templates")
async def restock_template_skills_endpoint(authorization: str | None = Header(default=None)):
    """重新补充缺失的模板技能

    从 templates/skills/ 复制缺失的模板技能到用户工作区。
    不会覆盖用户已修改的技能。

    Returns:
        {
            "status": "ok",
            "restocked": [skill_name1, skill_name2, ...]
        }
    """
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    restocked = restock_template_skills(user_id)

    # 重新扫描技能
    sm = _get_skill_manager(authorization)
    sm.scan_skills()

    # 同步到配置
    sm.sync_to_config()

    return {"status": "ok", "restocked": restocked}
