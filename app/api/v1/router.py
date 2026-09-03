from fastapi import APIRouter

from app.api.v1.endpoints import analytics, dashboard, health, sync

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(sync.router, tags=["sync"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(analytics.router, tags=["analytics"])
