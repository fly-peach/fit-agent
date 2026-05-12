"""Rogers Agent - 简化版主应用入口

独立运行的健身助手 Agent，基于 AgentScope 和 FastAPI。
使用 fakeredis 存储会话状态。
"""
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rogers")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.agent import agent_app, router as agent_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用。"""
    app = FastAPI(
        title="Rogers Agent API",
        description="专业的健身和健康管理助手 - 多智能体管道编排",
        version="2.0.0",
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 AgentApp 的路由（包含 /process, /v1/chat/completions 等）
    app.include_router(agent_app.router, prefix="", tags=["agent-runtime"])

    # 注册我们的 REST API
    app.include_router(agent_router)

    # 移除 AgentApp 默认的首页路由，避免冲突
    app.router.routes = [
        route for route in app.router.routes
        if not (getattr(route, "path", None) == "/" and getattr(route, "name", None) == "root")
    ]

    @app.get("/")
    async def root():
        """根路径 - API 信息。"""
        return {
            "name": "Rogers Agent API",
            "version": "2.0.0",
            "description": "专业的健身和健康管理助手",
            "endpoints": {
                "health": "/api/agent/health",
                "config": "/api/agent/config",
                "chat": "/api/agent/chat",
                "agent_process": "/process",
                "openapi": "/openapi.json",
                "docs": "/docs",
            },
        }

    @app.get("/health")
    async def health_check():
        """健康检查。"""
        from src.agents.config import config
        return {
            "status": "healthy",
            "api_key_configured": config.is_configured(),
            "vision_model": config.VISION_MODEL,
            "reasoning_model": config.REASONING_MODEL,
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    from src.agents.config import config

    logger.info("=" * 60)
    logger.info("Rogers Agent - 健身助手")
    logger.info("=" * 60)
    logger.info(f"Vision Model: {config.VISION_MODEL}")
    logger.info(f"Reasoning Model: {config.REASONING_MODEL}")
    logger.info(f"API Key Configured: {'Yes' if config.is_configured() else 'No'}")
    logger.info("=" * 60)

    if not config.is_configured():
        logger.warning("⚠️  请在 .env 文件中配置 DASHSCOPE_API_KEY")
        logger.warning("⚠️  或者设置环境变量 DASHSCOPE_API_KEY")

    uvicorn.run(
        "rogers_main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
    )
