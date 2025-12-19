"""
Autocomplete endpoint for AI-powered text completion.
"""
from fastapi import APIRouter, HTTPException
from app.schemas.autocomplete import AutocompleteRequest, AutocompleteResponse
from app.core.config import settings
import logging
import ollama
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=AutocompleteResponse)
async def get_autocomplete(request: AutocompleteRequest) -> AutocompleteResponse:
    """
    Get AI-powered text completion suggestions.

    Args:
        request: AutocompleteRequest with prefix text

    Returns:
        AutocompleteResponse with suggested completion

    Raises:
        HTTPException: If request validation fails
    """
    try:
        # Use Ollama client directly with timeout
        client = ollama.AsyncClient(host=settings.ollama_base_url)

        # Check if we need to capitalize (after sentence-ending punctuation)
        should_capitalize = False
        if request.prefix:
            # Look for sentence-ending punctuation followed by space
            stripped = request.prefix.rstrip()
            if stripped and stripped[-1] in '.!?':
                should_capitalize = True

        # Create a better prompt with context
        if request.context:
            prompt = (
                f"Given the context: {request.context}\n\n"
                f"Continue this text naturally with 5-10 words: {request.prefix}\n\n"
                f"Rules:\n"
                f"- Be contextually relevant\n"
                f"- Write only the next few words, no explanations\n"
                f"- Match the writing style\n"
                f"- {'Start with a capital letter' if should_capitalize else 'Continue naturally'}"
            )
        else:
            prompt = (
                f"Continue this text naturally with just a few words: {request.prefix}\n\n"
                f"Rules:\n"
                f"- Write only the completion, no explanations\n"
                f"- {'Start with a capital letter' if should_capitalize else 'Continue naturally'}\n"
                f"- Be concise and relevant"
            )

        # Call Ollama with timeout and token limit
        try:
            response = await asyncio.wait_for(
                client.generate(
                    model=settings.ollama_fast_model,
                    prompt=prompt,
                    stream=False,
                    options={
                        "temperature": 0.4,  # Slightly higher for creativity
                        "num_predict": 25,  # Slightly more tokens
                    },
                ),
                timeout=5.0  # 5 second timeout
            )

            completion = response.get("response", "").strip()

            # Clean up completion
            if not completion:
                return AutocompleteResponse(completion="")

            # Remove common prefixes that LLMs add
            for prefix in ["...", ".. ", ". ", "- "]:
                if completion.startswith(prefix):
                    completion = completion[len(prefix):].strip()
                    break

            # Don't return completion if it just repeats the prefix
            if completion.lower().startswith(request.prefix.lower()):
                completion = completion[len(request.prefix):].strip()

            # Capitalize first letter if needed
            if should_capitalize and completion and completion[0].islower():
                completion = completion[0].upper() + completion[1:]

            # Limit completion length to 100 characters
            if len(completion) > 100:
                # Cut at the last complete word within 100 chars
                completion = completion[:100]
                last_space = completion.rfind(' ')
                if last_space > 0:
                    completion = completion[:last_space]

            logger.info(f"Autocomplete for '{request.prefix[:50]}...' -> '{completion}'")
            return AutocompleteResponse(completion=completion)

        except asyncio.TimeoutError:
            logger.warning(f"Autocomplete timeout for: {request.prefix[:50]}")
            return AutocompleteResponse(completion="")

    except Exception as e:
        # Log error but return empty completion for graceful degradation
        logger.error(f"Autocomplete error: {str(e)}", exc_info=True)
        return AutocompleteResponse(completion="")
