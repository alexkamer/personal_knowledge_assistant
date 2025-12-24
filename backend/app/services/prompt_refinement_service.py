"""
Service for analyzing and refining image generation prompts.
"""
import json
import logging
import re
from typing import Dict, List, Optional

import ollama

from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptRefinementService:
    """Service for analyzing prompts and generating refinement questions."""

    def __init__(self):
        """Initialize the service with Ollama client."""
        self.ollama_client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.llm_model = "qwen2.5:14b"  # Use primary model for better reasoning
        self.use_dynamic_questions = True  # Toggle for LLM-generated questions

    # Category detection patterns
    CATEGORY_PATTERNS = {
        "person": r"\b(person|man|woman|child|portrait|face|people|human|character)\b",
        "animal": r"\b(cat|dog|bird|animal|pet|wildlife|creature)\b",
        "landscape": r"\b(mountain|landscape|scenery|nature|forest|beach|ocean|desert|sky|sunset|sunrise)\b",
        "object": r"\b(car|building|house|furniture|product|item|tool|machine)\b",
        "food": r"\b(food|meal|dish|cooking|restaurant|cuisine)\b",
        "abstract": r"\b(abstract|pattern|texture|design|art)\b",
    }

    # Question templates by category
    CATEGORY_QUESTIONS = {
        "person": [
            {
                "id": "style",
                "question": "What artistic style?",
                "type": "single-select",
                "options": ["Photorealistic", "Digital art", "Oil painting", "Watercolor", "Cartoon/Anime"],
            },
            {
                "id": "setting",
                "question": "Where is the person?",
                "type": "single-select",
                "options": ["Studio portrait", "Outdoor nature", "Urban environment", "Indoor room", "Fantasy world"],
            },
            {
                "id": "mood",
                "question": "What mood or feeling?",
                "type": "single-select",
                "options": ["Happy/Joyful", "Serious/Professional", "Mysterious", "Dramatic", "Peaceful"],
            },
            {
                "id": "lighting",
                "question": "What kind of lighting?",
                "type": "single-select",
                "options": ["Natural sunlight", "Golden hour", "Dramatic/Moody", "Soft/Studio", "Night/Dark"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., specific clothing, colors, props, expression...",
            },
        ],
        "animal": [
            {
                "id": "style",
                "question": "What artistic style?",
                "type": "single-select",
                "options": ["Photorealistic", "Cute/Cartoon", "Fantasy", "Watercolor", "Digital art"],
            },
            {
                "id": "setting",
                "question": "Where is the animal?",
                "type": "single-select",
                "options": ["Natural habitat", "Studio portrait", "Urban environment", "Home/Indoor", "Fantasy world"],
            },
            {
                "id": "action",
                "question": "What is the animal doing?",
                "type": "single-select",
                "options": ["Posing/Portrait", "Playing", "Sleeping/Resting", "Hunting/Active", "Interacting"],
            },
            {
                "id": "mood",
                "question": "What mood?",
                "type": "single-select",
                "options": ["Cute/Adorable", "Majestic/Regal", "Wild/Fierce", "Peaceful", "Playful/Funny"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., specific colors, accessories, background elements...",
            },
        ],
        "landscape": [
            {
                "id": "style",
                "question": "What artistic style?",
                "type": "single-select",
                "options": ["Photorealistic", "Cinematic", "Painterly/Artistic", "Fantasy", "Minimalist"],
            },
            {
                "id": "time",
                "question": "Time of day?",
                "type": "single-select",
                "options": ["Sunrise/Golden hour", "Midday/Bright", "Sunset/Dusk", "Night/Stars", "Overcast/Moody"],
            },
            {
                "id": "season",
                "question": "What season?",
                "type": "single-select",
                "options": ["Spring/Blooms", "Summer/Lush", "Autumn/Colors", "Winter/Snow", "Any/Timeless"],
            },
            {
                "id": "mood",
                "question": "What atmosphere?",
                "type": "single-select",
                "options": ["Serene/Peaceful", "Dramatic/Epic", "Mysterious/Moody", "Vibrant/Energetic", "Desolate/Lonely"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., specific elements like lake, cabin, wildlife, weather...",
            },
        ],
        "object": [
            {
                "id": "style",
                "question": "What artistic style?",
                "type": "single-select",
                "options": ["Photorealistic", "Product photography", "Technical/Blueprint", "Artistic", "Minimalist"],
            },
            {
                "id": "setting",
                "question": "What setting/background?",
                "type": "single-select",
                "options": ["White studio background", "Natural environment", "Lifestyle/In-use", "Abstract background", "Detailed scene"],
            },
            {
                "id": "lighting",
                "question": "What kind of lighting?",
                "type": "single-select",
                "options": ["Soft/Studio", "Dramatic/Shadows", "Natural sunlight", "Neon/Colorful", "Rim lighting"],
            },
            {
                "id": "angle",
                "question": "What angle/perspective?",
                "type": "single-select",
                "options": ["Straight-on", "45-degree angle", "Top-down", "Close-up detail", "Wide/Environmental"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., specific materials, colors, textures, brand style...",
            },
        ],
        "food": [
            {
                "id": "style",
                "question": "What photographic style?",
                "type": "single-select",
                "options": ["Professional food photography", "Rustic/Homestyle", "Modern/Minimalist", "Editorial/Magazine", "Casual/Lifestyle"],
            },
            {
                "id": "setting",
                "question": "What setting?",
                "type": "single-select",
                "options": ["Clean table/Surface", "Restaurant setting", "Outdoor/Picnic", "Kitchen/Cooking", "Abstract/Artistic"],
            },
            {
                "id": "lighting",
                "question": "What lighting?",
                "type": "single-select",
                "options": ["Natural window light", "Overhead/Flat", "Dramatic/Moody", "Bright/Airy", "Warm/Cozy"],
            },
            {
                "id": "angle",
                "question": "What angle?",
                "type": "single-select",
                "options": ["Top-down (flat lay)", "45-degree angle", "Eye-level/Straight", "Close-up detail", "Wide/Scene"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., garnishes, plating style, props, colors...",
            },
        ],
        "abstract": [
            {
                "id": "style",
                "question": "What abstract style?",
                "type": "single-select",
                "options": ["Geometric patterns", "Fluid/Organic", "Fractal/Mathematical", "Color gradients", "Minimalist"],
            },
            {
                "id": "colors",
                "question": "What color palette?",
                "type": "single-select",
                "options": ["Vibrant/Bold", "Pastel/Soft", "Monochrome", "Warm tones", "Cool tones", "Rainbow/Multi"],
            },
            {
                "id": "mood",
                "question": "What feeling?",
                "type": "single-select",
                "options": ["Calm/Meditative", "Energetic/Dynamic", "Mysterious/Dark", "Cheerful/Bright", "Ethereal/Dreamy"],
            },
            {
                "id": "complexity",
                "question": "How complex?",
                "type": "single-select",
                "options": ["Simple/Minimal", "Moderately detailed", "Highly intricate", "Chaotic/Busy", "Balanced"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., specific shapes, textures, inspirations...",
            },
        ],
        "default": [
            {
                "id": "style",
                "question": "What artistic style?",
                "type": "single-select",
                "options": ["Photorealistic", "Digital art", "Painterly", "Cartoon", "Fantasy", "Minimalist"],
            },
            {
                "id": "mood",
                "question": "What mood or atmosphere?",
                "type": "single-select",
                "options": ["Vibrant/Energetic", "Calm/Peaceful", "Dark/Mysterious", "Bright/Cheerful", "Dramatic"],
            },
            {
                "id": "detail",
                "question": "Level of detail?",
                "type": "single-select",
                "options": ["Highly detailed", "Moderate detail", "Simple/Minimal", "Abstract"],
            },
            {
                "id": "extras",
                "question": "Any additional details? (optional)",
                "type": "text",
                "placeholder": "e.g., specific colors, elements, style references...",
            },
        ],
    }

    def detect_category(self, prompt: str) -> str:
        """
        Detect the primary category of the prompt.

        Args:
            prompt: The user's basic prompt

        Returns:
            Category name (person, animal, landscape, object, food, abstract, or default)
        """
        prompt_lower = prompt.lower()

        # Check each category pattern
        for category, pattern in self.CATEGORY_PATTERNS.items():
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                logger.info(f"Detected category '{category}' for prompt: {prompt[:50]}...")
                return category

        logger.info(f"Using default category for prompt: {prompt[:50]}...")
        return "default"

    async def generate_dynamic_questions(self, prompt: str, category: str) -> List[Dict]:
        """
        Use LLM to generate contextual refinement questions.

        Args:
            prompt: The user's basic prompt
            category: Detected category

        Returns:
            List of question objects with id, question, type, and options
        """
        system_prompt = """You are an expert at refining image generation prompts. Given a basic prompt, generate 4-6 specific, contextual questions that will help create a better, more detailed image prompt.

CRITICAL RULES:
1. Questions must be SPECIFIC to the prompt content, not generic
2. Each question should have 4-5 concrete, actionable options
3. Always include one optional text question at the end for "Any additional details?"
4. Output ONLY valid JSON, no explanation
5. Use "single-select" type for multiple choice, "text" type for free-form input

Example for "A serene mountain landscape":
{
  "questions": [
    {
      "id": "time_of_day",
      "question": "What time of day for this mountain scene?",
      "type": "single-select",
      "options": ["Dawn with soft pink light", "Midday with clear blue sky", "Golden hour sunset", "Night with stars", "Misty morning"]
    },
    {
      "id": "season",
      "question": "Which season?",
      "type": "single-select",
      "options": ["Spring with wildflowers", "Summer green valleys", "Autumn colors", "Winter snow-covered peaks", "Any season"]
    },
    {
      "id": "mood",
      "question": "What atmosphere should the mountains evoke?",
      "type": "single-select",
      "options": ["Peaceful and calm", "Dramatic and epic", "Mystical with fog", "Vibrant and alive", "Desolate and remote"]
    },
    {
      "id": "style",
      "question": "What visual style?",
      "type": "single-select",
      "options": ["Photorealistic", "Cinematic wide-angle", "Painterly artistic", "Fantasy illustration", "Minimalist"]
    },
    {
      "id": "extras",
      "question": "Any additional details? (optional)",
      "type": "text",
      "placeholder": "e.g., lake in foreground, eagles flying, specific mountain peaks..."
    }
  ]
}"""

        user_message = f"""Generate refinement questions for this image prompt:
"{prompt}"

Category: {category}

Generate 4-6 questions that are SPECIFIC to this exact prompt. Make options concrete and descriptive."""

        try:
            logger.info(f"Generating dynamic questions for: {prompt[:50]}...")
            response = await self.ollama_client.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                },
            )

            # Parse the JSON response
            content = response["message"]["content"].strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            # Parse JSON
            result = json.loads(content)
            questions = result.get("questions", [])

            logger.info(f"Generated {len(questions)} dynamic questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {content[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Error generating dynamic questions: {e}")
            return None

    async def get_questions(self, prompt: str) -> Dict:
        """
        Get refinement questions based on the prompt.
        Uses LLM-generated questions if enabled, falls back to templates.

        Args:
            prompt: The user's basic prompt

        Returns:
            Dict with category and questions
        """
        category = self.detect_category(prompt)

        # Try to generate dynamic questions if enabled
        if self.use_dynamic_questions:
            try:
                dynamic_questions = await self.generate_dynamic_questions(prompt, category)
                if dynamic_questions:
                    logger.info(f"Using {len(dynamic_questions)} LLM-generated questions")
                    return {"category": category, "prompt": prompt, "questions": dynamic_questions}
            except Exception as e:
                logger.warning(f"Failed to generate dynamic questions, falling back to templates: {e}")

        # Fall back to template questions
        logger.info("Using template questions")
        questions = self.CATEGORY_QUESTIONS.get(category, self.CATEGORY_QUESTIONS["default"])
        return {"category": category, "prompt": prompt, "questions": questions}

    def build_enhanced_prompt(
        self, basic_prompt: str, answers: Dict[str, str], category: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Build an enhanced prompt from user answers.
        Works with both template-based and dynamically generated questions.

        Args:
            basic_prompt: The original user prompt
            answers: Dict of question_id -> answer
            category: Optional category (will detect if not provided)

        Returns:
            Dict with enhanced_prompt and negative_prompt
        """
        if not category:
            category = self.detect_category(basic_prompt)

        # Build enhanced prompt by combining basic prompt with answers
        enhanced_parts = [basic_prompt]

        # For dynamically generated questions, simply append all answers
        # Skip the "extras" field as it's usually a text input we'll add at the end
        for question_id, answer in answers.items():
            if question_id == "extras":
                continue  # Handle extras at the end
            if answer and answer.strip():
                # Clean up the answer and add it
                enhanced_parts.append(answer.strip().lower())

        # Add user's extra details if provided (from free-text question)
        if "extras" in answers and answers["extras"] and answers["extras"].strip():
            enhanced_parts.append(answers["extras"])

        # Add quality terms
        enhanced_parts.extend(["professional", "high quality", "detailed"])

        # Combine into final prompt
        enhanced_prompt = ", ".join(enhanced_parts)

        # Generate negative prompt based on category
        negative_prompt = self._generate_negative_prompt(category)

        logger.info(f"Built enhanced prompt from '{basic_prompt[:30]}...' -> '{enhanced_prompt[:50]}...'")

        return {"enhanced_prompt": enhanced_prompt, "negative_prompt": negative_prompt}

    def _generate_negative_prompt(self, category: str) -> str:
        """Generate appropriate negative prompt based on category."""
        base_negative = ["low quality", "blurry", "distorted", "deformed", "ugly", "bad anatomy"]

        category_specific = {
            "person": ["disfigured face", "extra limbs", "bad proportions"],
            "animal": ["deformed body", "extra legs", "mutated"],
            "landscape": ["oversaturated", "unnatural colors", "cluttered"],
            "object": ["poor lighting", "cluttered background", "unprofessional"],
            "food": ["unappetizing", "messy", "unnatural colors"],
            "abstract": ["chaotic", "messy", "incoherent"],
        }

        negatives = base_negative + category_specific.get(category, [])
        return ", ".join(negatives)


# Singleton instance
_prompt_refinement_service: Optional[PromptRefinementService] = None


def get_prompt_refinement_service() -> PromptRefinementService:
    """Get or create the prompt refinement service singleton."""
    global _prompt_refinement_service
    if _prompt_refinement_service is None:
        _prompt_refinement_service = PromptRefinementService()
    return _prompt_refinement_service
