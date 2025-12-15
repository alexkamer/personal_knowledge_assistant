"""
Custom exceptions and error handlers for the application.
"""
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class KnowledgeAssistantException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class OllamaConnectionError(KnowledgeAssistantException):
    """Raised when Ollama service is unavailable."""

    def __init__(self, message: str = "Unable to connect to Ollama. Please ensure Ollama is running."):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class ModelNotFoundError(KnowledgeAssistantException):
    """Raised when requested LLM model is not available."""

    def __init__(self, model: str):
        super().__init__(
            f"Model '{model}' not found. Please check available models or pull the model first.",
            status.HTTP_404_NOT_FOUND,
        )


class EmbeddingError(KnowledgeAssistantException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str = "Failed to generate embeddings. Please try again."):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class VectorDBError(KnowledgeAssistantException):
    """Raised when vector database operations fail."""

    def __init__(self, message: str = "Vector database operation failed. Please try again."):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentProcessingError(KnowledgeAssistantException):
    """Raised when document processing fails."""

    def __init__(self, message: str = "Failed to process document. Please check the file format."):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


def create_error_response(message: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        message: Human-readable error message
        details: Optional additional error details

    Returns:
        Formatted error response dictionary
    """
    response = {"detail": message}
    if details:
        response["error_details"] = details
    return response


async def knowledge_assistant_exception_handler(
    request: Request, exc: KnowledgeAssistantException
) -> JSONResponse:
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.message),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions with consistent formatting."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(str(exc.detail)),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    # Don't expose internal error details in production
    message = "An unexpected error occurred. Please try again later."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(message),
    )
