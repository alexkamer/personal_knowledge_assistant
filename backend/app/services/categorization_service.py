"""
Service for automatically categorizing documents based on content and metadata.
"""
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

# Define categories and their keywords
CATEGORIES = {
    "Computer Science & Technology": [
        "algorithm", "programming", "software", "computer", "computing", "data structure",
        "machine learning", "artificial intelligence", "neural network", "deep learning",
        "database", "network", "cybersecurity", "blockchain", "cloud", "api", "frontend",
        "backend", "web", "mobile", "app", "code", "javascript", "python", "java",
    ],
    "Mathematics & Statistics": [
        "mathematics", "algebra", "calculus", "geometry", "topology", "number theory",
        "statistics", "probability", "theorem", "proof", "equation", "matrix", "vector",
        "differential", "integral", "function", "trigonometry", "mathematical",
    ],
    "Physics & Astronomy": [
        "physics", "quantum", "relativity", "mechanics", "thermodynamics", "electromagnetism",
        "particle", "nuclear", "atomic", "astrophysics", "cosmology", "astronomy", "planet",
        "star", "galaxy", "universe", "space", "gravitational", "wave", "light",
    ],
    "Chemistry & Materials": [
        "chemistry", "chemical", "molecule", "atom", "compound", "reaction", "organic",
        "inorganic", "polymer", "catalyst", "acid", "base", "element", "periodic table",
        "bond", "electrochemistry", "biochemistry",
    ],
    "Biology & Life Sciences": [
        "biology", "cell", "dna", "rna", "gene", "genetics", "evolution", "organism",
        "species", "ecology", "neuroscience", "brain", "molecular biology", "protein",
        "enzyme", "metabolism", "microbiology", "botany", "zoology", "anatomy", "physiology",
    ],
    "Medicine & Health": [
        "medicine", "medical", "health", "disease", "treatment", "therapy", "patient",
        "clinical", "diagnosis", "symptom", "doctor", "hospital", "surgery", "drug",
        "vaccine", "immunology", "pharmacology", "pathology", "epidemiology",
    ],
    "Psychology & Cognitive Science": [
        "psychology", "cognitive", "behavior", "mental", "mind", "consciousness",
        "perception", "memory", "learning", "emotion", "personality", "psychotherapy",
        "neuropsychology", "developmental", "social psychology",
    ],
    "Philosophy & Logic": [
        "philosophy", "epistemology", "metaphysics", "ethics", "logic", "reasoning",
        "ontology", "phenomenology", "existentialism", "rationalism", "empiricism",
        "morality", "aesthetics", "political philosophy", "philosophy of mind",
    ],
    "Social Sciences": [
        "sociology", "anthropology", "economics", "political science", "geography",
        "social", "society", "culture", "community", "population", "demographic",
        "microeconomics", "macroeconomics", "econometrics", "behavioral economics",
    ],
    "History & Humanities": [
        "history", "historical", "civilization", "ancient", "medieval", "modern",
        "revolution", "war", "empire", "literature", "language", "linguistics",
        "humanities", "culture", "art history",
    ],
    "Engineering": [
        "engineering", "mechanical", "electrical", "civil", "chemical engineering",
        "aerospace", "biomedical", "industrial", "robotics", "control", "design",
        "manufacturing", "materials science",
    ],
    "Earth & Environmental Science": [
        "earth", "geology", "climate", "weather", "meteorology", "ocean", "oceanography",
        "atmosphere", "environmental", "ecology", "sustainability", "renewable energy",
        "global warming", "greenhouse", "carbon", "pollution",
    ],
    "Arts & Music": [
        "art", "music", "painting", "sculpture", "architecture", "design", "aesthetic",
        "composer", "symphony", "opera", "jazz", "classical music", "contemporary art",
    ],
    "Education": [
        "education", "learning", "teaching", "pedagogy", "curriculum", "student",
        "school", "university", "academic", "course",
    ],
}


def categorize_document(
    filename: str,
    content: str,
    metadata_json: Optional[str] = None,
    file_type: str = "",
) -> str:
    """
    Automatically categorize a document based on its content and metadata.

    Args:
        filename: The document filename
        content: The document content
        metadata_json: Optional JSON metadata string
        file_type: File type extension

    Returns:
        Category name or "Uncategorized"
    """
    # Combine all text to analyze
    text_to_analyze = f"{filename.lower()} {content.lower()}"

    # Add metadata if available
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
            if "title" in metadata:
                text_to_analyze += f" {metadata['title'].lower()}"
            if "description" in metadata:
                text_to_analyze += f" {metadata['description'].lower()}"
            if "og_title" in metadata:
                text_to_analyze += f" {metadata['og_title'].lower()}"
        except json.JSONDecodeError:
            pass

    # Count keyword matches for each category
    category_scores = {}

    for category, keywords in CATEGORIES.items():
        score = 0
        for keyword in keywords:
            # Count occurrences of keyword
            score += text_to_analyze.count(keyword.lower())

        category_scores[category] = score

    # Get category with highest score
    if category_scores:
        best_category = max(category_scores.items(), key=lambda x: x[1])
        if best_category[1] > 0:  # Only return if we found at least one match
            logger.info(f"Categorized as '{best_category[0]}' with score {best_category[1]}")
            return best_category[0]

    logger.info("No clear category match, returning Uncategorized")
    return "Uncategorized"


def get_all_categories() -> list[str]:
    """Get list of all available categories."""
    return list(CATEGORIES.keys()) + ["Uncategorized"]
