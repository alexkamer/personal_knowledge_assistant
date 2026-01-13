"""
Expand knowledge library with additional reputable sources.
Focus on filling gaps and adding depth to existing categories.
"""
import asyncio
import httpx
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Expanded source collection organized by priority and domain
REPUTABLE_SOURCES = {
    # Tier 1: Academic encyclopedias and peer-reviewed sources
    "stanford_sep": [
        # Additional Philosophy topics
        "https://plato.stanford.edu/entries/ethics/",
        "https://plato.stanford.edu/entries/logic-classical/",
        "https://plato.stanford.edu/entries/mind/",
        "https://plato.stanford.edu/entries/causation/",
        "https://plato.stanford.edu/entries/relativism/",
        "https://plato.stanford.edu/entries/existentialism/",
        "https://plato.stanford.edu/entries/pragmatism/",
        "https://plato.stanford.edu/entries/phenomenology/",
        "https://plato.stanford.edu/entries/language-thought/",
        "https://plato.stanford.edu/entries/intentionality/",
        # Science and Math topics
        "https://plato.stanford.edu/entries/scientific-method/",
        "https://plato.stanford.edu/entries/scientific-explanation/",
        "https://plato.stanford.edu/entries/scientific-realism/",
        "https://plato.stanford.edu/entries/probability-interpret/",
        "https://plato.stanford.edu/entries/logic-modal/",
        "https://plato.stanford.edu/entries/set-theory/",
    ],

    "iep": [
        # Psychology and Mind
        "https://iep.utm.edu/cognition/",
        "https://iep.utm.edu/behavior/",
        "https://iep.utm.edu/memory/",
        "https://iep.utm.edu/emotion/",
        # Social and Political
        "https://iep.utm.edu/ethics-politics/",
        "https://iep.utm.edu/soc-cont/",
        "https://iep.utm.edu/law-phil/",
        "https://iep.utm.edu/feminism/",
    ],

    # Tier 2: Government and Research Institutions
    "nasa": [
        # Space exploration and astronomy
        "https://science.nasa.gov/universe/",
        "https://science.nasa.gov/earth/",
        "https://science.nasa.gov/planetary-science/",
        "https://www.nasa.gov/humans-in-space/",
        "https://www.nasa.gov/technology/",
        "https://climate.nasa.gov/",
        "https://exoplanets.nasa.gov/what-is-an-exoplanet/overview/",
    ],

    "nih": [
        # Health and medicine
        "https://medlineplus.gov/brain.html",
        "https://medlineplus.gov/heartdiseases.html",
        "https://medlineplus.gov/cancer.html",
        "https://medlineplus.gov/immunesystem.html",
        "https://www.nih.gov/health-information/nutrition",
        "https://www.genome.gov/about-genomics",
    ],

    "smithsonian": [
        # History and culture
        "https://www.si.edu/learn/teaching-resources/science-technology-resources",
        "https://naturalhistory.si.edu/education/teaching-resources",
    ],

    # Tier 3: High-quality encyclopedias
    "britannica": [
        # Arts and Humanities
        "https://www.britannica.com/art/art",
        "https://www.britannica.com/art/architecture",
        "https://www.britannica.com/art/sculpture",
        "https://www.britannica.com/art/painting",
        "https://www.britannica.com/art/photography",
        "https://www.britannica.com/topic/language",
        "https://www.britannica.com/topic/linguistics",
        # Social Sciences (expanded)
        "https://www.britannica.com/science/political-science",
        "https://www.britannica.com/topic/culture",
        "https://www.britannica.com/topic/religion",
        "https://www.britannica.com/topic/ethics-philosophy",
        # Technology
        "https://www.britannica.com/technology/technology",
        "https://www.britannica.com/technology/artificial-intelligence",
        "https://www.britannica.com/technology/robotics",
        # Environmental Science
        "https://www.britannica.com/science/environmental-science",
        "https://www.britannica.com/science/climate-change",
        "https://www.britannica.com/science/ecosystem",
        "https://www.britannica.com/science/biodiversity",
    ],

    # Tier 4: Specialized Wikipedia topics (high-quality, well-sourced)
    "wikipedia_specialized": [
        # Advanced Math
        "https://en.wikipedia.org/wiki/Abstract_algebra",
        "https://en.wikipedia.org/wiki/Real_analysis",
        "https://en.wikipedia.org/wiki/Complex_analysis",
        "https://en.wikipedia.org/wiki/Functional_analysis",
        "https://en.wikipedia.org/wiki/Numerical_analysis",
        # Advanced CS
        "https://en.wikipedia.org/wiki/Distributed_computing",
        "https://en.wikipedia.org/wiki/Parallel_computing",
        "https://en.wikipedia.org/wiki/Compiler",
        "https://en.wikipedia.org/wiki/Programming_language_theory",
        "https://en.wikipedia.org/wiki/Formal_verification",
        "https://en.wikipedia.org/wiki/Information_theory",
        # Advanced Physics
        "https://en.wikipedia.org/wiki/Statistical_mechanics",
        "https://en.wikipedia.org/wiki/String_theory",
        "https://en.wikipedia.org/wiki/Dark_matter",
        "https://en.wikipedia.org/wiki/Dark_energy",
        # Biology and Health
        "https://en.wikipedia.org/wiki/Epigenetics",
        "https://en.wikipedia.org/wiki/Microbiome",
        "https://en.wikipedia.org/wiki/CRISPR",
        "https://en.wikipedia.org/wiki/Virology",
        "https://en.wikipedia.org/wiki/Epidemiology",
        # Social Sciences
        "https://en.wikipedia.org/wiki/Behavioral_economics",
        "https://en.wikipedia.org/wiki/Game_theory",
        "https://en.wikipedia.org/wiki/Cognitive_psychology",
        "https://en.wikipedia.org/wiki/Developmental_psychology",
        # Environmental
        "https://en.wikipedia.org/wiki/Renewable_energy",
        "https://en.wikipedia.org/wiki/Sustainable_development",
        "https://en.wikipedia.org/wiki/Conservation_biology",
        # Technology
        "https://en.wikipedia.org/wiki/Internet_of_things",
        "https://en.wikipedia.org/wiki/5G",
        "https://en.wikipedia.org/wiki/Nanotechnology",
        "https://en.wikipedia.org/wiki/Biotechnology",
    ],
}


