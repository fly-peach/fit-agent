"""Routers Module"""
from .auth import router as auth_router
from .user import router as user_router
from .health import router as health_router
from .training import router as training_router
from .diet import router as diet_router
from .agent import agent_app as agent_router

__all__ = [
    "auth_router",
    "user_router",
    "health_router",
    "training_router",
    "diet_router",
    "agent_router",
]