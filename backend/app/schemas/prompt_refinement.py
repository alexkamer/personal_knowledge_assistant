"""
Pydantic schemas for prompt refinement.
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Question(BaseModel):
    """A single refinement question."""

    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="The question text")
    type: Literal["single-select", "text"] = Field(..., description="Question type")
    options: Optional[List[str]] = Field(None, description="Options for single-select questions")
    placeholder: Optional[str] = Field(None, description="Placeholder text for text questions")


class AnalyzePromptRequest(BaseModel):
    """Request to analyze a prompt and get refinement questions."""

    prompt: str = Field(..., min_length=1, max_length=500, description="The basic prompt to analyze")


class AnalyzePromptResponse(BaseModel):
    """Response with refinement questions."""

    category: str = Field(..., description="Detected prompt category")
    prompt: str = Field(..., description="The original prompt")
    questions: List[Question] = Field(..., description="Refinement questions to ask")


class BuildPromptRequest(BaseModel):
    """Request to build an enhanced prompt from answers."""

    basic_prompt: str = Field(..., min_length=1, max_length=500, description="The original prompt")
    answers: Dict[str, str] = Field(..., description="User's answers to refinement questions")
    category: Optional[str] = Field(None, description="Optional category (will detect if not provided)")


class BuildPromptResponse(BaseModel):
    """Response with enhanced prompt."""

    enhanced_prompt: str = Field(..., description="The enhanced, detailed prompt")
    negative_prompt: str = Field(..., description="Automatically generated negative prompt")
    original_prompt: str = Field(..., description="The original basic prompt")
