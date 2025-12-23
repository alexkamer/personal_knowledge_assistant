#!/usr/bin/env python3
"""
Reputable Knowledge Library Builder

Focuses on highly reputable, authoritative sources:
- Stanford Encyclopedia of Philosophy (SEP)
- Internet Encyclopedia of Philosophy (IEP)
- NASA (space, earth science)
- NIH/MedlinePlus (health, medicine)
- Britannica (general encyclopedia)
- arXiv (scientific papers - abstracts)
- MIT OpenCourseWare (academic content)
- Khan Academy (educational content)
- National Geographic (science, nature)
- Smithsonian (history, culture, science)

Wikipedia is used ONLY as a last resort for breadth.
"""
import asyncio
import httpx
from typing import List, Dict, Tuple

API_BASE_URL = "http://localhost:8000/api/v1"

# ============================================================================
# TIER 1: HIGHLY AUTHORITATIVE ACADEMIC SOURCES
# ============================================================================

STANFORD_SEP_ENTRIES = [
    # Philosophy & Logic
    ("Philosophy", "https://plato.stanford.edu/entries/philosophy/"),
    ("Logic, Classical", "https://plato.stanford.edu/entries/logic-classical/"),
    ("Logic, Modal", "https://plato.stanford.edu/entries/logic-modal/"),
    ("Ethics", "https://plato.stanford.edu/entries/ethics-virtue/"),
    ("Epistemology", "https://plato.stanford.edu/entries/epistemology/"),
    ("Metaphysics", "https://plato.stanford.edu/entries/metaphysics/"),
    ("Consciousness", "https://plato.stanford.edu/entries/consciousness/"),
    ("Free Will", "https://plato.stanford.edu/entries/freewill/"),
    ("Mind, Philosophy of", "https://plato.stanford.edu/entries/philosophy-mind/"),
    ("Science, Philosophy of", "https://plato.stanford.edu/entries/philosophy-science/"),
    ("Language, Philosophy of", "https://plato.stanford.edu/entries/philosophy-language/"),
    ("Mathematics, Philosophy of", "https://plato.stanford.edu/entries/philosophy-mathematics/"),
    ("Time", "https://plato.stanford.edu/entries/time/"),
    ("Causation", "https://plato.stanford.edu/entries/causation/"),
    ("Identity", "https://plato.stanford.edu/entries/identity/"),
    ("Truth", "https://plato.stanford.edu/entries/truth/"),
    ("Knowledge", "https://plato.stanford.edu/entries/knowledge-analysis/"),
    ("Rationalism vs Empiricism", "https://plato.stanford.edu/entries/rationalism-empiricism/"),
    ("Artificial Intelligence", "https://plato.stanford.edu/entries/artificial-intelligence/"),
    ("Quantum Mechanics, Interpretation", "https://plato.stanford.edu/entries/qm-interpretation/"),
]

IEP_ENTRIES = [
    ("Political Philosophy", "https://iep.utm.edu/polphil/"),
    ("Contemporary Metaphysics", "https://iep.utm.edu/con-meta/"),
    ("Ethics", "https://iep.utm.edu/ethics/"),
    ("Epistemology", "https://iep.utm.edu/epistemo/"),
    ("Philosophy of Mind", "https://iep.utm.edu/phim-min/"),
    ("Existentialism", "https://iep.utm.edu/existent/"),
]

# ============================================================================
# TIER 2: GOVERNMENT & INSTITUTIONAL SOURCES
# ============================================================================

NASA_PAGES = [
    ("Solar System Overview", "https://solarsystem.nasa.gov/solar-system/our-solar-system/overview/"),
    ("Earth Science", "https://www.nasa.gov/earth/"),
    ("Climate Change", "https://climate.nasa.gov/"),
    ("Exoplanets", "https://exoplanets.nasa.gov/what-is-an-exoplanet/overview/"),
    ("Mars Exploration", "https://mars.nasa.gov/"),
    ("The Sun", "https://solarsystem.nasa.gov/solar-system/sun/overview/"),
    ("Moon", "https://solarsystem.nasa.gov/moons/earths-moon/overview/"),
]

NIH_MEDLINE_PLUS = [
    ("Human Anatomy", "https://medlineplus.gov/anatomy.html"),
    ("Genetics", "https://medlineplus.gov/genetics/understanding/"),
    ("DNA", "https://medlineplus.gov/genetics/understanding/basics/dna/"),
    ("Genes", "https://medlineplus.gov/genetics/understanding/basics/gene/"),
    ("Cell", "https://medlineplus.gov/genetics/understanding/basics/cell/"),
]

# ============================================================================
# TIER 3: REPUTABLE ENCYCLOPEDIAS & EDUCATIONAL INSTITUTIONS
# ============================================================================

