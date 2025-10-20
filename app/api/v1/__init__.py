from fastapi import APIRouter
from .endpoints import health, onboarding, auth, pipeline, chat_sessions, chat, widgets

api_router = APIRouter()

# Include endpoint routes
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(chat_sessions.router, prefix="/chat/sessions", tags=["chat"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(widgets.router, prefix="/widgets", tags=["widgets"])