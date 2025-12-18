"""
API v1 router combining all endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import chat, context, contradictions, documents, knowledge_evolution, learning_gaps, notes, research, tags, youtube

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
api_router.include_router(context.router, prefix="/context", tags=["context"])
api_router.include_router(contradictions.router, prefix="/contradictions", tags=["contradictions"])
api_router.include_router(learning_gaps.router, prefix="/learning-gaps", tags=["learning_gaps"])
api_router.include_router(knowledge_evolution.router, prefix="/knowledge-evolution", tags=["knowledge_evolution"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
