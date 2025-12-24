"""
Service for analyzing and refining image generation prompts.
"""
import json
import logging
import os
import re
from typing import Dict, List, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("google-genai package not installed. Install with: pip install google-genai")

from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptRefinementService:
    """Service for analyzing prompts and generating refinement questions."""

    def __init__(self):
        """Initialize the service with Gemini client."""
        if not GENAI_AVAILABLE:
            logger.error("google-genai package not installed - falling back to template questions")
            self.client = None
            self.use_dynamic_questions = False
            return

        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured - falling back to template questions")
            self.client = None
            self.use_dynamic_questions = False
            return

        # Set GOOGLE_API_KEY environment variable for genai client
        os.environ['GOOGLE_API_KEY'] = settings.gemini_api_key

        # Initialize client
        self.client = genai.Client()
        self.llm_model = "gemini-2.0-flash-exp"  # Fast Gemini model with structured output
        self.use_dynamic_questions = True  # Enable LLM-generated questions
        logger.info("Prompt refinement service initialized with Gemini Flash")

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
        Use Gemini Flash to generate contextual refinement questions.

        Args:
            prompt: The user's basic prompt
            category: Detected category

        Returns:
            List of question objects with id, question, type, and options
        """
        if not self.client:
            logger.warning("Gemini client not available")
            return None

        system_instructions = """You are an expert at refining image generation prompts using professional techniques. Generate 4-6 questions that build a NARRATIVE, DESCRIPTIVE prompt rather than just collecting keywords.

PROMPTING PHILOSOPHY:
- Describe the SCENE, don't just list keywords
- Use photography/art terminology for professional results
- Build descriptive paragraphs, not disconnected words
- Guide users toward structured, detailed descriptions

QUESTION STRATEGIES BY TYPE:

Photorealistic:
- Ask about shot type, camera angle, lens details
- Lighting setup and atmosphere
- Fine textures and details to emphasize

Illustrations/Stickers:
- Style specifics (line quality, shading technique)
- Color palette and design characteristics
- Background treatment (transparent, solid, gradient)

Product Photography:
- Studio lighting setup (softbox, three-point, etc.)
- Camera angle and what it showcases
- Background surface and composition
- Key details to emphasize

Minimalist/Design:
- Subject placement and negative space
- Color scheme and mood
- Lighting quality (soft, dramatic, etc.)

CRITICAL RULES:
1. Questions must be SPECIFIC to the prompt content
2. Options should be DESCRIPTIVE PHRASES, not single words
3. Always include one text question for additional narrative details
4. Use "single-select" for multiple choice, "text" for free-form
5. Output ONLY valid JSON with a "questions" array

Example for "A serene mountain landscape":
{
  "questions": [
    {
      "id": "shot_composition",
      "question": "What camera perspective and composition?",
      "type": "single-select",
      "options": [
        "Wide-angle landscape shot emphasizing vast scale",
        "Telephoto compressed layers of mountain ranges",
        "Low angle looking up at towering peaks",
        "Aerial drone shot revealing valley patterns",
        "Eye-level with foreground interest"
      ]
    },
    {
      "id": "lighting_atmosphere",
      "question": "What lighting creates the serene mood?",
      "type": "single-select",
      "options": [
        "Dawn with soft pink alpenglow on peaks",
        "Golden hour side-lighting with long shadows",
        "Overcast diffused light for muted tones",
        "Dramatic rays breaking through clouds",
        "Blue hour twilight with subtle color gradients"
      ]
    },
    {
      "id": "environmental_details",
      "question": "What environmental elements enhance the scene?",
      "type": "single-select",
      "options": [
        "Pristine alpine lake reflecting mountains",
        "Wildflower meadow in foreground",
        "Wispy clouds wrapping mountain flanks",
        "Ancient weathered pine trees framing view",
        "Fresh snow on distant peaks"
      ]
    },
    {
      "id": "visual_style",
      "question": "What photographic style and processing?",
      "type": "single-select",
      "options": [
        "Photorealistic with rich detail and texture",
        "Cinematic color grading with teal and orange",
        "Fine art black and white with contrast",
        "Painterly with impressionistic qualities",
        "HDR processed for dramatic detail"
      ]
    },
    {
      "id": "narrative_details",
      "question": "Any additional narrative details to enrich the scene? (optional)",
      "type": "text",
      "placeholder": "Describe textures, mood elements, or story details like 'morning mist rising from valley, distant eagle soaring, sense of peaceful isolation'"
    }
  ]
}"""

        user_message = f"""Generate refinement questions for this image prompt:
"{prompt}"

Category: {category}

Generate 4-6 questions with DESCRIPTIVE options that build toward a rich, narrative prompt. Focus on helping the user describe the scene professionally, not just list attributes."""

        try:
            logger.info(f"Generating dynamic questions with Gemini for: {prompt[:50]}...")

            # Use Gemini with JSON response mode for reliable structured output
            response = self.client.models.generate_content(
                model=self.llm_model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instructions,
                    temperature=0.7,
                    response_mime_type="application/json",  # Force JSON output
                ),
            )

            # Parse the JSON response
            content = response.text.strip()
            result = json.loads(content)
            questions = result.get("questions", [])

            logger.info(f"Generated {len(questions)} dynamic questions in {len(content)} chars")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response content: {content[:200] if 'content' in locals() else 'N/A'}...")
            return None
        except Exception as e:
            logger.error(f"Error generating dynamic questions with Gemini: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
        Build an enhanced, narrative-style prompt from user answers.
        Constructs descriptive sentences rather than keyword lists.

        Args:
            basic_prompt: The original user prompt
            answers: Dict of question_id -> answer
            category: Optional category (will detect if not provided)

        Returns:
            Dict with enhanced_prompt and negative_prompt
        """
        if not category:
            category = self.detect_category(basic_prompt)

        # Start with the base subject/scene
        narrative_parts = [basic_prompt]

        # Separate answers by type for better narrative flow
        narrative_answers = []
        extras_text = None

        for question_id, answer in answers.items():
            # Handle the optional text field specially
            if question_id in ["extras", "narrative_details", "additional_details"]:
                if answer and answer.strip():
                    extras_text = answer.strip()
                continue

            # Collect descriptive answers
            if answer and answer.strip():
                # Keep the descriptive phrases as-is (they're already narrative)
                narrative_answers.append(answer.strip())

        # Build narrative description
        if narrative_answers:
            # Join descriptive elements with period for better narrative flow
            description = ". ".join(narrative_answers)
            # Capitalize first letter if needed
            if description and not description[0].isupper():
                description = description[0].upper() + description[1:]
            narrative_parts.append(description)

        # Add user's additional narrative details if provided
        if extras_text:
            narrative_parts.append(extras_text)

        # Add quality indicators as a final sentence
        narrative_parts.append("Professional quality, highly detailed")

        # Combine with period separation for narrative flow
        enhanced_prompt = ". ".join(narrative_parts)

        # Ensure proper sentence ending
        if not enhanced_prompt.endswith("."):
            enhanced_prompt += "."

        # Generate negative prompt based on category
        negative_prompt = self._generate_negative_prompt(category)

        logger.info(f"Built narrative prompt from '{basic_prompt[:30]}...' -> '{enhanced_prompt[:80]}...'")

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
