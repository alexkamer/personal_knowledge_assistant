"""
Pydantic schemas for Conversation and Message models.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base schema for messages."""

    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message (user query)."""

    conversation_id: Optional[str] = Field(None, description="Conversation ID (creates new if not provided)")


class MessageFeedbackCreate(BaseModel):
    """Schema for creating message feedback."""

    is_positive: bool = Field(..., description="True for thumbs up, False for thumbs down")
    comment: Optional[str] = Field(None, description="Optional feedback comment")


class MessageFeedbackResponse(BaseModel):
    """Schema for message feedback response."""

    id: str
    message_id: str
    is_positive: bool
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(MessageBase):
    """Schema for message response."""

    id: str
    conversation_id: str
    created_at: datetime
    model_used: Optional[str] = None
    sources: Optional[List[dict]] = None  # Parsed from retrieved_chunks
    feedback: Optional[MessageFeedbackResponse] = None
    suggested_questions: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base schema for conversations."""

    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = None
    is_pinned: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""

    id: str
    summary: Optional[str] = None
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with full message history."""

    messages: List[MessageResponse]


class ConversationListResponse(BaseModel):
    """Schema for list of conversations response."""

    conversations: List[ConversationResponse]
    total: int


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., min_length=1, description="User's question or message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    conversation_title: Optional[str] = Field(None, description="Title for new conversation")
    model: Optional[str] = Field(None, description="LLM model to use")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    include_web_search: bool = Field(False, description="Include web search results")


class ChatResponse(BaseModel):
    """Schema for chat response."""

    conversation_id: str
    message_id: str
    response: str
    sources: List[dict]
    model_used: str
    suggested_questions: Optional[List[str]] = None