async def add_document_from_url(url: str) -> bool:
    """Add a document from URL to the knowledge base."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/documents/from-url",
                json={"url": url}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Added: {data['filename'][:80]}")
                return True
            else:
                print(f"✗ Failed ({response.status_code}): {url}")
                return False
    except Exception as e:
        print(f"✗ Error: {url} - {str(e)[:100]}")
        return False


async def build_expanded_library():
    """Build expanded knowledge library from reputable sources."""
    total_added = 0
    total_failed = 0

    print("=" * 80)
    print("EXPANDING KNOWLEDGE LIBRARY")
    print("=" * 80)
    print()

    # Process each tier
    for tier_name, urls in REPUTABLE_SOURCES.items():
        print(f"\n{'='*80}")
        print(f"Processing: {tier_name.upper().replace('_', ' ')}")
        print(f"{'='*80}")
        print(f"URLs to process: {len(urls)}")
        print()

        tier_added = 0
        tier_failed = 0

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] ", end="")
            success = await add_document_from_url(url)
            if success:
                tier_added += 1
                total_added += 1
            else:
                tier_failed += 1
                total_failed += 1

            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)

        print(f"\n{tier_name}: {tier_added} added, {tier_failed} failed")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total documents added: {total_added}")
    print(f"Total failed: {total_failed}")
    print(f"Success rate: {total_added / (total_added + total_failed) * 100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    print("\nStarting expanded library build...")
    print("This will add ~90 additional high-quality documents\n")
    asyncio.run(build_expanded_library())
    print("\nDone! Your knowledge library has been expanded.")
