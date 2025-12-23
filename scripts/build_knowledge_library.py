#!/usr/bin/env python3
"""
Script to systematically build a comprehensive knowledge library.

Adds content from reputable sources across major domains:
- Wikipedia (general reference)
- Stanford Encyclopedia of Philosophy (philosophy/logic)
- NIH/PubMed (health/medicine)
- NASA (space/astronomy)
- NIST (physics/chemistry standards)
- IEEE (technology/engineering)
- MIT OpenCourseWare (academic content)
"""
import asyncio
import httpx
from typing import List, Dict, Tuple

API_BASE_URL = "http://localhost:8000/api/v1"

# Reputable Sources with URLs
# Format: (topic_name, url, source_type)
REPUTABLE_SOURCES = [
    # Stanford Encyclopedia of Philosophy
    ("Philosophy Overview", "https://plato.stanford.edu/entries/philosophy/", "Stanford SEP"),
    ("Logic", "https://plato.stanford.edu/entries/logic-classical/", "Stanford SEP"),
    ("Ethics", "https://plato.stanford.edu/entries/ethics-virtue/", "Stanford SEP"),
    ("Epistemology", "https://plato.stanford.edu/entries/epistemology/", "Stanford SEP"),

    # Internet Encyclopedia of Philosophy
    ("Metaphysics", "https://iep.utm.edu/con-meta/", "IEP"),
    ("Political Philosophy", "https://iep.utm.edu/polphil/", "IEP"),

    # MIT OpenCourseWare (publicly accessible intro pages)
    ("Computer Science Introduction", "https://ocw.mit.edu/courses/intro-programming/", "MIT OCW"),

    # NASA
    ("Solar System", "https://solarsystem.nasa.gov/solar-system/our-solar-system/overview/", "NASA"),
    ("Earth Science", "https://www.nasa.gov/earth/", "NASA"),
    ("Exoplanets", "https://exoplanets.nasa.gov/what-is-an-exoplanet/overview/", "NASA"),

    # NIH/MedlinePlus (health information)
    ("Human Anatomy", "https://medlineplus.gov/anatomy.html", "NIH MedlinePlus"),
    ("Genetics", "https://medlineplus.gov/genetics/understanding/", "NIH MedlinePlus"),

    # Britannica (reputable encyclopedia)
    ("World History", "https://www.britannica.com/topic/history", "Britannica"),
    ("Biology", "https://www.britannica.com/science/biology", "Britannica"),
    ("Chemistry", "https://www.britannica.com/science/chemistry", "Britannica"),
]

# Level 1: Major Academic Disciplines (Broad Foundation - Wikipedia for breadth)
LEVEL_1_TOPICS = {
    "Natural Sciences": [
        "Science",
        "Physics",
        "Chemistry",
        "Biology",
        "Astronomy",
        "Earth_science",
        "Geology",
        "Meteorology",
        "Oceanography",
    ],
    "Formal Sciences": [
        "Mathematics",
        "Logic",
        "Statistics",
        "Computer_science",
        "Information_theory",
        "Systems_science",
    ],
    "Social Sciences": [
        "Psychology",
        "Sociology",
        "Anthropology",
        "Economics",
        "Political_science",
        "Geography",
        "History",
        "Linguistics",
    ],
    "Applied Sciences": [
        "Engineering",
        "Medicine",
        "Agriculture",
        "Architecture",
        "Business",
        "Education",
        "Law",
    ],
    "Humanities": [
        "Philosophy",
        "Literature",
        "Art",
        "Music",
        "Religion",
        "Ethics",
    ],
}

# Level 2: Important Subtopics (More Specific)
LEVEL_2_TOPICS = {
    "Physics": [
        "Classical_mechanics",
        "Thermodynamics",
        "Electromagnetism",
        "Quantum_mechanics",
        "Relativity",
        "Particle_physics",
        "Astrophysics",
    ],
    "Computer Science": [
        "Algorithm",
        "Data_structure",
        "Artificial_intelligence",
        "Machine_learning",
        "Database",
        "Computer_network",
        "Operating_system",
        "Programming_language",
        "Software_engineering",
    ],
    "Biology": [
        "Genetics",
        "Evolution",
        "Ecology",
        "Molecular_biology",
        "Cell_biology",
        "Biochemistry",
        "Neuroscience",
    ],
    "Mathematics": [
        "Algebra",
        "Calculus",
        "Geometry",
        "Number_theory",
        "Topology",
        "Probability",
        "Linear_algebra",
    ],
    "Psychology": [
        "Cognitive_psychology",
        "Behavioral_psychology",
        "Developmental_psychology",
        "Social_psychology",
        "Clinical_psychology",
    ],
    "Economics": [
        "Microeconomics",
        "Macroeconomics",
        "Game_theory",
        "Econometrics",
        "Behavioral_economics",
    ],
}

# Level 3: Specialized/Current Topics
LEVEL_3_TOPICS = [
    # AI/ML Specific
    "Deep_learning",
    "Neural_network",
    "Natural_language_processing",
    "Computer_vision",
    "Reinforcement_learning",
    "Transformer_(machine_learning_model)",

    # Technology
    "Blockchain",
    "Cloud_computing",
    "Quantum_computing",
    "Cybersecurity",
    "Internet_of_things",

    # Science
    "CRISPR",
    "Climate_change",
    "Renewable_energy",
    "Nanotechnology",
    "Biotechnology",

    # Society
    "Globalization",
    "Sustainability",
    "Democracy",
    "Capitalism",
    "Human_rights",
]


