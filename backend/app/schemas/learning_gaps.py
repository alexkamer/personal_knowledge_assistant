"""
Pydantic schemas for Learning Gaps Detection.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class LearningGapItem(BaseModel):
    """Schema for a single detected learning gap."""

    topic: str = Field(..., description="The missing foundational concept")
    description: str = Field(..., description="What this concept is and why it matters")
    prerequisite_for: str = Field(
        ..., description="How it relates to the user's question"
    )
    importance: str = Field(
        ..., description="Importance level: critical/important/helpful"
    )
    learning_resources: List[str] = Field(
        ..., description="Where to learn this concept"
    )
    estimated_time: str = Field(..., description="Estimated learning time")


class LearningGapRequest(BaseModel):
    """Schema for learning gap detection request."""

    user_question: str = Field(..., description="The user's question to analyze")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None, description="Previous conversation messages for context"
    )
    context: Optional[str] = Field(
        None, description="RAG context from knowledge base"
    )
    model: Optional[str] = Field(
        None, description="LLM model to use (default: qwen2.5:14b)"
    )


class LearningGapResponse(BaseModel):
    """Schema for learning gap detection response."""

    user_question: str
    gaps: List[LearningGapItem]
    total_gaps: int


class LearningPathRequest(BaseModel):
    """Schema for learning path generation request."""

    user_question: str = Field(..., description="The target topic")
    gaps: List[Dict] = Field(..., description="Detected learning gaps")
    model: Optional[str] = Field(
        None, description="LLM model to use (default: qwen2.5:14b)"
    )


class LearningPathResponse(BaseModel):
    """Schema for learning path generation response."""

    target_topic: str
    learning_sequence: List[str]
    total_estimated_time: str
    gaps: List[LearningGapItem]
