"""
LLM service for interfacing with Ollama local models.
"""
import logging
from typing import AsyncIterator, List, Optional

import ollama

from app.core.config import settings
from app.core.exceptions import ModelNotFoundError, OllamaConnectionError
from app.core.retry import retry_with_backoff, ollama_circuit_breaker

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama local LLMs."""

    def __init__(self):
        """Initialize LLM service."""
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.primary_model = settings.ollama_primary_model
        self.timeout = settings.ollama_request_timeout

    async def generate_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[dict]] = None,
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> str | AsyncIterator[str]:
        """
        Generate an answer using RAG context and conversation history.

        Args:
            query: User's question
            context: Retrieved context from RAG
            conversation_history: Previous messages in conversation
            model: Model to use (defaults to primary)
            stream: Whether to stream the response
            temperature: Temperature override for generation
            system_prompt: Custom system prompt override

        Returns:
            Generated answer as string or async iterator if streaming
        """
        model = model or self.primary_model
        temperature = temperature if temperature is not None else 0.7

        # Build the system prompt (use custom if provided)
        system_prompt = system_prompt or self._build_system_prompt()

        # Build the conversation messages
        messages = []

        # Add system message
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add current query with context
        user_message = self._build_user_message(query, context)
        messages.append({"role": "user", "content": user_message})

        logger.info(f"Generating answer with {model} (stream={stream})")
        logger.debug(f"Messages: {len(messages)} messages, last query: {query[:100]}...")

        try:
            if stream:
                return self._stream_response(model, messages, temperature)
            else:
                return await self._generate_response(model, messages, temperature)
        except ollama.ResponseError as e:
            logger.error(f"Ollama response error: {e}")
            if "model" in str(e).lower() and "not found" in str(e).lower():
                raise ModelNotFoundError(model)
            raise OllamaConnectionError(f"Ollama error: {str(e)}")
        except ollama.RequestError as e:
            logger.error(f"Ollama request error: {e}")
            raise OllamaConnectionError("Cannot connect to Ollama. Is it running?")
        except Exception as e:
            logger.error(f"Unexpected error generating answer: {e}")
            raise

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(ollama.RequestError, ollama.ResponseError, Exception),
        circuit_breaker=ollama_circuit_breaker,
    )
    async def _generate_response(self, model: str, messages: List[dict], temperature: float) -> str:
        """Generate a complete response (non-streaming) with retry logic."""
        response = await self.client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": temperature,
                "top_p": 0.9,
            },
        )

        answer = response["message"]["content"]
        logger.info(f"Generated answer: {len(answer)} characters")
        return answer

    @retry_with_backoff(
        max_retries=2,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(ollama.RequestError, ollama.ResponseError, Exception),
        circuit_breaker=ollama_circuit_breaker,
    )
    async def generate_follow_up_questions(
        self,
        query: str,
        answer: str,
        context: str,
        model: Optional[str] = None,
    ) -> List[str]:
        """
        Generate 3-4 relevant follow-up questions based on the conversation with retry logic.

        Args:
            query: The user's original question
            answer: The assistant's answer
            context: The context used to generate the answer
            model: Model to use (defaults to primary)

        Returns:
            List of 3-4 suggested follow-up questions
        """
        model = model or self.primary_model

        prompt = f"""Generate 3-4 natural follow-up questions for this conversation.

USER: {query}
ASSISTANT: {answer}

Requirements:
- Questions must be directly related to what was just discussed
- Keep questions short and conversational
- Focus on practical next steps or clarifications
- Avoid generic questions that don't fit the context

Output ONLY the questions, one per line, no numbering."""

        try:
            response = await self.client.chat(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.8,  # Slightly higher for creativity
                    "top_p": 0.9,
                },
            )

            # Parse the response into individual questions
            questions_text = response["message"]["content"].strip()
            questions = [
                q.strip()
                for q in questions_text.split("\n")
                if q.strip() and len(q.strip()) > 10
            ]

            # Limit to 4 questions max
            questions = questions[:4]

            logger.info(f"Generated {len(questions)} follow-up questions")
            return questions

        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return []  # Return empty list on failure

    async def _stream_response(
        self,
        model: str,
        messages: List[dict],
        temperature: float,
    ) -> AsyncIterator[str]:
        """Stream response chunks as they're generated."""
        async for chunk in await self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            options={
                "temperature": temperature,
                "top_p": 0.9,
            },
        ):
            if chunk.get("message", {}).get("content"):
                yield chunk["message"]["content"]

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """You are a helpful AI assistant for a personal knowledge management system.

Answer questions using conversation history and the user's documents.

Key rules:
- Check conversation history FIRST for context (e.g., "that", "it", pronouns, follow-ups)
- Answer directly without meta-commentary about your process
- Be conversational and concise - avoid robotic phrases like "I'll do my best", "Based on the provided context", "Additionally, reviewing"
- Only mention documents if they're actually relevant to the answer
- If knowledge base context is irrelevant, ignore it completely - don't explain why you're ignoring it
- Cite sources naturally when using specific info (e.g., "Your note on X mentions...")
- If you don't know something, just say "I don't have information about that"

CRITICAL: Users want answers, not explanations of how you're thinking. Be natural and direct."""

    def _build_user_message(self, query: str, context: str) -> str:
        """Build the user message with context."""
        if context:
            return f"""{query}

[Available context from knowledge base:]
{context}"""
        else:
            # No context - this is a general knowledge question or conversation continuation
            return query

    async def list_available_models(self) -> List[dict]:
        """
        List available Ollama models.

        Returns:
            List of available models with metadata
        """
        try:
            response = await self.client.list()
            models = response.get("models", [])
            logger.info(f"Found {len(models)} available models")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def check_model_available(self, model: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model: Model name to check

        Returns:
            True if model is available
        """
        models = await self.list_available_models()
        return any(m["name"] == model for m in models)


# Global instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """
    Get the global LLM service instance.

    Returns:
        LLM service singleton
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
