"""
Knowledge Evolution Timeline Service

Tracks how user's understanding of topics changes over time by analyzing
conversation history and showing conceptual evolution.

Innovation: Visualizes learning journey by comparing past vs. current understanding,
highlighting breakthroughs and corrected misconceptions.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConceptualSnapshot:
    """Represents user's understanding of a topic at a specific point in time."""

    def __init__(
        self,
        timestamp: datetime,
        topic: str,
        understanding_summary: str,
        key_concepts_known: List[str],
        misconceptions: List[str],
        confidence_level: float,  # 0.0-1.0
        questions_asked: List[str],
        source_conversation_id: str,
    ):
        self.timestamp = timestamp
        self.topic = topic
        self.understanding_summary = understanding_summary
        self.key_concepts_known = key_concepts_known
        self.misconceptions = misconceptions
        self.confidence_level = confidence_level
        self.questions_asked = questions_asked
        self.source_conversation_id = source_conversation_id


class ConceptualEvolution:
    """Represents how understanding of a topic evolved between two points in time."""

    def __init__(
        self,
        topic: str,
        from_snapshot: ConceptualSnapshot,
        to_snapshot: ConceptualSnapshot,
        concepts_learned: List[str],
        misconceptions_corrected: List[str],
        new_misconceptions: List[str],
        confidence_change: float,
        breakthrough_moments: List[str],
        evolution_summary: str,
    ):
        self.topic = topic
        self.from_snapshot = from_snapshot
        self.to_snapshot = to_snapshot
        self.concepts_learned = concepts_learned
        self.misconceptions_corrected = misconceptions_corrected
        self.new_misconceptions = new_misconceptions
        self.confidence_change = confidence_change
        self.breakthrough_moments = breakthrough_moments
        self.evolution_summary = evolution_summary