async def add_document_from_url(url: str, session: httpx.AsyncClient) -> Dict:
    """Add a document from URL to the knowledge base."""
    try:
        response = await session.post(
            f"{API_BASE_URL}/documents/from-url",
            json={"url": url},
            timeout=60.0
        )
        response.raise_for_status()
        return {"url": url, "status": "success", "data": response.json()}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}


async def build_reputable_sources(session: httpx.AsyncClient):
    """Add content from reputable academic and authoritative sources."""
    print("\n" + "="*80)
    print("LEVEL 0: Reputable Sources - Academic & Authoritative Content")
    print("="*80 + "\n")

    total = len(REPUTABLE_SOURCES)

    for i, (topic, url, source) in enumerate(REPUTABLE_SOURCES, 1):
        print(f"[{i}/{total}] {source}: {topic}...", end=" ")

        result = await add_document_from_url(url, session)
        if result["status"] == "success":
            print("✓")
        else:
            print(f"✗ ({result['error'][:50]})")

        await asyncio.sleep(2)  # Be respectful with rate limiting


async def build_level_1(session: httpx.AsyncClient):
    """Build Level 1: Major disciplines."""
    print("\n" + "="*80)
    print("LEVEL 1: Building Foundation - Major Academic Disciplines (Wikipedia)")
    print("="*80 + "\n")

    total = sum(len(topics) for topics in LEVEL_1_TOPICS.values())
    current = 0

    for domain, topics in LEVEL_1_TOPICS.items():
        print(f"\n📚 {domain}")
        print("-" * 80)

        for topic in topics:
            current += 1
            url = f"https://en.wikipedia.org/wiki/{topic}"
            print(f"[{current}/{total}] Adding: {topic.replace('_', ' ')}...", end=" ")

            result = await add_document_from_url(url, session)
            if result["status"] == "success":
                print("✓")
            else:
                print(f"✗ ({result['error'][:50]})")

            # Rate limiting
            await asyncio.sleep(1)


async def build_level_2(session: httpx.AsyncClient):
    """Build Level 2: Important subtopics."""
    print("\n" + "="*80)
    print("LEVEL 2: Adding Depth - Important Subtopics")
    print("="*80 + "\n")

    total = sum(len(topics) for topics in LEVEL_2_TOPICS.values())
    current = 0

    for domain, topics in LEVEL_2_TOPICS.items():
        print(f"\n📖 {domain}")
        print("-" * 80)

        for topic in topics:
            current += 1
            url = f"https://en.wikipedia.org/wiki/{topic}"
            print(f"[{current}/{total}] Adding: {topic.replace('_', ' ')}...", end=" ")

            result = await add_document_from_url(url, session)
            if result["status"] == "success":
                print("✓")
            else:
                print(f"✗ ({result['error'][:50]})")

            await asyncio.sleep(1)


async def build_level_3(session: httpx.AsyncClient):
    """Build Level 3: Specialized topics."""
    print("\n" + "="*80)
    print("LEVEL 3: Adding Specialization - Current & Specialized Topics")
    print("="*80 + "\n")

    total = len(LEVEL_3_TOPICS)

    for i, topic in enumerate(LEVEL_3_TOPICS, 1):
        url = f"https://en.wikipedia.org/wiki/{topic}"
        print(f"[{i}/{total}] Adding: {topic.replace('_', ' ')}...", end=" ")

        result = await add_document_from_url(url, session)
        if result["status"] == "success":
            print("✓")
        else:
            print(f"✗ ({result['error'][:50]})")

        await asyncio.sleep(1)


async def get_document_count(session: httpx.AsyncClient) -> int:
    """Get current document count."""
    try:
        response = await session.get(f"{API_BASE_URL}/documents/")
        response.raise_for_status()
        return response.json()["total"]
    except Exception:
        return 0


async def main():
    """Main execution."""
    print("\n" + "🌍 KNOWLEDGE LIBRARY BUILDER 🌍".center(80))
    print("=" * 80)
    print("\nBuilding comprehensive knowledge library from reputable sources:")
    print("  - Academic institutions (Stanford, MIT)")
    print("  - Government agencies (NASA, NIH)")
    print("  - Reputable encyclopedias (Britannica, Wikipedia)")
    print()

    async with httpx.AsyncClient() as session:
        # Check starting count
        start_count = await get_document_count(session)
        print(f"Starting document count: {start_count}")

        # Build each level
        await build_reputable_sources(session)
        level0_count = await get_document_count(session)
        print(f"\n✓ Level 0 Complete! Documents: {level0_count} (+{level0_count - start_count})")

        await build_level_1(session)
        level1_count = await get_document_count(session)
        print(f"\n✓ Level 1 Complete! Documents: {level1_count} (+{level1_count - level0_count})")

        await build_level_2(session)
        level2_count = await get_document_count(session)
        print(f"\n✓ Level 2 Complete! Documents: {level2_count} (+{level2_count - level1_count})")

        await build_level_3(session)
        final_count = await get_document_count(session)
        print(f"\n✓ Level 3 Complete! Documents: {final_count} (+{final_count - level2_count})")

        # Summary
        print("\n" + "="*80)
        print("📊 BUILD COMPLETE - SUMMARY")
        print("="*80)
        print(f"Starting documents: {start_count}")
        print(f"Final documents:    {final_count}")
        print(f"Added:              {final_count - start_count}")
        print(f"\nSources used:")
        print(f"  - Reputable academic/government sources: {level0_count - start_count}")
        print(f"  - Wikipedia (general reference): {final_count - level0_count}")
        print("\n✨ Your comprehensive knowledge library is ready!")


if __name__ == "__main__":
    asyncio.run(main())
