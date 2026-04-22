from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.body_composition import router as body_composition_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.daily_metrics import router as daily_metrics_router
from app.api.v1.daily_nutrition import router as daily_nutrition_router
from app.api.v1.daily_workout import router as daily_workout_router
from app.api.v1.agent import router as agent_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(assessments_router, prefix="/assessments", tags=["assessments"])
api_router.include_router(body_composition_router, prefix="/body-composition", tags=["body-composition"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(daily_metrics_router, prefix="/daily-metrics", tags=["daily-metrics"])
api_router.include_router(daily_workout_router, prefix="/daily-workout", tags=["daily-workout"])
api_router.include_router(daily_nutrition_router, prefix="/daily-nutrition", tags=["daily-nutrition"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
