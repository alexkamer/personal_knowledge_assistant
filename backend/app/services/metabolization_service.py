"""
Cognitive Metabolization Service

Transforms passive content consumption into active learning by generating
comprehension questions and tracking engagement with material.

Innovation: Ensures users truly understand content before marking it as "learned"
by requiring active recall and reflection.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetabolizationQuestion:
    """Represents a comprehension question for content."""

    def __init__(
        self,
        question: str,
        question_type: str,  # "recall", "comprehension", "application", "synthesis"
        difficulty: str,  # "easy", "medium", "hard"
        key_concepts: List[str],
        expected_answer_hints: str,
    ):
        self.question = question
        self.question_type = question_type
        self.difficulty = difficulty
        self.key_concepts = key_concepts
        self.expected_answer_hints = expected_answer_hints


class MetabolizationScore:
    """Tracks user's metabolization progress for a piece of content."""

    def __init__(
        self,
        content_id: str,
        content_type: str,  # "note", "document", "youtube"
        comprehension_score: float,  # 0.0-1.0
        questions_answered: int,
        total_questions: int,
        key_concepts_grasped: List[str],
        areas_for_review: List[str],
        metabolization_level: str,  # "not_started", "in_progress", "metabolized"
        last_interaction: datetime,
    ):
        self.content_id = content_id
        self.content_type = content_type
        self.comprehension_score = comprehension_score
        self.questions_answered = questions_answered
        self.total_questions = total_questions
        self.key_concepts_grasped = key_concepts_grasped
        self.areas_for_review = areas_for_review
        self.metabolization_level = metabolization_level
        self.last_interaction = last_interaction


