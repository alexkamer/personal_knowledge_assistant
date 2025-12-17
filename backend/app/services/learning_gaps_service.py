"""
Learning Gaps Detection Service

Analyzes user questions and conversation history to identify missing foundational
knowledge, then generates personalized learning paths to fill those gaps.

Innovation: Helps users build complete understanding by detecting conceptual prerequisites.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LearningGap:
    """Represents a detected knowledge gap."""

    def __init__(
        self,
        topic: str,
        description: str,
        prerequisite_for: str,
        importance: str,  # "critical", "important", "helpful"
        learning_resources: List[str],
        estimated_time: str,
    ):
        self.topic = topic
        self.description = description
        self.prerequisite_for = prerequisite_for
        self.importance = importance
        self.learning_resources = learning_resources
        self.estimated_time = estimated_time


class LearningPath:
    """Represents a personalized learning path to fill knowledge gaps."""

    def __init__(
        self,
        target_topic: str,
        gaps: List[LearningGap],
        learning_sequence: List[str],
        total_estimated_time: str,
    ):
        self.target_topic = target_topic
        self.gaps = gaps
        self.learning_sequence = learning_sequence
        self.total_estimated_time = total_estimated_time


class LearningGapsService:
    """Service for detecting knowledge gaps and generating learning paths."""

    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def detect_gaps(
        self,
        user_question: str,
        conversation_history: List[Dict[str, str]],
        context: str = "",
        model: str = "qwen2.5:14b",
    ) -> List[LearningGap]:
        """
        Analyze user's question to detect foundational knowledge gaps.

        Args:
            user_question: The user's current question
            conversation_history: Previous conversation messages
            context: RAG context from knowledge base
            model: LLM model to use

        Returns:
            List of detected learning gaps
        """
        try:
            # Build gap detection prompt
            gap_prompt = self._build_gap_detection_prompt(
                user_question, conversation_history, context
            )

            # Generate response using LLM
            response = await self.llm_service.generate_answer(
                query=user_question,
                context=context,
                conversation_history=[],  # Don't include history for analysis
                model=model,
                temperature=0.3,  # Lower temp for more consistent analysis
                system_prompt=gap_prompt,
            )

            # Parse the response into LearningGap objects
            gaps = self._parse_gap_response(response, user_question)

            return gaps

        except Exception as e:
            logger.error(f"Error detecting learning gaps: {e}", exc_info=True)
            return []

    def _build_gap_detection_prompt(
        self,
        user_question: str,
        conversation_history: List[Dict[str, str]],
        context: str,
    ) -> str:
        """Build the system prompt for gap detection."""

        return """You are a learning diagnostician. Analyze the user's question to identify foundational knowledge gaps that would help them understand the topic more deeply.

ANALYSIS FRAMEWORK:
1. What concepts does the user's question assume they understand?
2. What foundational knowledge is required to fully grasp the topic?
3. Are there prerequisite concepts they might be missing?
4. What would help them build from basics to advanced understanding?

For each gap you identify, provide:
- TOPIC: The missing foundational concept
- DESCRIPTION: What this concept is and why it matters
- PREREQUISITE_FOR: How it relates to their question
- IMPORTANCE: critical/important/helpful
- RESOURCES: Where they can learn it (from knowledge base or general guidance)
- TIME: Estimated learning time (e.g., "5 minutes", "30 minutes", "2 hours")

