from agent import agent_app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from agentscope.session import RedisSession
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest

from config import REDIS_URL, SERVER_HOST, SERVER_PORT


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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_app.router, prefix="", tags=["agent"])

# AgentApp 的 openapi_extra 使用了 $ref 引用 AgentRequest，
# 但 include_router 不会合并 AgentApp 自定义的 openapi() 方法，
# 导致父 app 生成 OpenAPI schema 时找不到 AgentRequest 定义。
# 这里手动注入 schema 修复 $ref 解析。
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
