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
from contextlib import asynccontextmanager
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest

logger = logging.getLogger("fitagent")


from src.fitme.core.config import settings
from src.fitme.models import UserDBBase
from src.fitme.utils.database import user_engine

from .routers import auth_router, user_router, health_router, training_router, diet_router, exercise_router, agent_config_router
from .routers.agent import agent_app, router as agent_router, _auth_token
from .routers import skills, memory, context

@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化服务。"""
    # 1. 初始化 fitbase.db（建表 + 种子数据，幂等）
    from src.fitme.seed import seed_base_db
    result = seed_base_db()
    if any(v > 0 for v in result.values()):
        logger.info("fitbase.db 种子数据已加载: %s", result)

    # 2. 初始化 fituser.db（建表）
    UserDBBase.metadata.create_all(bind=user_engine)

    # 迁移：为新列添加 ALTER TABLE (仅在 user_db 上)
    import sqlalchemy as sa
    with user_engine.connect() as conn:
        for col, col_type in [("recurring_group_id", "INTEGER")]:
            try:
                conn.execute(sa.text(f"ALTER TABLE training_plans ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # 列已存在

    # 创建测试账户
    from .seed import seed_test_accounts
    seed_test_accounts()

    # 3. 初始化 agent_memory.db（FitAgentSQLMemory 专用，独立于主库）
    from src.agents.harness.memory.fitagent_memory import FitAgentSQLMemory
    from src.fitme.utils.database import async_agent_memory_engine
    memory = FitAgentSQLMemory(
        engine_or_session=async_agent_memory_engine,
        user_id="_init",
        session_id="_init",
    )
    try:
        await memory._create_table()
    finally:
        await memory.close()

    try:
        yield
    finally:
        print("AgentApp is shutting down...")



app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FitAgent 健身管理平台 API",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"],
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


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(health_router)
app.include_router(training_router)
app.include_router(diet_router)
app.include_router(exercise_router)
app.include_router(agent_config_router)
app.include_router(agent_app.router, prefix="", tags=["agent"])
app.include_router(agent_router)
app.include_router(skills.router)
app.include_router(memory.router)
app.include_router(context.router)

# AgentScope Runtime 会自动注册 "/" 根路由，导致前端首页被 JSON 响应覆盖。
# 保留其 "/process" 等接口，仅移除冲突的首页路由。
app.router.routes = [
    route for route in app.router.routes
    if not (getattr(route, "path", None) == "/" and getattr(route, "name", None) == "root")
]



_original_openapi = app.openapi


def _patched_openapi() -> dict:
    schema = _original_openapi()
    agent_schema = AgentRequest.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    components = schema.setdefault("components", {})
    component_schemas = components.setdefault("schemas", {})
    for def_name, def_schema in agent_schema.pop("$defs", {}).items():
        component_schemas.setdefault(def_name, def_schema)
    component_schemas.setdefault("AgentRequest", agent_schema)
    return schema



app.openapi = _patched_openapi

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ========== 静态文件服务 (前端控制台) ==========
from fastapi.responses import FileResponse

CONSOLE_DIR = Path(__file__).resolve().parent.parent / "console"
DIST_DIR = CONSOLE_DIR / "dist"

if DIST_DIR.exists():
    # 挂载静态文件在根路径（必须放在所有 API 路由之后）
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    # SPA fallback: 所有非 API 路由都返回 index.html
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"detail": "Not Found"}, 404
elif CONSOLE_DIR.exists():
    # 开发模式 fallback (如果有需要)
    pass
