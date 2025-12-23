"""
Build comprehensive knowledge library from Wikipedia.
Focus on foundational topics across all major domains.
"""
import asyncio
import httpx
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Comprehensive Wikipedia topics organized by domain
WIKIPEDIA_LIBRARY = {
    "Computer Science & AI": [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Deep_learning",
        "https://en.wikipedia.org/wiki/Neural_network",
        "https://en.wikipedia.org/wiki/Natural_language_processing",
        "https://en.wikipedia.org/wiki/Computer_vision",
        "https://en.wikipedia.org/wiki/Algorithm",
        "https://en.wikipedia.org/wiki/Data_structure",
        "https://en.wikipedia.org/wiki/Database",
        "https://en.wikipedia.org/wiki/Operating_system",
        "https://en.wikipedia.org/wiki/Computer_network",
        "https://en.wikipedia.org/wiki/Cryptography",
        "https://en.wikipedia.org/wiki/Cloud_computing",
        "https://en.wikipedia.org/wiki/Blockchain",
        "https://en.wikipedia.org/wiki/Quantum_computing",
    ],

    "Mathematics": [
        "https://en.wikipedia.org/wiki/Mathematics",
        "https://en.wikipedia.org/wiki/Calculus",
        "https://en.wikipedia.org/wiki/Linear_algebra",
        "https://en.wikipedia.org/wiki/Probability_theory",
        "https://en.wikipedia.org/wiki/Statistics",
        "https://en.wikipedia.org/wiki/Number_theory",
        "https://en.wikipedia.org/wiki/Graph_theory",
        "https://en.wikipedia.org/wiki/Topology",
        "https://en.wikipedia.org/wiki/Abstract_algebra",
        "https://en.wikipedia.org/wiki/Differential_equation",
    ],

    "Physics": [
        "https://en.wikipedia.org/wiki/Physics",
        "https://en.wikipedia.org/wiki/Quantum_mechanics",
        "https://en.wikipedia.org/wiki/General_relativity",
        "https://en.wikipedia.org/wiki/Special_relativity",
        "https://en.wikipedia.org/wiki/Thermodynamics",
        "https://en.wikipedia.org/wiki/Electromagnetism",
        "https://en.wikipedia.org/wiki/Particle_physics",
        "https://en.wikipedia.org/wiki/Nuclear_physics",
        "https://en.wikipedia.org/wiki/Atomic_physics",
        "https://en.wikipedia.org/wiki/Condensed_matter_physics",
        "https://en.wikipedia.org/wiki/Astrophysics",
        "https://en.wikipedia.org/wiki/Cosmology",
        "https://en.wikipedia.org/wiki/Optics",
        "https://en.wikipedia.org/wiki/Acoustics",
    ],

    "Chemistry": [
        "https://en.wikipedia.org/wiki/Chemistry",
        "https://en.wikipedia.org/wiki/Organic_chemistry",
        "https://en.wikipedia.org/wiki/Inorganic_chemistry",
        "https://en.wikipedia.org/wiki/Physical_chemistry",
        "https://en.wikipedia.org/wiki/Analytical_chemistry",
        "https://en.wikipedia.org/wiki/Biochemistry",
        "https://en.wikipedia.org/wiki/Quantum_chemistry",
        "https://en.wikipedia.org/wiki/Electrochemistry",
        "https://en.wikipedia.org/wiki/Polymer_chemistry",
    ],

    "Biology": [
        "https://en.wikipedia.org/wiki/Biology",
        "https://en.wikipedia.org/wiki/Genetics",
        "https://en.wikipedia.org/wiki/Evolution",
        "https://en.wikipedia.org/wiki/Cell_biology",
        "https://en.wikipedia.org/wiki/Molecular_biology",
        "https://en.wikipedia.org/wiki/Neuroscience",
        "https://en.wikipedia.org/wiki/Ecology",
        "https://en.wikipedia.org/wiki/Microbiology",
        "https://en.wikipedia.org/wiki/Immunology",
        "https://en.wikipedia.org/wiki/Virology",
        "https://en.wikipedia.org/wiki/Botany",
        "https://en.wikipedia.org/wiki/Zoology",
    ],

    "Philosophy": [
        "https://en.wikipedia.org/wiki/Philosophy",
        "https://en.wikipedia.org/wiki/Metaphysics",
        "https://en.wikipedia.org/wiki/Epistemology",
        "https://en.wikipedia.org/wiki/Ethics",
        "https://en.wikipedia.org/wiki/Logic",
        "https://en.wikipedia.org/wiki/Philosophy_of_mind",
        "https://en.wikipedia.org/wiki/Philosophy_of_science",
        "https://en.wikipedia.org/wiki/Political_philosophy",
        "https://en.wikipedia.org/wiki/Existentialism",
        "https://en.wikipedia.org/wiki/Phenomenology_(philosophy)",
    ],

    "Psychology": [
        "https://en.wikipedia.org/wiki/Psychology",
        "https://en.wikipedia.org/wiki/Cognitive_psychology",
        "https://en.wikipedia.org/wiki/Developmental_psychology",
        "https://en.wikipedia.org/wiki/Social_psychology",
        "https://en.wikipedia.org/wiki/Behavioral_psychology",
        "https://en.wikipedia.org/wiki/Neuroscience",
    ],

    "Social Sciences": [
        "https://en.wikipedia.org/wiki/Sociology",
        "https://en.wikipedia.org/wiki/Economics",
        "https://en.wikipedia.org/wiki/Anthropology",
        "https://en.wikipedia.org/wiki/Political_science",
        "https://en.wikipedia.org/wiki/Game_theory",
        "https://en.wikipedia.org/wiki/Behavioral_economics",
    ],

    "History": [
        "https://en.wikipedia.org/wiki/History",
        "https://en.wikipedia.org/wiki/World_history",
        "https://en.wikipedia.org/wiki/Ancient_history",
        "https://en.wikipedia.org/wiki/Medieval_history",
        "https://en.wikipedia.org/wiki/Modern_history",
    ],

    "Engineering": [
        "https://en.wikipedia.org/wiki/Engineering",
        "https://en.wikipedia.org/wiki/Mechanical_engineering",
        "https://en.wikipedia.org/wiki/Electrical_engineering",
        "https://en.wikipedia.org/wiki/Civil_engineering",
        "https://en.wikipedia.org/wiki/Chemical_engineering",
        "https://en.wikipedia.org/wiki/Aerospace_engineering",
    ],

    "Medicine": [
        "https://en.wikipedia.org/wiki/Medicine",
        "https://en.wikipedia.org/wiki/Anatomy",
        "https://en.wikipedia.org/wiki/Physiology",
        "https://en.wikipedia.org/wiki/Pathology",
        "https://en.wikipedia.org/wiki/Pharmacology",
    ],

    "Earth Science": [
        "https://en.wikipedia.org/wiki/Geology",
        "https://en.wikipedia.org/wiki/Meteorology",
        "https://en.wikipedia.org/wiki/Oceanography",
        "https://en.wikipedia.org/wiki/Climate_change",
        "https://en.wikipedia.org/wiki/Environmental_science",
    ],

    "Arts & Literature": [
        "https://en.wikipedia.org/wiki/Art",
        "https://en.wikipedia.org/wiki/Literature",
        "https://en.wikipedia.org/wiki/Music",
        "https://en.wikipedia.org/wiki/Architecture",
        "https://en.wikipedia.org/wiki/Film",
    ],
}