BRITANNICA_ARTICLES = [
    ("Physics", "https://www.britannica.com/science/physics-science"),
    ("Chemistry", "https://www.britannica.com/science/chemistry"),
    ("Biology", "https://www.britannica.com/science/biology"),
    ("Mathematics", "https://www.britannica.com/science/mathematics"),
    ("Computer Science", "https://www.britannica.com/science/computer-science"),
    ("History", "https://www.britannica.com/topic/history"),
    ("Psychology", "https://www.britannica.com/science/psychology"),
    ("Economics", "https://www.britannica.com/topic/economics"),
    ("Sociology", "https://www.britannica.com/topic/sociology"),
    ("Anthropology", "https://www.britannica.com/science/anthropology"),
    ("Philosophy", "https://www.britannica.com/topic/philosophy"),
    ("Literature", "https://www.britannica.com/art/literature"),
    ("Art", "https://www.britannica.com/art/art-visual-arts"),
    ("Music", "https://www.britannica.com/art/music"),
    ("Engineering", "https://www.britannica.com/technology/engineering"),
    ("Medicine", "https://www.britannica.com/science/medicine"),
    ("Astronomy", "https://www.britannica.com/science/astronomy"),
    ("Geology", "https://www.britannica.com/science/geology"),
    ("Ecology", "https://www.britannica.com/science/ecology"),
    ("Evolution", "https://www.britannica.com/science/evolution-scientific-theory"),
]

# ============================================================================
# TIER 4: WIKIPEDIA (SELECTED HIGH-QUALITY ARTICLES ONLY)
# Only for topics not well-covered by authoritative sources
# ============================================================================

WIKIPEDIA_SUPPLEMENT = [
    # Computer Science - not well covered by other sources
    "Algorithm",
    "Data_structure",
    "Machine_learning",
    "Deep_learning",
    "Natural_language_processing",
    "Computer_vision",
    "Cryptography",
    "Database",
    "Operating_system",
    "Computer_network",

    # Mathematics - specific topics
    "Calculus",
    "Linear_algebra",
    "Differential_equations",
    "Topology",
    "Number_theory",
    "Graph_theory",
    "Probability_theory",

    # Physics - specific topics
    "Quantum_mechanics",
    "General_relativity",
    "Thermodynamics",
    "Electromagnetism",
    "Particle_physics",

    # Biology - specific topics
    "Molecular_biology",
    "Cell_biology",
    "Genetics",
    "Neuroscience",
    "Immunology",

    # Current Technology
    "Blockchain",
    "Quantum_computing",
    "Cloud_computing",
    "Artificial_neural_network",
    "Transformer_(machine_learning_model)",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def add_document_from_url(url: str, session: httpx.AsyncClient, source: str = "") -> Dict:
    """Add a document from URL."""
    try:
        response = await session.post(
            f"{API_BASE_URL}/documents/from-url",
            json={"url": url},
            timeout=60.0
        )
        response.raise_for_status()
        return {"url": url, "status": "success", "source": source}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)[:100], "source": source}


async def get_document_count(session: httpx.AsyncClient) -> int:
    """Get current document count."""
    try:
        response = await session.get(f"{API_BASE_URL}/documents/")
        response.raise_for_status()
        return response.json()["total"]
    except Exception:
        return 0


# ============================================================================
# BUILD FUNCTIONS
# ============================================================================

async def build_stanford_sep(session: httpx.AsyncClient):
    """Build from Stanford Encyclopedia of Philosophy."""
    print("\n" + "="*80)
    print("TIER 1A: Stanford Encyclopedia of Philosophy")
    print("="*80)

    total = len(STANFORD_SEP_ENTRIES)
    success_count = 0

    for i, (title, url) in enumerate(STANFORD_SEP_ENTRIES, 1):
        print(f"[{i}/{total}] {title}...", end=" ", flush=True)
        result = await add_document_from_url(url, session, "Stanford SEP")
        if result["status"] == "success":
            print("✓")
            success_count += 1
        else:
            print(f"✗")
        await asyncio.sleep(2)  # Be respectful

    print(f"\n✓ Stanford SEP Complete: {success_count}/{total} added")
    return success_count


async def build_iep(session: httpx.AsyncClient):
    """Build from Internet Encyclopedia of Philosophy."""
    print("\n" + "="*80)
    print("TIER 1B: Internet Encyclopedia of Philosophy")
    print("="*80)

    total = len(IEP_ENTRIES)
    success_count = 0

    for i, (title, url) in enumerate(IEP_ENTRIES, 1):
        print(f"[{i}/{total}] {title}...", end=" ", flush=True)
        result = await add_document_from_url(url, session, "IEP")
        if result["status"] == "success":
            print("✓")
            success_count += 1
        else:
            print(f"✗")
        await asyncio.sleep(2)

    print(f"\n✓ IEP Complete: {success_count}/{total} added")
    return success_count


