"""
API endpoints for prompt refinement.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.prompt_refinement import (
    AnalyzePromptRequest,
    AnalyzePromptResponse,
    BuildPromptRequest,
    BuildPromptResponse,
)
from app.services.prompt_refinement_service import get_prompt_refinement_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalyzePromptResponse)
async def analyze_prompt(request: AnalyzePromptRequest) -> AnalyzePromptResponse:
    """
    Analyze a basic prompt and return refinement questions.

    This endpoint detects the category of the prompt (person, animal, landscape, etc.)
    and returns contextually relevant questions to help refine the prompt.
    Uses LLM to generate dynamic, context-specific questions.
    """
    try:
        service = get_prompt_refinement_service()
        result = await service.get_questions(request.prompt)

        return AnalyzePromptResponse(
            category=result["category"], prompt=result["prompt"], questions=result["questions"]
        )
    except Exception as e:
        logger.error(f"Error analyzing prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze prompt: {str(e)}")


@router.post("/build", response_model=BuildPromptResponse)
async def build_prompt(request: BuildPromptRequest) -> BuildPromptResponse:
    """
    Build an enhanced prompt from user answers.

    Takes the basic prompt and user's answers to refinement questions,
    and returns a detailed, enhanced prompt ready for image generation.
    """
    try:
        service = get_prompt_refinement_service()
        result = service.build_enhanced_prompt(
            basic_prompt=request.basic_prompt, answers=request.answers, category=request.category
        )

        return BuildPromptResponse(
            enhanced_prompt=result["enhanced_prompt"],
            negative_prompt=result["negative_prompt"],
            original_prompt=request.basic_prompt,
        )
    except Exception as e:
        logger.error(f"Error building enhanced prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build enhanced prompt: {str(e)}")
