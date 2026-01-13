"""
Build knowledge library in batches with progress tracking.
"""
import requests
import time

# All URLs organized by domain
LIBRARY_URLS = [
    # Computer Science & AI (15)
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

    # Mathematics (10)
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

    # Physics (14)
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

    # Chemistry (9)
    "https://en.wikipedia.org/wiki/Chemistry",
    "https://en.wikipedia.org/wiki/Organic_chemistry",
    "https://en.wikipedia.org/wiki/Inorganic_chemistry",
    "https://en.wikipedia.org/wiki/Physical_chemistry",
    "https://en.wikipedia.org/wiki/Analytical_chemistry",
    "https://en.wikipedia.org/wiki/Biochemistry",
    "https://en.wikipedia.org/wiki/Quantum_chemistry",
    "https://en.wikipedia.org/wiki/Electrochemistry",
    "https://en.wikipedia.org/wiki/Polymer_chemistry",

    # Biology (12)
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

    # Philosophy (10)
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

    # Psychology (6)
    "https://en.wikipedia.org/wiki/Psychology",
    "https://en.wikipedia.org/wiki/Cognitive_psychology",
    "https://en.wikipedia.org/wiki/Developmental_psychology",
    "https://en.wikipedia.org/wiki/Social_psychology",
    "https://en.wikipedia.org/wiki/Behavioral_psychology",

    # Social Sciences (6)
    "https://en.wikipedia.org/wiki/Sociology",
    "https://en.wikipedia.org/wiki/Economics",
    "https://en.wikipedia.org/wiki/Anthropology",
    "https://en.wikipedia.org/wiki/Political_science",
    "https://en.wikipedia.org/wiki/Game_theory",
    "https://en.wikipedia.org/wiki/Behavioral_economics",

    # History (5)
    "https://en.wikipedia.org/wiki/History",
    "https://en.wikipedia.org/wiki/World_history",
    "https://en.wikipedia.org/wiki/Ancient_history",
    "https://en.wikipedia.org/wiki/Medieval_history",
    "https://en.wikipedia.org/wiki/Modern_history",

    # Engineering (6)
    "https://en.wikipedia.org/wiki/Engineering",
    "https://en.wikipedia.org/wiki/Mechanical_engineering",
    "https://en.wikipedia.org/wiki/Electrical_engineering",
    "https://en.wikipedia.org/wiki/Civil_engineering",
    "https://en.wikipedia.org/wiki/Chemical_engineering",
    "https://en.wikipedia.org/wiki/Aerospace_engineering",

    # Medicine (5)
    "https://en.wikipedia.org/wiki/Medicine",
    "https://en.wikipedia.org/wiki/Anatomy",
    "https://en.wikipedia.org/wiki/Physiology",
    "https://en.wikipedia.org/wiki/Pathology",
    "https://en.wikipedia.org/wiki/Pharmacology",

    # Earth Science (5)
    "https://en.wikipedia.org/wiki/Geology",
    "https://en.wikipedia.org/wiki/Meteorology",
    "https://en.wikipedia.org/wiki/Oceanography",
    "https://en.wikipedia.org/wiki/Climate_change",
    "https://en.wikipedia.org/wiki/Environmental_science",

    # Arts & Literature (5)
    "https://en.wikipedia.org/wiki/Art",
    "https://en.wikipedia.org/wiki/Literature",
    "https://en.wikipedia.org/wiki/Music",
    "https://en.wikipedia.org/wiki/Architecture",
    "https://en.wikipedia.org/wiki/Film",
]


def add_document(url):
    """Add document from URL."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/documents/from-url",
            json={"url": url},
            timeout=60
        )
        if response.status_code in [200, 201]:
            data = response.json()
            return True, data.get('filename', 'Unknown')[:60]
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def main():
    print("\n" + "="*80)
    print("BUILDING COMPREHENSIVE KNOWLEDGE LIBRARY")
    print(f"Total URLs to process: {len(LIBRARY_URLS)}")
    print("="*80 + "\n")

    added = 0
    failed = 0

    for i, url in enumerate(LIBRARY_URLS, 1):
        print(f"[{i:3d}/{len(LIBRARY_URLS)}] ", end="", flush=True)
        success, result = add_document(url)

        if success:
            print(f"✓ {result}")
            added += 1
        else:
            print(f"✗ {result}")
            failed += 1

        # Progress update every 10 documents
        if i % 10 == 0:
            print(f"  → Progress: {added} added, {failed} failed\n")

        # Small delay to avoid overwhelming server
        time.sleep(1.5)

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Successfully added: {added}/{len(LIBRARY_URLS)}")
    print(f"Failed: {failed}/{len(LIBRARY_URLS)}")
    if added + failed > 0:
        print(f"Success rate: {added/(added+failed)*100:.1f}%")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
