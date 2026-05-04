"""FitAgent FastAPI Application"""
import os
import logging
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest

logger = logging.getLogger("fitagent")


from src.fitme.core.config import settings
from src.fitme.models import Base
from src.fitme.utils.database import engine

from .routers import auth_router, user_router, health_router, training_router, diet_router, exercise_router
from .routers.agent import agent_app, router as agent_router, _auth_token
from .routers import skills, memory, context

@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化服务。"""
    # 创建数据库表并创建测试账户
    Base.metadata.create_all(bind=engine)

    # 迁移：为新列添加 ALTER TABLE
    import sqlalchemy as sa
    with engine.connect() as conn:
        for col, col_type in [("recurring_group_id", "INTEGER")]:
            try:
                conn.execute(sa.text(f"ALTER TABLE training_plans ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # 列已存在

    from .seed import seed_test_accounts
    seed_test_accounts()

    # Disk-based session storage — stores under users/{user_id}/sessions/
    sessions_dir = Path(__file__).resolve().parent.parent / "agent_db" / "workspace" / "users"
    from src.agents.harness.sessions.user_session import UserSession
    session = UserSession(save_dir=str(sessions_dir))

    # agent_app 的 query_func 通过 agent_app.state 访问 session，
    # 需要同时设置到 agent_app 上。
    app.state.session = session
    agent_app.state.session = session

    try:
        yield
    finally:
        # Clean up ReMe memory managers
        from src.agents.agent import agent_cache
        for agent in agent_cache._agents.values():
            mm = getattr(agent, "_memory_manager", None)
            if mm:
                try:
                    await mm.close()
                except Exception as e:
                    logger.warning(f"Failed to close memory manager: {e}")
        agent_cache._agents.clear()
        print("AgentApp is shutting down...")
        
        
        
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
app.include_router(agent_app.router, prefix="", tags=["agent"])
app.include_router(agent_router)
app.include_router(skills.router)
app.include_router(memory.router)
app.include_router(context.router)



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
@app.get("/")
def root():
    """根路由"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "FitAgent API 服务运行中"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}