class KnowledgeEvolutionService:
    """Service for tracking and analyzing knowledge evolution over time."""

    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def create_conceptual_snapshot(
        self,
        topic: str,
        conversation_messages: List[Dict[str, str]],
        conversation_id: str,
        timestamp: datetime,
        model: str = "qwen2.5:14b",
    ) -> ConceptualSnapshot:
        """
        Create a snapshot of user's current understanding of a topic.

        Args:
            topic: The topic to analyze understanding for
            conversation_messages: Messages from the conversation
            conversation_id: ID of the conversation
            timestamp: When this snapshot was taken
            model: LLM model to use

        Returns:
            ConceptualSnapshot capturing current understanding
        """
        try:
            # Build snapshot analysis prompt
            snapshot_prompt = self._build_snapshot_prompt(
                topic, conversation_messages
            )

            # Generate snapshot using LLM
            response = await self.llm_service.generate_answer(
                query=f"Analyze understanding of: {topic}",
                context=self._format_conversation_context(conversation_messages),
                conversation_history=[],
                model=model,
                temperature=0.3,  # Lower temp for consistent analysis
                system_prompt=snapshot_prompt,
            )

            # Parse response into snapshot
            snapshot = self._parse_snapshot(
                response, topic, timestamp, conversation_id
            )

            return snapshot

        except Exception as e:
            logger.error(f"Error creating conceptual snapshot: {e}", exc_info=True)
            # Return minimal snapshot
            return ConceptualSnapshot(
                timestamp=timestamp,
                topic=topic,
                understanding_summary="Unable to analyze understanding",
                key_concepts_known=[],
                misconceptions=[],
                confidence_level=0.5,
                questions_asked=[],
                source_conversation_id=conversation_id,
            )

    def _build_snapshot_prompt(
        self, topic: str, conversation_messages: List[Dict[str, str]]
    ) -> str:
        """Build the system prompt for snapshot analysis."""

        return f"""You are a learning analyst. Based on this conversation about "{topic}", analyze the user's current understanding.

ANALYSIS FRAMEWORK:
1. What concepts does the user demonstrate understanding of?
2. What misconceptions or incorrect beliefs do they show?
3. What is their confidence level (0.0-1.0)?
4. What questions did they ask that reveal their knowledge gaps?

RESPONSE FORMAT (use exactly this format):
UNDERSTANDING: [2-3 sentence summary of their current grasp of the topic]
KEY_CONCEPTS: [comma-separated list of concepts they understand]
MISCONCEPTIONS: [comma-separated list of incorrect beliefs, or "None detected"]
CONFIDENCE: [0.0-1.0, where 1.0 is expert-level]
QUESTIONS_ASKED: [key questions they asked that reveal understanding level]

EXAMPLE:
Topic: "Transformer Architecture"

UNDERSTANDING: User has basic grasp of attention mechanism but struggles with multi-head attention details. They understand the high-level architecture (encoder-decoder) but are unclear on why self-attention is computed multiple times in parallel.

KEY_CONCEPTS: attention mechanism, encoder-decoder, sequence-to-sequence, positional encoding

MISCONCEPTIONS: Believes each attention head learns the same thing (they actually learn different aspects), thinks attention is only computed once per layer

CONFIDENCE: 0.4

QUESTIONS_ASKED: What is multi-head attention? Why not just use one attention head? How are the heads combined?"""

    def _format_conversation_context(
        self, conversation_messages: List[Dict[str, str]]
    ) -> str:
        """Format conversation messages for context."""
        formatted = []
        for msg in conversation_messages[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:500]  # Limit length
            formatted.append(f"{role.capitalize()}: {content}")
        return "\n\n".join(formatted)

    def _parse_snapshot(
        self,
        response: str,
        topic: str,
        timestamp: datetime,
        conversation_id: str,
    ) -> ConceptualSnapshot:
        """Parse LLM response into ConceptualSnapshot."""

        try:
            # Extract fields
            understanding = self._extract_field(response, "UNDERSTANDING:")
            key_concepts_str = self._extract_field(response, "KEY_CONCEPTS:")
            misconceptions_str = self._extract_field(response, "MISCONCEPTIONS:")
            confidence_str = self._extract_field(response, "CONFIDENCE:")
            questions_str = self._extract_field(response, "QUESTIONS_ASKED:")

            # Parse lists
            key_concepts = [c.strip() for c in key_concepts_str.split(",") if c.strip()]

            misconceptions = []
            if misconceptions_str.lower() != "none detected":
                misconceptions = [
                    m.strip() for m in misconceptions_str.split(",") if m.strip()
                ]

            # Parse confidence
            try:
                confidence = float(confidence_str.split()[0])
                confidence = max(0.0, min(1.0, confidence))
            except:
                confidence = 0.5

            # Extract questions
            questions = [q.strip() for q in questions_str.split("?") if q.strip()]
            questions = [q + "?" for q in questions]  # Add back question marks

            return ConceptualSnapshot(
                timestamp=timestamp,
                topic=topic,
                understanding_summary=understanding,
                key_concepts_known=key_concepts,
                misconceptions=misconceptions,
                confidence_level=confidence,
                questions_asked=questions,
                source_conversation_id=conversation_id,
            )

        except Exception as e:
            logger.error(f"Error parsing snapshot: {e}")
            return ConceptualSnapshot(
                timestamp=timestamp,
                topic=topic,
                understanding_summary="Unable to parse understanding",
                key_concepts_known=[],
                misconceptions=[],
                confidence_level=0.5,
                questions_asked=[],
                source_conversation_id=conversation_id,
            )

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from formatted text."""
        try:
            start_idx = text.find(field_name)
            if start_idx == -1:
                return ""

            start_idx += len(field_name)
            remaining_text = text[start_idx:].strip()

            field_markers = [
                "UNDERSTANDING:",
                "KEY_CONCEPTS:",
                "MISCONCEPTIONS:",
                "CONFIDENCE:",
                "QUESTIONS_ASKED:",
            ]

            end_idx = len(remaining_text)
            for marker in field_markers:
                marker_pos = remaining_text.find(marker)
                if marker_pos > 0 and marker_pos < end_idx:
                    end_idx = marker_pos

            value = remaining_text[:end_idx].strip()
            return value

        except Exception as e:
            logger.error(f"Error extracting field {field_name}: {e}")
            return ""

    async def analyze_evolution(
        self,
        topic: str,
        earlier_snapshot: ConceptualSnapshot,
        later_snapshot: ConceptualSnapshot,
        model: str = "qwen2.5:14b",
    ) -> ConceptualEvolution:
        """
        Analyze how understanding evolved between two snapshots.

        Args:
            topic: The topic being analyzed
            earlier_snapshot: Earlier conceptual snapshot
            later_snapshot: More recent conceptual snapshot
            model: LLM model to use

        Returns:
            ConceptualEvolution showing changes in understanding
        """
        try:
            # Build evolution analysis prompt
            evolution_prompt = f"""You are a learning progress analyst. Compare these two snapshots of understanding to identify growth and changes.

EARLIER SNAPSHOT ({earlier_snapshot.timestamp.strftime('%Y-%m-%d')}):
Understanding: {earlier_snapshot.understanding_summary}
Concepts Known: {', '.join(earlier_snapshot.key_concepts_known)}
Misconceptions: {', '.join(earlier_snapshot.misconceptions) if earlier_snapshot.misconceptions else 'None'}
Confidence: {earlier_snapshot.confidence_level}

LATER SNAPSHOT ({later_snapshot.timestamp.strftime('%Y-%m-%d')}):
Understanding: {later_snapshot.understanding_summary}
Concepts Known: {', '.join(later_snapshot.key_concepts_known)}
Misconceptions: {', '.join(later_snapshot.misconceptions) if later_snapshot.misconceptions else 'None'}
Confidence: {later_snapshot.confidence_level}