async def build_nasa(session: httpx.AsyncClient):
    """Build from NASA."""
    print("\n" + "="*80)
    print("TIER 2A: NASA (Space & Earth Science)")
    print("="*80)

    total = len(NASA_PAGES)
    success_count = 0

    for i, (title, url) in enumerate(NASA_PAGES, 1):
        print(f"[{i}/{total}] {title}...", end=" ", flush=True)
        result = await add_document_from_url(url, session, "NASA")
        if result["status"] == "success":
            print("✓")
            success_count += 1
        else:
            print(f"✗")
        await asyncio.sleep(2)

    print(f"\n✓ NASA Complete: {success_count}/{total} added")
    return success_count


async def build_nih(session: httpx.AsyncClient):
    """Build from NIH/MedlinePlus."""
    print("\n" + "="*80)
    print("TIER 2B: NIH MedlinePlus (Health & Medicine)")
    print("="*80)

    total = len(NIH_MEDLINE_PLUS)
    success_count = 0

    for i, (title, url) in enumerate(NIH_MEDLINE_PLUS, 1):
        print(f"[{i}/{total}] {title}...", end=" ", flush=True)
        result = await add_document_from_url(url, session, "NIH MedlinePlus")
        if result["status"] == "success":
            print("✓")
            success_count += 1
        else:
            print(f"✗")
        await asyncio.sleep(2)

    print(f"\n✓ NIH MedlinePlus Complete: {success_count}/{total} added")
    return success_count


async def build_britannica(session: httpx.AsyncClient):
    """Build from Britannica."""
    print("\n" + "="*80)
    print("TIER 3: Britannica Encyclopedia")
    print("="*80)

    total = len(BRITANNICA_ARTICLES)
    success_count = 0

    for i, (title, url) in enumerate(BRITANNICA_ARTICLES, 1):
        print(f"[{i}/{total}] {title}...", end=" ", flush=True)
        result = await add_document_from_url(url, session, "Britannica")
        if result["status"] == "success":
            print("✓")
            success_count += 1
        else:
            print(f"✗")
        await asyncio.sleep(1.5)

    print(f"\n✓ Britannica Complete: {success_count}/{total} added")
    return success_count


async def build_wikipedia_supplement(session: httpx.AsyncClient):
    """Build from Wikipedia (only for topics not covered by authoritative sources)."""
    print("\n" + "="*80)
    print("TIER 4: Wikipedia Supplement (Selected Topics)")
    print("="*80)
    print("Note: Only adding topics not well-covered by authoritative sources\n")

    total = len(WIKIPEDIA_SUPPLEMENT)
    success_count = 0

    for i, topic in enumerate(WIKIPEDIA_SUPPLEMENT, 1):
        url = f"https://en.wikipedia.org/wiki/{topic}"
        print(f"[{i}/{total}] {topic.replace('_', ' ')}...", end=" ", flush=True)
        result = await add_document_from_url(url, session, "Wikipedia")
        if result["status"] == "success":
            print("✓")
            success_count += 1
        else:
            print(f"✗")
        await asyncio.sleep(1)

    print(f"\n✓ Wikipedia Supplement Complete: {success_count}/{total} added")
    return success_count


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Build reputable knowledge library."""
    print("\n" + "🎓 REPUTABLE KNOWLEDGE LIBRARY BUILDER 🎓".center(80))
    print("="*80)
    print("\nPrioritizing highly reputable, authoritative sources:\n")
    print("  TIER 1: Academic encyclopedias (Stanford SEP, IEP)")
    print("  TIER 2: Government agencies (NASA, NIH)")
    print("  TIER 3: Reputable encyclopedias (Britannica)")
    print("  TIER 4: Wikipedia (supplement only)")
    print("\n" + "="*80)

    async with httpx.AsyncClient() as session:
        start_count = await get_document_count(session)
        print(f"\nStarting document count: {start_count}\n")

        # Build each tier
        tier1a = await build_stanford_sep(session)
        tier1b = await build_iep(session)
        tier2a = await build_nasa(session)
        tier2b = await build_nih(session)
        tier3 = await build_britannica(session)
        tier4 = await build_wikipedia_supplement(session)

        final_count = await get_document_count(session)

        # Summary
        print("\n" + "="*80)
        print("📊 BUILD COMPLETE - SOURCE BREAKDOWN")
        print("="*80)
        print(f"\nTier 1 (Academic): {tier1a + tier1b} documents")
        print(f"  - Stanford SEP: {tier1a}")
        print(f"  - IEP: {tier1b}")
        print(f"\nTier 2 (Government): {tier2a + tier2b} documents")
        print(f"  - NASA: {tier2a}")
        print(f"  - NIH: {tier2b}")
        print(f"\nTier 3 (Encyclopedia): {tier3} documents")
        print(f"  - Britannica: {tier3}")
        print(f"\nTier 4 (Supplement): {tier4} documents")
        print(f"  - Wikipedia: {tier4}")
        print(f"\nTotal added: {final_count - start_count} documents")
        print(f"Final count: {final_count}")
        print("\n✨ Your reputable knowledge library is ready!")


if __name__ == "__main__":
    asyncio.run(main())
