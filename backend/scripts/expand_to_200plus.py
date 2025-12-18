"""
Expand library to 200+ documents with specialized topics.
"""
import requests
import time

# Additional specialized topics to expand the library
EXPANSION_URLS = [
    # Advanced Computer Science
    "https://en.wikipedia.org/wiki/Computational_complexity_theory",
    "https://en.wikipedia.org/wiki/Theory_of_computation",
    "https://en.wikipedia.org/wiki/Programming_paradigm",
    "https://en.wikipedia.org/wiki/Object-oriented_programming",
    "https://en.wikipedia.org/wiki/Functional_programming",
    "https://en.wikipedia.org/wiki/Software_engineering",
    "https://en.wikipedia.org/wiki/Computer_graphics",
    "https://en.wikipedia.org/wiki/Human-computer_interaction",
    "https://en.wikipedia.org/wiki/Information_retrieval",
    "https://en.wikipedia.org/wiki/Computer_security",
    "https://en.wikipedia.org/wiki/Distributed_computing",
    "https://en.wikipedia.org/wiki/Parallel_computing",
    "https://en.wikipedia.org/wiki/Compiler",
    "https://en.wikipedia.org/wiki/Formal_verification",

    # Advanced AI/ML
    "https://en.wikipedia.org/wiki/Reinforcement_learning",
    "https://en.wikipedia.org/wiki/Supervised_learning",
    "https://en.wikipedia.org/wiki/Unsupervised_learning",
    "https://en.wikipedia.org/wiki/Transformer_(machine_learning_model)",
    "https://en.wikipedia.org/wiki/Convolutional_neural_network",
    "https://en.wikipedia.org/wiki/Recurrent_neural_network",
    "https://en.wikipedia.org/wiki/Generative_adversarial_network",
    "https://en.wikipedia.org/wiki/Large_language_model",

    # Advanced Math
    "https://en.wikipedia.org/wiki/Real_analysis",
    "https://en.wikipedia.org/wiki/Complex_analysis",
    "https://en.wikipedia.org/wiki/Functional_analysis",
    "https://en.wikipedia.org/wiki/Numerical_analysis",
    "https://en.wikipedia.org/wiki/Combinatorics",
    "https://en.wikipedia.org/wiki/Discrete_mathematics",
    "https://en.wikipedia.org/wiki/Mathematical_logic",
    "https://en.wikipedia.org/wiki/Set_theory",
    "https://en.wikipedia.org/wiki/Category_theory",

    # Advanced Physics
    "https://en.wikipedia.org/wiki/Quantum_field_theory",
    "https://en.wikipedia.org/wiki/String_theory",
    "https://en.wikipedia.org/wiki/Dark_matter",
    "https://en.wikipedia.org/wiki/Dark_energy",
    "https://en.wikipedia.org/wiki/Higgs_boson",
    "https://en.wikipedia.org/wiki/Black_hole",
    "https://en.wikipedia.org/wiki/Big_Bang",
    "https://en.wikipedia.org/wiki/Quantum_entanglement",
    "https://en.wikipedia.org/wiki/Superconductivity",
    "https://en.wikipedia.org/wiki/Plasma_(physics)",

    # Advanced Biology
    "https://en.wikipedia.org/wiki/Epigenetics",
    "https://en.wikipedia.org/wiki/Proteomics",
    "https://en.wikipedia.org/wiki/Genomics",
    "https://en.wikipedia.org/wiki/Bioinformatics",
    "https://en.wikipedia.org/wiki/Synthetic_biology",
    "https://en.wikipedia.org/wiki/Systems_biology",
    "https://en.wikipedia.org/wiki/CRISPR",
    "https://en.wikipedia.org/wiki/Stem_cell",
    "https://en.wikipedia.org/wiki/Microbiome",
    "https://en.wikipedia.org/wiki/Evolutionary_biology",

    # Technology & Innovation
    "https://en.wikipedia.org/wiki/Internet_of_things",
    "https://en.wikipedia.org/wiki/5G",
    "https://en.wikipedia.org/wiki/Nanotechnology",
    "https://en.wikipedia.org/wiki/Biotechnology",
    "https://en.wikipedia.org/wiki/Robotics",
    "https://en.wikipedia.org/wiki/Virtual_reality",
    "https://en.wikipedia.org/wiki/Augmented_reality",
    "https://en.wikipedia.org/wiki/Cybersecurity",
    "https://en.wikipedia.org/wiki/Software_development",

    # Environmental & Sustainability
    "https://en.wikipedia.org/wiki/Renewable_energy",
    "https://en.wikipedia.org/wiki/Sustainable_development",
    "https://en.wikipedia.org/wiki/Conservation_biology",
    "https://en.wikipedia.org/wiki/Biodiversity",
    "https://en.wikipedia.org/wiki/Ecosystem",
    "https://en.wikipedia.org/wiki/Carbon_footprint",
    "https://en.wikipedia.org/wiki/Green_technology",

    # Social Sciences & Economics
    "https://en.wikipedia.org/wiki/Macroeconomics",
    "https://en.wikipedia.org/wiki/Microeconomics",
    "https://en.wikipedia.org/wiki/International_relations",
    "https://en.wikipedia.org/wiki/Public_policy",
    "https://en.wikipedia.org/wiki/Development_economics",
    "https://en.wikipedia.org/wiki/Econometrics",
    "https://en.wikipedia.org/wiki/Social_network",
    "https://en.wikipedia.org/wiki/Organizational_behavior",

    # Arts & Culture
    "https://en.wikipedia.org/wiki/Renaissance",
    "https://en.wikipedia.org/wiki/Classical_music",
    "https://en.wikipedia.org/wiki/Modern_art",
    "https://en.wikipedia.org/wiki/Theater",
    "https://en.wikipedia.org/wiki/Dance",
    "https://en.wikipedia.org/wiki/Photography",

    # Medicine & Health
    "https://en.wikipedia.org/wiki/Neurology",
    "https://en.wikipedia.org/wiki/Cardiology",
    "https://en.wikipedia.org/wiki/Oncology",
    "https://en.wikipedia.org/wiki/Psychiatry",
    "https://en.wikipedia.org/wiki/Public_health",
    "https://en.wikipedia.org/wiki/Epidemiology",
    "https://en.wikipedia.org/wiki/Medical_imaging",
    "https://en.wikipedia.org/wiki/Vaccine",

    # Philosophy & Ethics
    "https://en.wikipedia.org/wiki/Utilitarianism",
    "https://en.wikipedia.org/wiki/Deontology",
    "https://en.wikipedia.org/wiki/Virtue_ethics",
    "https://en.wikipedia.org/wiki/Applied_ethics",
    "https://en.wikipedia.org/wiki/Philosophy_of_language",
    "https://en.wikipedia.org/wiki/Aesthetics",
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
    print("EXPANDING LIBRARY TO 200+ DOCUMENTS")
    print(f"Adding {len(EXPANSION_URLS)} specialized topics")
    print("="*80 + "\n")

    added = 0
    failed = 0

    for i, url in enumerate(EXPANSION_URLS, 1):
        print(f"[{i:3d}/{len(EXPANSION_URLS)}] ", end="", flush=True)
        success, result = add_document(url)

        if success:
            print(f"✓ {result}")
            added += 1
        else:
            print(f"✗ {result}")
            failed += 1

        if i % 10 == 0:
            print(f"  → Progress: {added} added, {failed} failed\n")

        time.sleep(1.5)

    print("\n" + "="*80)
    print("EXPANSION COMPLETE")
    print("="*80)
    print(f"Successfully added: {added}/{len(EXPANSION_URLS)}")
    print(f"Failed: {failed}/{len(EXPANSION_URLS)}")
    if added + failed > 0:
        print(f"Success rate: {added/(added+failed)*100:.1f}%")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