RESPONSE FORMAT (use exactly this format):
GAP 1:
TOPIC: [concept name]
DESCRIPTION: [clear explanation]
PREREQUISITE_FOR: [how it relates to user's question]
IMPORTANCE: [critical/important/helpful]
RESOURCES: [learning sources]
TIME: [estimated time]

GAP 2:
...

RULES:
- Only identify gaps that are truly foundational (not tangential topics)
- Prioritize by importance (critical gaps first)
- Be specific and actionable
- If no gaps detected, respond with: "NO_GAPS_DETECTED"

EXAMPLE:
User Question: "How does multi-head attention work in Transformers?"

GAP 1:
TOPIC: Attention Mechanism Basics
DESCRIPTION: Understanding how basic attention computes weighted sums over inputs based on relevance scores. This is the foundation that multi-head attention builds upon.
PREREQUISITE_FOR: Multi-head attention is multiple attention mechanisms running in parallel
IMPORTANCE: critical
RESOURCES: Start with "scaled dot-product attention" in knowledge base
TIME: 15 minutes

GAP 2:
TOPIC: Matrix Operations (Query, Key, Value)
DESCRIPTION: Understanding how Q, K, V matrices transform inputs and compute attention scores through matrix multiplication.
PREREQUISITE_FOR: Each attention head uses separate Q/K/V matrices
IMPORTANCE: important
RESOURCES: Review linear algebra basics and attention mechanism documentation
TIME: 20 minutes"""

    def _parse_gap_response(
        self, response: str, user_question: str
    ) -> List[LearningGap]:
        """Parse LLM response into LearningGap objects."""

        gaps = []

        # Check for no gaps detected
        if "NO_GAPS_DETECTED" in response:
            return gaps

        # Split by "GAP" markers
        gap_sections = response.split("GAP ")[1:]  # Skip empty first element

        for section in gap_sections:
            try:
                # Extract fields
                topic = self._extract_field(section, "TOPIC:")
                description = self._extract_field(section, "DESCRIPTION:")
                prerequisite_for = self._extract_field(section, "PREREQUISITE_FOR:")
                importance = self._extract_field(section, "IMPORTANCE:").lower()
                resources = self._extract_field(section, "RESOURCES:")
                time = self._extract_field(section, "TIME:")

                # Validate importance level
                if importance not in ["critical", "important", "helpful"]:
                    importance = "helpful"

                # Create LearningGap object
                gap = LearningGap(
                    topic=topic,
                    description=description,
                    prerequisite_for=prerequisite_for,
                    importance=importance,
                    learning_resources=[resources],  # Single resource for now
                    estimated_time=time,
                )

                gaps.append(gap)

            except Exception as e:
                logger.error(f"Error parsing gap section: {e}")
                continue

        return gaps

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from formatted text."""
        try:
            # Find field start
            start_idx = text.find(field_name)
            if start_idx == -1:
                return ""

            # Get text after field name
            start_idx += len(field_name)
            remaining_text = text[start_idx:].strip()

            # Find end of field (next field marker or end of text)
            field_markers = [
                "TOPIC:",
                "DESCRIPTION:",
                "PREREQUISITE_FOR:",
                "IMPORTANCE:",
                "RESOURCES:",
                "TIME:",
                "GAP ",
            ]

            end_idx = len(remaining_text)
            for marker in field_markers:
                marker_pos = remaining_text.find(marker)
                if marker_pos > 0 and marker_pos < end_idx:
                    end_idx = marker_pos

            # Extract and clean the value
            value = remaining_text[:end_idx].strip()
            return value

        except Exception as e:
            logger.error(f"Error extracting field {field_name}: {e}")
            return ""

    async def generate_learning_path(
        self,
        user_question: str,
        gaps: List[LearningGap],
        model: str = "qwen2.5:14b",
    ) -> LearningPath:
        """
        Generate a personalized learning path based on detected gaps.

        Args:
            user_question: The user's original question
            gaps: List of detected knowledge gaps
            model: LLM model to use

        Returns:
            LearningPath with sequenced learning steps
        """
        try:
            # Build learning path generation prompt
            gap_summary = "\n".join(
                [
                    f"{i+1}. {gap.topic} ({gap.importance}): {gap.description}"
                    for i, gap in enumerate(gaps)
                ]
            )

            path_prompt = f"""You are a learning path designer. Given these knowledge gaps, create an optimal learning sequence.

Detected Gaps:
{gap_summary}

Target Question: {user_question}

Create a step-by-step learning path that:
1. Orders topics from foundational to advanced
2. Shows dependencies between concepts
3. Provides estimated total learning time
4. Suggests a logical progression

Respond with a numbered sequence (e.g., "1. Learn X → 2. Then Y → 3. Finally Z")"""

            # Generate learning path
            response = await self.llm_service.generate_answer(
                query=path_prompt,
                context="",
                conversation_history=[],
                model=model,
                temperature=0.3,
            )

            # Extract sequence
            learning_sequence = self._parse_learning_sequence(response)

            # Calculate total time
            total_time = self._calculate_total_time(gaps)

            return LearningPath(
                target_topic=user_question,
                gaps=gaps,
                learning_sequence=learning_sequence,
                total_estimated_time=total_time,
            )

        except Exception as e:
            logger.error(f"Error generating learning path: {e}", exc_info=True)
            # Return minimal path
            return LearningPath(
                target_topic=user_question,
                gaps=gaps,
                learning_sequence=[gap.topic for gap in gaps],
                total_estimated_time="Unknown",
            )

    def _parse_learning_sequence(self, response: str) -> List[str]:
        """Parse learning sequence from LLM response."""
        sequence = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            # Look for numbered steps (e.g., "1.", "2.", etc.)
            if line and (
                line[0].isdigit() or line.startswith("-") or line.startswith("•")
            ):
                # Remove numbering and clean up
                step = line.lstrip("0123456789.-•→ ").strip()
                if step:
                    sequence.append(step)

        return sequence

    def _calculate_total_time(self, gaps: List[LearningGap]) -> str:
        """Calculate total estimated learning time from gaps."""
        total_minutes = 0

        for gap in gaps:
            time_str = gap.estimated_time.lower()

            # Parse time strings (e.g., "15 minutes", "2 hours", "1.5 hours")
            if "minute" in time_str:
                try:
                    minutes = int(time_str.split()[0])
                    total_minutes += minutes
                except:
                    pass
            elif "hour" in time_str:
                try:
                    hours = float(time_str.split()[0])
                    total_minutes += int(hours * 60)
                except:
                    pass

        if total_minutes == 0:
            return "Variable"

        # Format total time
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes / 60
            if hours == int(hours):
                return f"{int(hours)} hours"
            else:
                return f"{hours:.1f} hours"