class MetabolizationService:
    """Service for generating comprehension questions and tracking learning progress."""

    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def generate_comprehension_questions(
        self,
        content: str,
        content_type: str,
        content_title: str,
        num_questions: int = 3,
        model: str = "qwen2.5:14b",
    ) -> List[MetabolizationQuestion]:
        """
        Generate comprehension questions for content to test understanding.

        Args:
            content: The content text to generate questions from
            content_type: Type of content (note/document/youtube)
            content_title: Title of the content
            num_questions: Number of questions to generate (default: 3)
            model: LLM model to use

        Returns:
            List of MetabolizationQuestion objects
        """
        try:
            # Build question generation prompt
            question_prompt = self._build_question_prompt(
                content, content_title, num_questions
            )

            # Generate questions using LLM
            response = await self.llm_service.generate_answer(
                query=f"Generate {num_questions} comprehension questions for: {content_title}",
                context=content[:2000],  # Limit context size
                conversation_history=[],
                model=model,
                temperature=0.7,  # Some creativity for diverse questions
                system_prompt=question_prompt,
            )

            # Parse response into question objects
            questions = self._parse_questions(response)

            return questions

        except Exception as e:
            logger.error(f"Error generating comprehension questions: {e}", exc_info=True)
            # Return fallback questions
            return self._generate_fallback_questions(content_title)

    def _build_question_prompt(
        self, content: str, content_title: str, num_questions: int
    ) -> str:
        """Build the system prompt for question generation."""

        return f"""You are a learning assessment designer. Generate {num_questions} comprehension questions that test true understanding of the content, not just memorization.

QUESTION TYPES (use a mix):
1. RECALL: Test if user remembers key facts ("What is X?")
2. COMPREHENSION: Test if user understands concepts ("Explain why X works")
3. APPLICATION: Test if user can apply knowledge ("How would you use X in Y scenario?")
4. SYNTHESIS: Test if user can connect ideas ("How does X relate to Z?")

GUIDELINES:
- Questions should require active thinking, not passive recall
- Vary difficulty (1 easy, 1-2 medium, 0-1 hard)
- Focus on key concepts, not trivial details
- Questions should be answerable based on the content
- Avoid yes/no questions

RESPONSE FORMAT (use exactly this format):
Q1:
QUESTION: [the question text]
TYPE: [recall/comprehension/application/synthesis]
DIFFICULTY: [easy/medium/hard]
KEY_CONCEPTS: [comma-separated concepts being tested]
HINTS: [brief hints about what a good answer should include]

Q2:
...

EXAMPLE:
Content Title: "Transformer Architecture"

Q1:
QUESTION: What problem does the attention mechanism solve in neural networks?
TYPE: comprehension
DIFFICULTY: medium
KEY_CONCEPTS: attention mechanism, sequence modeling, context
HINTS: Good answer should mention: handling variable-length sequences, computing relevance between elements, avoiding sequential processing limitations

Q2:
QUESTION: How would you modify a Transformer to handle extremely long documents (100k+ tokens)?
TYPE: application
DIFFICULTY: hard
KEY_CONCEPTS: transformer limitations, memory complexity, architectural modifications
HINTS: Should discuss: quadratic attention complexity, techniques like sparse attention or hierarchical processing, trade-offs between efficiency and accuracy"""

    def _parse_questions(self, response: str) -> List[MetabolizationQuestion]:
        """Parse LLM response into MetabolizationQuestion objects."""

        questions = []

        # Split by "Q" markers
        question_sections = response.split("Q")[1:]  # Skip empty first element

        for section in question_sections:
            try:
                # Extract fields
                question_text = self._extract_field(section, "QUESTION:")
                q_type = self._extract_field(section, "TYPE:").lower()
                difficulty = self._extract_field(section, "DIFFICULTY:").lower()
                key_concepts_str = self._extract_field(section, "KEY_CONCEPTS:")
                hints = self._extract_field(section, "HINTS:")

                # Parse key concepts
                key_concepts = [
                    c.strip() for c in key_concepts_str.split(",") if c.strip()
                ]

                # Validate fields
                if q_type not in ["recall", "comprehension", "application", "synthesis"]:
                    q_type = "comprehension"

                if difficulty not in ["easy", "medium", "hard"]:
                    difficulty = "medium"

                # Create question object
                question = MetabolizationQuestion(
                    question=question_text,
                    question_type=q_type,
                    difficulty=difficulty,
                    key_concepts=key_concepts,
                    expected_answer_hints=hints,
                )

                questions.append(question)

            except Exception as e:
                logger.error(f"Error parsing question section: {e}")
                continue

        return questions

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
                "QUESTION:",
                "TYPE:",
                "DIFFICULTY:",
                "KEY_CONCEPTS:",
                "HINTS:",
                "Q",
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

    def _generate_fallback_questions(
        self, content_title: str
    ) -> List[MetabolizationQuestion]:
        """Generate generic fallback questions when LLM fails."""

        return [
            MetabolizationQuestion(
                question=f"What are the main concepts covered in '{content_title}'?",
                question_type="recall",
                difficulty="easy",
                key_concepts=["main concepts"],
                expected_answer_hints="List 2-3 key ideas or topics",
            ),
            MetabolizationQuestion(
                question=f"How would you explain '{content_title}' to someone unfamiliar with the topic?",
                question_type="comprehension",
                difficulty="medium",
                key_concepts=["explanation", "understanding"],
                expected_answer_hints="Provide a clear, simple explanation in your own words",
            ),
            MetabolizationQuestion(
                question=f"What questions do you still have about '{content_title}'?",
                question_type="synthesis",
                difficulty="easy",
                key_concepts=["reflection", "gaps"],
                expected_answer_hints="Identify areas where you'd like more clarity",
            ),
        ]

    async def evaluate_answer(
        self,
        question: MetabolizationQuestion,
        user_answer: str,
        content_context: str,
        model: str = "qwen2.5:14b",
    ) -> Dict[str, any]:
        """
        Evaluate user's answer to a comprehension question.

        Args:
            question: The question that was asked
            user_answer: The user's response
            content_context: Original content for reference
            model: LLM model to use

        Returns:
            Dict with evaluation results (score, feedback, concepts_demonstrated)
        """
        try:
            # Build evaluation prompt
            eval_prompt = f"""You are an educational evaluator. Assess the user's answer to this comprehension question.

Question: {question.question}
Expected Key Concepts: {', '.join(question.key_concepts)}
Hints for Good Answer: {question.expected_answer_hints}

User's Answer: {user_answer}

Provide evaluation in this format:
SCORE: [0.0-1.0, where 1.0 is excellent understanding]
CONCEPTS_DEMONSTRATED: [comma-separated list of concepts the user showed understanding of]
FEEDBACK: [constructive feedback - what they got right, what to improve]
SUGGESTIONS: [2-3 specific suggestions for deeper understanding]"""

            # Generate evaluation
            response = await self.llm_service.generate_answer(
                query="Evaluate this answer",
                context=content_context[:1000],
                conversation_history=[],
                model=model,
                temperature=0.3,  # Lower temp for consistent evaluation
                system_prompt=eval_prompt,
            )

            # Parse evaluation response
            evaluation = self._parse_evaluation(response)

            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating answer: {e}", exc_info=True)
            # Return neutral evaluation
            return {
                "score": 0.5,
                "concepts_demonstrated": [],
                "feedback": "Thank you for your answer. Keep engaging with the material to deepen your understanding.",
                "suggestions": [
                    "Review the key concepts",
                    "Try explaining it in different words",
                ],
            }

    def _parse_evaluation(self, response: str) -> Dict[str, any]:
        """Parse evaluation response from LLM."""

        try:
            # Extract score
            score_str = self._extract_field(response, "SCORE:")
            score = float(score_str.split()[0])  # Get first number
            score = max(0.0, min(1.0, score))  # Clamp to 0-1

            # Extract concepts
            concepts_str = self._extract_field(response, "CONCEPTS_DEMONSTRATED:")
            concepts = [c.strip() for c in concepts_str.split(",") if c.strip()]

            # Extract feedback
            feedback = self._extract_field(response, "FEEDBACK:")

            # Extract suggestions
            suggestions_str = self._extract_field(response, "SUGGESTIONS:")
            suggestions = [
                s.strip().lstrip("0123456789.-• ")
                for s in suggestions_str.split("\n")
                if s.strip()
            ][:3]  # Limit to 3 suggestions

            return {
                "score": score,
                "concepts_demonstrated": concepts,
                "feedback": feedback,
                "suggestions": suggestions,
            }

        except Exception as e:
            logger.error(f"Error parsing evaluation: {e}")
            return {
                "score": 0.5,
                "concepts_demonstrated": [],
                "feedback": response[:200],  # Use first part of response
                "suggestions": [],
            }

    def calculate_metabolization_score(
        self, evaluations: List[Dict[str, any]]
    ) -> MetabolizationScore:
        """
        Calculate overall metabolization score from multiple evaluations.

        Args:
            evaluations: List of evaluation results from answered questions

        Returns:
            MetabolizationScore object with overall assessment
        """
        if not evaluations:
            return MetabolizationScore(
                content_id="",
                content_type="",
                comprehension_score=0.0,
                questions_answered=0,
                total_questions=0,
                key_concepts_grasped=[],
                areas_for_review=[],
                metabolization_level="not_started",
                last_interaction=datetime.now(),
            )

        # Calculate average score
        avg_score = sum(e["score"] for e in evaluations) / len(evaluations)

        # Collect all demonstrated concepts
        all_concepts = []
        for e in evaluations:
            all_concepts.extend(e["concepts_demonstrated"])

        # Determine metabolization level
        if avg_score >= 0.8:
            level = "metabolized"
        elif avg_score >= 0.5:
            level = "in_progress"
        else:
            level = "not_started"

        # Areas for review (concepts with low scores)
        areas_for_review = []
        for i, e in enumerate(evaluations):
            if e["score"] < 0.6:
                areas_for_review.extend(e.get("suggestions", []))

        return MetabolizationScore(
            content_id="",  # Set by caller
            content_type="",  # Set by caller
            comprehension_score=avg_score,
            questions_answered=len(evaluations),
            total_questions=len(evaluations),
            key_concepts_grasped=list(set(all_concepts)),
            areas_for_review=list(set(areas_for_review)),
            metabolization_level=level,
            last_interaction=datetime.now(),
        )
