"""
LLM service for interfacing with Ollama local models.
"""
import logging
from typing import AsyncIterator, List, Optional

import ollama

from app.core.config import settings
from app.core.exceptions import ModelNotFoundError, OllamaConnectionError

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
    ) -> str | AsyncIterator[str]:
        """
        Generate an answer using RAG context and conversation history.

        Args:
            query: User's question
            context: Retrieved context from RAG
            conversation_history: Previous messages in conversation
            model: Model to use (defaults to primary)
            stream: Whether to stream the response

        Returns:
            Generated answer as string or async iterator if streaming
        """
        model = model or self.primary_model

        # Build the system prompt
        system_prompt = self._build_system_prompt()

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
                return self._stream_response(model, messages)
            else:
                return await self._generate_response(model, messages)
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

    async def _generate_response(self, model: str, messages: List[dict]) -> str:
        """Generate a complete response (non-streaming)."""
        response = await self.client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
            },
        )

        answer = response["message"]["content"]
        logger.info(f"Generated answer: {len(answer)} characters")
        return answer

    async def generate_follow_up_questions(
        self,
        query: str,
        answer: str,
        context: str,
        model: Optional[str] = None,
    ) -> List[str]:
        """
        Generate 3-4 relevant follow-up questions based on the conversation.

        Args:
            query: The user's original question
            answer: The assistant's answer
            context: The context used to generate the answer
            model: Model to use (defaults to primary)

        Returns:
            List of 3-4 suggested follow-up questions
        """
        model = model or self.primary_model

        prompt = f"""Based on this conversation, generate 3-4 relevant follow-up questions that would help the user explore this topic further.

USER QUESTION:
{query}

ASSISTANT ANSWER:
{answer}

CONTEXT AVAILABLE:
{context[:500]}...

Generate 3-4 short, clear follow-up questions (one per line) that:
1. Explore related concepts or details not covered
2. Go deeper into specific aspects mentioned
3. Connect to practical applications or examples
4. Are natural next steps in learning about this topic

Output ONLY the questions, one per line, without numbering or bullet points."""

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
    ) -> AsyncIterator[str]:
        """Stream response chunks as they're generated."""
        async for chunk in await self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
            },
        ):
            if chunk.get("message", {}).get("content"):
                yield chunk["message"]["content"]

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """You are a helpful AI assistant for a personal knowledge management system.

Your role is to answer questions based on the user's notes and documents. You have access to relevant context retrieved from their knowledge base.

Guidelines:
- Answer questions accurately based on the provided context
- If the context doesn't contain enough information, say so clearly
- Cite sources when using specific information from the context
- Be concise but thorough in your explanations
- If asked about something not in the context, acknowledge the limitation
- Maintain a helpful and professional tone

When referencing information, mention the source (e.g., "According to your note on Machine Learning...")"""

    def _build_user_message(self, query: str, context: str) -> str:
        """Build the user message with context."""
        if context:
            return f"""Based on the following context from my knowledge base, please answer my question:

CONTEXT:
{context}

QUESTION:
{query}

Please provide a clear and helpful answer based on the context above."""
        else:
            # No context - this is a general knowledge question
            return f"""QUESTION:
{query}

Please provide a clear and concise answer to this question using your general knowledge."""

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
