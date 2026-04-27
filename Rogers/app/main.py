"""FitAgent FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys
sys.path.insert(0, "E:/fitagent/rogers/src")
from fitme.core.config import settings
from fitme.models import Base
from fitme.utils.database import engine

from .routers import auth_router, user_router, health_router, training_router, diet_router, agent_router


app = FastAPI(
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
app.include_router(agent_router)


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