async def add_document_from_url(url: str) -> tuple[bool, str]:
    """Add a document from URL. Returns (success, filename)."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/documents/from-url",
                json={"url": url}
            )
            if response.status_code == 200:
                data = response.json()
                filename = data['filename'][:70]
                return True, filename
            else:
                return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


async def build_library():
    """Build comprehensive knowledge library."""
    print("\n" + "="*80)
    print("BUILDING COMPREHENSIVE KNOWLEDGE LIBRARY")
    print("="*80 + "\n")

    total_added = 0
    total_failed = 0

    for domain, urls in WIKIPEDIA_LIBRARY.items():
        print(f"\n{'='*80}")
        print(f"{domain} ({len(urls)} articles)")
        print("="*80)

        domain_added = 0
        for i, url in enumerate(urls, 1):
            success, result = await add_document_from_url(url)
            if success:
                print(f"  [{i:2d}/{len(urls)}] ✓ {result}")
                domain_added += 1
                total_added += 1
            else:
                print(f"  [{i:2d}/{len(urls)}] ✗ Failed: {result}")
                total_failed += 1

            # Small delay between requests
            await asyncio.sleep(1)

        print(f"\n  → {domain_added}/{len(urls)} added successfully")

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total added: {total_added}")
    print(f"Total failed: {total_failed}")
    print(f"Success rate: {total_added/(total_added+total_failed)*100:.1f}%")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(build_library())
