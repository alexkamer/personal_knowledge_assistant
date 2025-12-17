"""
Socratic Learning Mode Service

Instead of answering directly, guides users to discover answers through questioning.
Innovation: Helps users learn deeply through self-discovery rather than passive consumption.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SocraticService:
    """Service for generating Socratic-style questioning responses."""

    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def generate_socratic_response(
        self,
        user_question: str,
        context: str,
        conversation_history: List[Dict[str, str]],
        model: str = "qwen2.5:14b",
    ) -> str:
        """
        Generate a Socratic response that guides the user to discover the answer
        through questions rather than directly answering.

        Args:
            user_question: The user's original question
            context: RAG context from knowledge base
            conversation_history: Previous conversation messages
            model: LLM model to use

        Returns:
            A Socratic response that asks guiding questions
        """
        try:
            # Build Socratic system prompt
            socratic_prompt = self._build_socratic_prompt(
                user_question, context, conversation_history
            )

            # Generate response using LLM
            response = await self.llm_service.generate_answer(
                query=user_question,
                context=context,
                conversation_history=conversation_history,
                model=model,
                temperature=0.8,  # Higher temp for more diverse questions
                system_prompt=socratic_prompt,
            )

            return response

        except Exception as e:
            logger.error(f"Error generating Socratic response: {e}", exc_info=True)
            # Fallback to a generic Socratic question
            return self._generate_fallback_question(user_question)

    def _build_socratic_prompt(
        self,
        user_question: str,
        context: str,
        conversation_history: List[Dict[str, str]],
    ) -> str:
        """Build the system prompt for Socratic mode."""

        return """You are a Socratic teacher. Your role is to guide students to discover answers themselves through thoughtful questioning, NOT to provide direct answers.

RULES FOR SOCRATIC TEACHING:
1. NEVER directly answer the question - always respond with guiding questions
2. Ask questions that help the student break down the problem
3. Start with foundational concepts and build up gradually
4. Use analogies and concrete examples to make abstract ideas tangible
5. If the student is stuck, ask simpler questions to establish a foundation
6. Encourage the student to articulate their thinking
7. Validate correct reasoning and gently redirect misconceptions
8. Be patient and encouraging - learning through discovery takes time

QUESTIONING STRATEGIES:
- "What do you already know about...?"
- "Can you think of a similar situation where...?"
- "What would happen if...?"
- "How would you explain X to someone who's never heard of it?"
- "What's the relationship between A and B?"
- "Can you break this down into smaller parts?"

EXAMPLE INTERACTION:
Student: "What is recursion?"
Socratic Teacher: "Great question! Let's explore this together. Think about a Russian doll - you know, the ones that nest inside each other. What pattern do you notice when you open each layer? And how might that relate to how a function could work?"

Student: "Each doll contains a smaller version of itself?"
Socratic Teacher: "Exactly! Now, imagine a function that needs to process a list. If the list is too big to handle at once, what might be a way to break it down using that same 'nested' pattern you just described?"

Your goal: Help the student reach understanding through their own reasoning, not by being told the answer."""

    def _generate_fallback_question(self, user_question: str) -> str:
        """Generate a fallback Socratic question when LLM fails."""

        return f"""Great question! Before I guide you to the answer, let's start with what you already know.

What concepts or ideas come to mind when you think about this question? Even if you're not sure, share your initial thoughts - there are no wrong answers at this stage of exploration!"""

    def should_reveal_answer(
        self,
        conversation_history: List[Dict[str, str]],
        threshold: int = 5,
    ) -> bool:
        """
        Determine if enough Socratic exchanges have happened and it's time
        to reveal the answer or give more direct guidance.

        Args:
            conversation_history: Previous conversation messages
            threshold: Number of exchanges before offering direct answer

        Returns:
            True if it's time to offer more direct help
        """
        # Count user messages (questions/responses) in current topic
        user_messages = [
            msg for msg in conversation_history if msg.get("role") == "user"
        ]

        return len(user_messages) >= threshold

    async def generate_progressive_hint(
        self,
        user_question: str,
        context: str,
        conversation_history: List[Dict[str, str]],
        hint_level: int,
        model: str = "qwen2.5:14b",
    ) -> str:
        """
        Generate progressively more direct hints as the user struggles.

        Args:
            user_question: The original question
            context: RAG context
            conversation_history: Previous messages
            hint_level: 1=very subtle, 2=moderate, 3=quite direct, 4=almost the answer
            model: LLM model to use

        Returns:
            A hint at the specified directness level
        """
        try:
            hint_prompts = {
                1: "Provide a very subtle hint by asking about a related foundational concept.",
                2: "Provide a moderate hint by suggesting a specific direction to explore.",
                3: "Provide a direct hint by outlining the key steps needed.",
                4: "Provide the answer but frame it as 'Here's how someone might approach this...'",
            }

            prompt = f"""You are helping a student who is working through: "{user_question}"

They've been trying, but are struggling. Provide a hint at level {hint_level}/4.

Level {hint_level} guidance: {hint_prompts.get(hint_level, hint_prompts[2])}

Context from their knowledge base:
{context[:500]}

Previous attempts:
{self._format_recent_history(conversation_history)}

Generate your hint:"""

            response = await self.llm_service.generate_answer(
                query=prompt,
                context=context,
                conversation_history=[],  # Don't include full history
                model=model,
                temperature=0.7,
                system_prompt="You are a patient tutor providing scaffolded hints.",
            )

            return response

        except Exception as e:
            logger.error(f"Error generating progressive hint: {e}", exc_info=True)
            return "Let's take a step back. What's the simplest part of this problem you feel confident about?"

    def _format_recent_history(
        self, conversation_history: List[Dict[str, str]], limit: int = 3
    ) -> str:
        """Format recent conversation history for context."""
        recent = conversation_history[-limit * 2 :] if conversation_history else []
        formatted = []

        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Limit length
            formatted.append(f"{role.capitalize()}: {content}")

        return "\n".join(formatted) if formatted else "No previous attempts."
