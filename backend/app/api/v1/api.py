"""
API v1 router combining all endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import chat, documents, notes, tags, youtube

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
