"""
Service for analyzing and refining image generation prompts.
"""
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptRefinementService:
    """Service for analyzing prompts and generating refinement questions."""

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

    def get_questions(self, prompt: str) -> Dict:
        """
        Get refinement questions based on the prompt.

        Args:
            prompt: The user's basic prompt

        Returns:
            Dict with category and questions
        """
        category = self.detect_category(prompt)
        questions = self.CATEGORY_QUESTIONS.get(category, self.CATEGORY_QUESTIONS["default"])

        return {"category": category, "prompt": prompt, "questions": questions}

    def build_enhanced_prompt(
        self, basic_prompt: str, answers: Dict[str, str], category: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Build an enhanced prompt from user answers.

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

        # Add style if provided
        if "style" in answers and answers["style"]:
            enhanced_parts.append(answers["style"].lower())

        # Add setting/environment if provided
        if "setting" in answers and answers["setting"]:
            enhanced_parts.append(f"set in {answers['setting'].lower()}")

        # Add time/season if provided
        if "time" in answers and answers["time"]:
            enhanced_parts.append(f"during {answers['time'].lower()}")
        if "season" in answers and answers["season"]:
            enhanced_parts.append(f"in {answers['season'].lower()}")

        # Add mood/atmosphere
        if "mood" in answers and answers["mood"]:
            enhanced_parts.append(f"{answers['mood'].lower()} atmosphere")

        # Add action if provided
        if "action" in answers and answers["action"]:
            enhanced_parts.append(answers["action"].lower())

        # Add lighting if provided
        if "lighting" in answers and answers["lighting"]:
            enhanced_parts.append(f"with {answers['lighting'].lower()}")

        # Add angle if provided
        if "angle" in answers and answers["angle"]:
            enhanced_parts.append(f"{answers['angle'].lower()} perspective")

        # Add colors if provided
        if "colors" in answers and answers["colors"]:
            enhanced_parts.append(f"{answers['colors'].lower()} color palette")

        # Add complexity if provided
        if "complexity" in answers and answers["complexity"]:
            enhanced_parts.append(answers["complexity"].lower())

        # Add detail level if provided
        if "detail" in answers and answers["detail"]:
            enhanced_parts.append(answers["detail"].lower())

        # Add user's extra details if provided
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
