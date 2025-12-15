"""
Pydantic schemas for API request/response validation.
"""
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentContentResponse,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages,
    ConversationListResponse,
    ChatRequest,
    ChatResponse,
    MessageResponse,
)

__all__ = [
    "NoteCreate",
    "NoteUpdate",
    "NoteResponse",
    "NoteListResponse",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentContentResponse",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationWithMessages",
    "ConversationListResponse",
    "ChatRequest",
    "ChatResponse",
    "MessageResponse",
]
