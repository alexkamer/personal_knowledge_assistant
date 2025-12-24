"""
Image generation endpoints for Gemini Imagen API.
"""
import json
import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.image_generation import ImageGenerationRequest
from app.services.image_generation_service import get_image_generation_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate/stream")
async def generate_images_stream(
    request: ImageGenerationRequest,
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

            # Send status: generating images
            image_word = "image" if request.number_of_images == 1 else "images"
            yield f'data: {json.dumps({"type": "status", "status": f"Generating {request.number_of_images} {image_word}..."})}\n\n'

            # Prepare reference images if provided
            reference_images = None
            if request.reference_images:
                reference_images = [
                    {"image_data": img.image_data, "mime_type": img.mime_type}
                    for img in request.reference_images
                ]

            # Generate images using service
            service = get_image_generation_service()
            images = await service.generate_images(
                prompt=request.prompt,
                aspect_ratio=request.aspect_ratio,
                image_size=request.image_size,
                number_of_images=request.number_of_images,
                negative_prompt=request.negative_prompt,
                model=request.model,
                reference_images=reference_images,
            )

            # Send images with metadata
            images_data = {
                "type": "images",
                "images": images,
                "metadata": {
                    "prompt": request.prompt,
                    "aspect_ratio": request.aspect_ratio,
                    "image_size": request.image_size,
                    "model": request.model,
                    "negative_prompt": request.negative_prompt,
                },
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