Analyze the evolution in this format:
CONCEPTS_LEARNED: [new concepts in later snapshot]
MISCONCEPTIONS_CORRECTED: [misconceptions from earlier that are gone in later]
NEW_MISCONCEPTIONS: [new misconceptions in later snapshot]
BREAKTHROUGH_MOMENTS: [key insights or "aha" moments, if any]
SUMMARY: [2-3 sentence summary of the learning journey between these snapshots]"""

            # Generate evolution analysis
            response = await self.llm_service.generate_answer(
                query=f"Analyze evolution of understanding: {topic}",
                context="",
                conversation_history=[],
                model=model,
                temperature=0.3,
            )

            # Parse evolution response
            evolution = self._parse_evolution(
                response, topic, earlier_snapshot, later_snapshot
            )

            return evolution

        except Exception as e:
            logger.error(f"Error analyzing evolution: {e}", exc_info=True)
            # Return minimal evolution
            return ConceptualEvolution(
                topic=topic,
                from_snapshot=earlier_snapshot,
                to_snapshot=later_snapshot,
                concepts_learned=[],
                misconceptions_corrected=[],
                new_misconceptions=[],
                confidence_change=later_snapshot.confidence_level
                - earlier_snapshot.confidence_level,
                breakthrough_moments=[],
                evolution_summary="Unable to analyze evolution",
            )

    def _parse_evolution(
        self,
        response: str,
        topic: str,
        earlier_snapshot: ConceptualSnapshot,
        later_snapshot: ConceptualSnapshot,
    ) -> ConceptualEvolution:
        """Parse evolution analysis response."""

        try:
            # Extract fields
            concepts_learned_str = self._extract_field(response, "CONCEPTS_LEARNED:")
            corrected_str = self._extract_field(
                response, "MISCONCEPTIONS_CORRECTED:"
            )
            new_misconceptions_str = self._extract_field(
                response, "NEW_MISCONCEPTIONS:"
            )
            breakthroughs_str = self._extract_field(response, "BREAKTHROUGH_MOMENTS:")
            summary = self._extract_field(response, "SUMMARY:")

            # Parse lists
            concepts_learned = [
                c.strip() for c in concepts_learned_str.split(",") if c.strip()
            ]
            misconceptions_corrected = [
                m.strip() for m in corrected_str.split(",") if m.strip()
            ]
            new_misconceptions = [
                m.strip() for m in new_misconceptions_str.split(",") if m.strip()
            ]
            breakthrough_moments = [
                b.strip().lstrip("0123456789.-• ")
                for b in breakthroughs_str.split("\n")
                if b.strip()
            ]

            # Calculate confidence change
            confidence_change = (
                later_snapshot.confidence_level - earlier_snapshot.confidence_level
            )

            return ConceptualEvolution(
                topic=topic,
                from_snapshot=earlier_snapshot,
                to_snapshot=later_snapshot,
                concepts_learned=concepts_learned,
                misconceptions_corrected=misconceptions_corrected,
                new_misconceptions=new_misconceptions,
                confidence_change=confidence_change,
                breakthrough_moments=breakthrough_moments,
                evolution_summary=summary,
            )

        except Exception as e:
            logger.error(f"Error parsing evolution: {e}")
            return ConceptualEvolution(
                topic=topic,
                from_snapshot=earlier_snapshot,
                to_snapshot=later_snapshot,
                concepts_learned=[],
                misconceptions_corrected=[],
                new_misconceptions=[],
                confidence_change=0.0,
                breakthrough_moments=[],
                evolution_summary="Unable to parse evolution",
            )

    def generate_thought_diff(
        self, earlier_snapshot: ConceptualSnapshot, later_snapshot: ConceptualSnapshot
    ) -> Dict[str, any]:
        """
        Generate a "thought diff" showing changes in understanding.

        Similar to git diff, but for concepts.

        Args:
            earlier_snapshot: Earlier understanding
            later_snapshot: Later understanding

        Returns:
            Dict with added/removed/modified concepts
        """
        earlier_concepts = set(earlier_snapshot.key_concepts_known)
        later_concepts = set(later_snapshot.key_concepts_known)

        added_concepts = list(later_concepts - earlier_concepts)
        removed_concepts = list(earlier_concepts - later_concepts)
        retained_concepts = list(earlier_concepts & later_concepts)

        earlier_misconceptions = set(earlier_snapshot.misconceptions)
        later_misconceptions = set(later_snapshot.misconceptions)

        corrected = list(earlier_misconceptions - later_misconceptions)
        new_mistakes = list(later_misconceptions - earlier_misconceptions)

        return {
            "added_concepts": added_concepts,
            "removed_concepts": removed_concepts,
            "retained_concepts": retained_concepts,
            "misconceptions_corrected": corrected,
            "new_misconceptions": new_mistakes,
            "confidence_delta": later_snapshot.confidence_level
            - earlier_snapshot.confidence_level,
            "time_elapsed": (
                later_snapshot.timestamp - earlier_snapshot.timestamp
            ).days,
        }
