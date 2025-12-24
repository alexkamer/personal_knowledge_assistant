"""
Image generation endpoints for Gemini Imagen API.
"""
import json
import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.image_generation import ImageGenerationRequest
from app.services.image_generation_service import get_image_generation_service
from app.services.image_context_service import get_image_context_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate/stream")
async def generate_images_stream(
    request: ImageGenerationRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Generate images and stream status updates via SSE.

    Returns Server-Sent Events (SSE) stream with:
    - type: "status" - Status updates during generation ("Validating prompt...", "Generating...")
    - type: "images" - Generated images as base64 data with metadata
    - type: "done" - Signal completion
    - type: "error" - Error message if generation fails

    Args:
        request: Image generation request with prompt, aspect ratio, size, etc.

    Returns:
        StreamingResponse with Server-Sent Events
    """

    async def generate_stream():
        """Generator function for streaming response."""
        try:
            # Send status: validating prompt
            yield f'data: {json.dumps({"type": "status", "status": "Validating prompt..."})}\n\n'

            # Basic prompt validation
            if not request.prompt.strip():
                yield f'data: {json.dumps({"type": "error", "error": "Prompt cannot be empty"})}\n\n'
                return

            # Handle conversation context if provided
            context_service = get_image_context_service()
            enhanced_prompt = request.prompt
            is_iterative = False

            if request.conversation_context:
                # Check if prompt is iterative
                yield f'data: {json.dumps({"type": "status", "status": "Analyzing prompt context..."})}\n\n'

                is_iterative = await context_service.is_iterative_prompt(
                    request.prompt,
                    request.conversation_context.previous_prompt
                )

                if is_iterative:
                    # Enhance prompt with previous context
                    enhanced_prompt = await context_service.enhance_prompt_with_context(
                        request.prompt,
                        request.conversation_context.previous_prompt,
                        request.conversation_context.previous_metadata
                    )

                    yield f'data: {json.dumps({"type": "status", "status": "Building on previous image..."})}\n\n'
                    logger.info(f"Iterative prompt detected. Enhanced: {enhanced_prompt}")

            # Send status: generating images
            image_word = "image" if request.number_of_images == 1 else "images"
            yield f'data: {json.dumps({"type": "status", "status": f"Generating {request.number_of_images} {image_word}..."})}\n\n'

            # Prepare reference images
            reference_images = None
            if request.reference_images:
                reference_images = [
                    {"image_data": img.image_data, "mime_type": img.mime_type}
                    for img in request.reference_images
                ]
            elif is_iterative and request.conversation_context and request.conversation_context.previous_image_data:
                # Automatically use previous image as reference for iterative prompts
                reference_images = [
                    {
                        "image_data": request.conversation_context.previous_image_data,
                        "mime_type": "image/png"  # Assume PNG for generated images
                    }
                ]
                logger.info("Using previous image as reference for iterative generation")

            # Generate images using service
            service = get_image_generation_service()
            images = await service.generate_images(
                prompt=enhanced_prompt,  # Use enhanced prompt if iterative
                aspect_ratio=request.aspect_ratio,
                image_size=request.image_size,
                number_of_images=request.number_of_images,
                negative_prompt=request.negative_prompt,
                model=request.model,
                reference_images=reference_images,
                enable_google_search=request.enable_google_search,
            )

            # Save images to database
            metadata = {
                "prompt": request.prompt,
                "aspect_ratio": request.aspect_ratio,
                "image_size": request.image_size,
                "model": request.model,
                "negative_prompt": request.negative_prompt,
            }

            try:
                saved_images = await service.save_images_to_database(
                    images=images,
                    prompt=request.prompt,
                    metadata=metadata,
                    db=db,
                )
                # Add image IDs to response
                for i, saved_img in enumerate(saved_images):
                    images[i]["id"] = saved_img.id
            except Exception as e:
                logger.error(f"Failed to save images to database: {e}", exc_info=True)
                # Continue anyway - at least return the generated images

            # Send images with metadata
            images_data = {
                "type": "images",
                "images": images,
                "metadata": metadata,
            }
            yield f"data: {json.dumps(images_data)}\n\n"

            # Send done signal
            yield f'data: {json.dumps({"type": "done"})}\n\n'

        except Exception as e:
            logger.error(f"Image generation stream error: {e}", exc_info=True)
            error_message = str(e)

            # Provide more helpful error messages for common issues
            if "API key not configured" in error_message:
                error_message = (
                    "Gemini API key is not configured. "
                    "Please add GEMINI_API_KEY to your environment variables."
                )
            elif "quota" in error_message.lower() or "rate" in error_message.lower():
                error_message = "API rate limit exceeded. Please try again later."
            elif "policy" in error_message.lower() or "safety" in error_message.lower():
                error_message = (
                    "Image generation blocked by content policy. "
                    "Please modify your prompt and try again."
                )

            yield f'data: {json.dumps({"type": "error", "error": error_message})}\n\n'

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/health")
async def check_health() -> dict:
    """
    Check if image generation service is available.

    Returns:
        Dictionary with service status
    """
    service = get_image_generation_service()
    is_available = service.client is not None

    return {
        "service": "image_generation",
        "available": is_available,
        "message": "Service is ready" if is_available else "Gemini API key not configured",
    }
