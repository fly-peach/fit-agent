"""FitAgent FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from agentscope.session import RedisSession
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest


import sys
from src.fitme.core.config import settings
from src.fitme.models import Base
from src.fitme.utils.database import engine

from .routers import auth_router, user_router, health_router, training_router, diet_router
from .routers.agent import agent_app
from .config import REDIS_URL, SERVER_HOST, SERVER_PORT

@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化服务。"""
    if REDIS_URL:
        import redis.asyncio as aioredis

        redis_client = aioredis.Redis.from_url(
            REDIS_URL, decode_responses=True
        )
        session = RedisSession(
            connection_pool=redis_client.connection_pool
        )
    else:
        # 开发/测试环境：使用 fakeredis
        import fakeredis

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        session = RedisSession(
            connection_pool=fake_redis.connection_pool
        )

    # agent_app 的 query_func 通过 agent_app.state 访问 session，
    # 需要同时设置到 agent_app 上。
    app.state.session = session
    agent_app.state.session = session

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


@app.on_event("startup")
def startup():
    """启动时创建数据库表"""
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(health_router)
app.include_router(training_router)
app.include_router(diet_router)
app.include_router(agent_app.router, prefix="", tags=["agent"])



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