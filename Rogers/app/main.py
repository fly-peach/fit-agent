"""FitAgent FastAPI Application"""
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load .env file FIRST before any other imports
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# 暂时禁用 agentscope_runtime，避免导入错误
# from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest

logger = logging.getLogger("fitagent")


from src.core.config import settings
from src.fitme.models import UserDBBase
from src.fitme.utils.database import user_engine, async_user_engine

from .routers import auth_router, user_router, health_router, training_router, diet_router, exercise_router, agent_config_router
from .routers.agent import agent_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化服务。"""
    # ── 0. SQLite 并发优化：WAL 模式 + busy_timeout ──
    import sqlalchemy as _sa
    with user_engine.connect() as conn:
        conn.execute(_sa.text("PRAGMA journal_mode=WAL"))
        conn.execute(_sa.text("PRAGMA busy_timeout=5000"))
        conn.commit()
    logger.info("SQLite WAL 模式已启用 (busy_timeout=5000ms)")

    # 1. 初始化 fitbase.db（建表 + 种子数据，幂等）
    from src.fitme.seed import seed_base_db
    result = seed_base_db()
    if any(v > 0 for v in result.values()):
        logger.info("fitbase.db 种子数据已加载: %s", result)

    # 2. 初始化 fituser.db（建表）
    UserDBBase.metadata.create_all(bind=user_engine)

    # 2.1 初始化 agent pipeline 交互记录表（复用 UserDBBase）
    from src.agents.harness.memory import PipelineExchange
    PipelineExchange.metadata.create_all(bind=user_engine)
    logger.info("agent_pipeline_exchanges 表已就绪")

    # 迁移：为新列添加 ALTER TABLE（仅在 user_db 上）
    import sqlalchemy as sa
    with user_engine.connect() as conn:
        for col, col_type in [("recurring_group_id", "INTEGER")]:
            try:
                conn.execute(sa.text(f"ALTER TABLE training_plans ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # 列已存在

        # 迁移：为 users 表添加 id 列（兼容 AsyncSQLAlchemyMemory）
        try:
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN id INTEGER"))
            conn.commit()
            logger.info("已为 users 表添加 id 列")
        except Exception:
            pass  # 列已存在

        # 迁移：为现有 users 记录填充 id = user_id
        try:
            result = conn.execute(sa.text("UPDATE users SET id = user_id WHERE id IS NULL"))
            conn.commit()
            if result.rowcount > 0:
                logger.info("已为 %d 条 users 记录同步 id = user_id", result.rowcount)
        except Exception:
            pass

        # 迁移：为 user_settings 表添加 auto_approve_db_write 列
        try:
            conn.execute(sa.text("ALTER TABLE user_settings ADD COLUMN auto_approve_db_write BOOLEAN DEFAULT 0"))
            conn.commit()
            logger.info("已为 user_settings 添加 auto_approve_db_write 列")
        except Exception:
            pass

    # 创建测试账户
    from .seed import seed_test_accounts
    seed_test_accounts()

    # 3. 在 fituser.db 上创建 agent_* 表（仅 4 张，跳过原版避免冲突）
    async with async_user_engine.begin() as conn:
        from src.agents.harness.memory.fit_memory import FitMemBase
        agent_tables = [
            FitMemBase.metadata.tables[name]
            for name in ("agent_users", "agent_session", "agent_message", "agent_message_mark")
        ]
        await conn.run_sync(lambda c: FitMemBase.metadata.create_all(c, tables=agent_tables))
    logger.info("Agent 记忆表 (agent_*) 已在 fituser.db 中就绪")

    try:
        yield
    finally:
        logger.info("FitAgent shutdown complete.")


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FitAgent 健身管理平台 API",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def set_auth_token(request: Request, call_next):
    """从多个来源提取 token 存入 ContextVar：
    1. Authorization: Bearer <token>
    2. ?token=<token> 查询参数（SSE 场景常用）
    3. Cookie token=<token>
    """
    from .routers.agent import _auth_token
    token = None
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    else:
        token = request.query_params.get("token")
    if not token:
        token = request.cookies.get("token")
    _auth_token.set(token)
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录每个 HTTP 请求的详细信息。"""
    start_time = time.time()
    method = request.method
    path = request.url.path
    client = request.client.host if request.client else "unknown"
    logger.info(">> %s %s from %s", method, path, client)

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info("<< %s %s -> %s (%.2fs)", method, path, response.status_code, duration)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，记录 500 错误详情。"""
    logger.exception(f"未处理异常 {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "detail": "服务器内部错误", "path": request.url.path},
    )


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(health_router)
app.include_router(training_router)
app.include_router(diet_router)
app.include_router(exercise_router)
app.include_router(agent_config_router)
app.include_router(agent_app.router, prefix="", tags=["agent"])

# AgentScope Runtime 会自动注册 "/" 根路由，导致前端首页被 JSON 响应覆盖。
# 保留其 "/process" 等接口，仅移除冲突的首页路由。
app.router.routes = [
    route for route in app.router.routes
    if not (getattr(route, "path", None) == "/" and getattr(route, "name", None) == "root")
]

# 暂时禁用 agentscope_runtime 相关代码
# _original_openapi = app.openapi
#
# def _patched_openapi() -> dict:
#     schema = _original_openapi()
#     agent_schema = AgentRequest.model_json_schema(
#         ref_template="#/components/schemas/{model}"
#     )
#     components = schema.setdefault("components", {})
#     component_schemas = components.setdefault("schemas", {})
#     for def_name, def_schema in agent_schema.pop("$defs", {}).items():
#         component_schemas.setdefault(def_name, def_schema)
#     component_schemas.setdefault("AgentRequest", agent_schema)
#     return schema
#
# app.openapi = _patched_openapi
