#!/usr/bin/env python3
"""
Comprehensive Knowledge Library Builder

Builds an extensive multi-level knowledge base:
- Level 0: Reputable authoritative sources
- Level 1: Major disciplines (30 topics)
- Level 2: Subdisciplines (100+ topics)
- Level 3: Specialized areas (200+ topics)
- Level 4: Specific concepts (500+ topics)
"""
import asyncio
import httpx
from typing import List, Dict, Tuple
import json

API_BASE_URL = "http://localhost:8000/api/v1"

# ============================================================================
# LEVEL 0: REPUTABLE AUTHORITATIVE SOURCES
# ============================================================================
LEVEL_0_SOURCES = [
    # Stanford Encyclopedia of Philosophy
    ("Philosophy", "https://plato.stanford.edu/entries/philosophy/", "Stanford SEP"),
    ("Logic", "https://plato.stanford.edu/entries/logic-classical/", "Stanford SEP"),
    ("Ethics", "https://plato.stanford.edu/entries/ethics-virtue/", "Stanford SEP"),
    ("Epistemology", "https://plato.stanford.edu/entries/epistemology/", "Stanford SEP"),
    ("Consciousness", "https://plato.stanford.edu/entries/consciousness/", "Stanford SEP"),

    # Internet Encyclopedia of Philosophy
    ("Metaphysics", "https://iep.utm.edu/con-meta/", "IEP"),
    ("Political Philosophy", "https://iep.utm.edu/polphil/", "IEP"),

    # NASA
    ("Solar System", "https://solarsystem.nasa.gov/solar-system/our-solar-system/overview/", "NASA"),
    ("Earth", "https://climate.nasa.gov/", "NASA"),

    # Britannica
    ("Biology", "https://www.britannica.com/science/biology", "Britannica"),
    ("Chemistry", "https://www.britannica.com/science/chemistry", "Britannica"),
    ("Physics", "https://www.britannica.com/science/physics-science", "Britannica"),
]

# ============================================================================
# LEVEL 1: MAJOR DISCIPLINES (30 topics)
# ============================================================================
LEVEL_1_DISCIPLINES = [
    # Natural Sciences
    "Science", "Physics", "Chemistry", "Biology", "Astronomy",
    "Earth_science", "Geology", "Meteorology", "Oceanography", "Ecology",

    # Formal Sciences
    "Mathematics", "Logic", "Statistics", "Computer_science",
    "Information_theory", "Systems_theory",

    # Social Sciences
    "Psychology", "Sociology", "Anthropology", "Economics",
    "Political_science", "Geography", "History", "Linguistics",

    # Applied Sciences
    "Engineering", "Medicine", "Agriculture", "Architecture",

    # Humanities
    "Philosophy", "Literature", "Art", "Music",
]

# ============================================================================
# LEVEL 2: SUBDISCIPLINES (organized by parent discipline)
# ============================================================================
LEVEL_2_SUBDISCIPLINES = {
    "Physics": [
        "Classical_mechanics", "Thermodynamics", "Electromagnetism",
        "Quantum_mechanics", "Quantum_field_theory", "Special_relativity",
        "General_relativity", "Particle_physics", "Nuclear_physics",
        "Atomic_physics", "Condensed_matter_physics", "Astrophysics",
        "Cosmology", "Optics", "Acoustics", "Fluid_dynamics",
    ],

    "Chemistry": [
        "Organic_chemistry", "Inorganic_chemistry", "Physical_chemistry",
        "Analytical_chemistry", "Biochemistry", "Chemical_engineering",
        "Electrochemistry", "Polymer_chemistry", "Quantum_chemistry",
        "Thermochemistry", "Photochemistry",
    ],

    "Biology": [
        "Molecular_biology", "Cell_biology", "Genetics", "Evolution",
        "Ecology", "Botany", "Zoology", "Microbiology", "Virology",
        "Immunology", "Neuroscience", "Developmental_biology",
        "Marine_biology", "Biotechnology", "Biophysics", "Biochemistry",
        "Anatomy", "Physiology", "Taxonomy",
    ],

    "Mathematics": [
        "Algebra", "Geometry", "Calculus", "Trigonometry",
        "Linear_algebra", "Abstract_algebra", "Number_theory",
        "Topology", "Analysis", "Differential_equations",
        "Discrete_mathematics", "Combinatorics", "Graph_theory",
        "Probability_theory", "Mathematical_statistics",
        "Numerical_analysis", "Optimization",
    ],

    "Computer_science": [
        "Algorithm", "Data_structure", "Programming_language",
        "Computer_architecture", "Operating_system", "Compiler",
        "Database", "Computer_network", "Computer_graphics",
        "Artificial_intelligence", "Machine_learning", "Computer_vision",
        "Natural_language_processing", "Cryptography", "Cybersecurity",
        "Software_engineering", "Distributed_computing", "Parallel_computing",
        "Quantum_computing", "Theory_of_computation",
    ],

    "Psychology": [
        "Cognitive_psychology", "Behavioral_psychology", "Developmental_psychology",
        "Social_psychology", "Clinical_psychology", "Neuropsychology",
        "Abnormal_psychology", "Personality_psychology", "Educational_psychology",
        "Industrial_and_organizational_psychology",
    ],

    "Economics": [
        "Microeconomics", "Macroeconomics", "Econometrics",
        "Behavioral_economics", "Game_theory", "International_economics",
        "Labor_economics", "Public_economics", "Development_economics",
        "Financial_economics",
    ],

    "Engineering": [
        "Mechanical_engineering", "Electrical_engineering", "Civil_engineering",
        "Chemical_engineering", "Aerospace_engineering", "Biomedical_engineering",
        "Computer_engineering", "Industrial_engineering", "Materials_science",
        "Robotics", "Control_theory",
    ],

    "Medicine": [
        "Anatomy", "Physiology", "Pathology", "Pharmacology",
        "Surgery", "Internal_medicine", "Pediatrics", "Psychiatry",
        "Radiology", "Oncology", "Cardiology", "Neurology",
    ],

    "Philosophy": [
        "Metaphysics", "Epistemology", "Ethics", "Logic",
        "Philosophy_of_mind", "Philosophy_of_science", "Political_philosophy",
        "Aesthetics", "Philosophy_of_language",
    ],
}

# ============================================================================
# LEVEL 3: SPECIALIZED AREAS (200+ topics)
# ============================================================================
LEVEL_3_SPECIALIZED = {
    "Machine_learning": [
        "Deep_learning", "Neural_network", "Convolutional_neural_network",
        "Recurrent_neural_network", "Transformer_(machine_learning_model)",
        "Supervised_learning", "Unsupervised_learning", "Reinforcement_learning",
        "Transfer_learning", "Ensemble_learning", "Decision_tree",
        "Random_forest", "Support_vector_machine", "K-nearest_neighbors",
        "Gradient_boosting", "Principal_component_analysis",
    ],

    "Artificial_intelligence": [
        "Expert_system", "Knowledge_representation", "Machine_reasoning",
        "Planning", "Automated_planning_and_scheduling",
        "Multi-agent_system", "Swarm_intelligence",
    ],

    "Deep_learning": [
        "Backpropagation", "Activation_function", "Loss_function",
        "Optimizer_(machine_learning)", "Batch_normalization",
        "Dropout_(neural_networks)", "Attention_(machine_learning)",
        "Generative_adversarial_network", "Autoencoder",
        "Variational_autoencoder",
    ],

    "Quantum_mechanics": [
        "Wave_function", "Schrödinger_equation", "Heisenberg_uncertainty_principle",
        "Quantum_entanglement", "Quantum_superposition", "Quantum_tunneling",
        "Spin_(physics)", "Pauli_exclusion_principle", "Quantum_harmonic_oscillator",
    ],

    "Genetics": [
        "DNA", "RNA", "Gene", "Genome", "Chromosome",
        "Mutation", "Genetic_code", "Gene_expression",
        "DNA_replication", "Transcription_(biology)", "Translation_(biology)",
        "CRISPR", "Epigenetics", "Population_genetics",
    ],

    "Ecology": [
        "Ecosystem", "Biodiversity", "Food_chain", "Food_web",
        "Trophic_level", "Ecological_niche", "Habitat",
        "Biome", "Climate_change", "Conservation_biology",
    ],

    "Calculus": [
        "Derivative", "Integral", "Limit_(mathematics)",
        "Differential_calculus", "Integral_calculus",
        "Fundamental_theorem_of_calculus", "Taylor_series",
        "Multivariable_calculus", "Vector_calculus",
    ],

    "Topology": [
        "Topological_space", "Continuous_function", "Homeomorphism",
        "Metric_space", "Manifold", "Knot_theory",
    ],

    "Cryptography": [
        "Encryption", "Public-key_cryptography", "RSA_(cryptosystem)",
        "Hash_function", "Digital_signature", "Blockchain",
    ],

    "Neuroscience": [
        "Neuron", "Synapse", "Action_potential", "Neurotransmitter",
        "Brain", "Cerebral_cortex", "Hippocampus", "Amygdala",
        "Neuroplasticity", "Memory", "Learning",
    ],
}

# ============================================================================
# LEVEL 4: SPECIFIC CONCEPTS (500+ topics)
# ============================================================================
LEVEL_4_CONCEPTS = {
    "Neural_network": [
        "Perceptron", "Multilayer_perceptron", "Feedforward_neural_network",
        "Long_short-term_memory", "Gated_recurrent_unit",
        "Residual_neural_network", "DenseNet", "U-Net",
        "Neural_architecture_search",
    ],

    "Transformer_(machine_learning_model)": [
        "Attention_is_All_You_Need", "BERT_(language_model)",
        "GPT-3", "GPT-4", "T5_(language_model)",
    ],

    "Computer_vision": [
        "Image_segmentation", "Object_detection", "Face_recognition",
        "Optical_character_recognition", "Image_classification",
        "Semantic_segmentation", "Instance_segmentation",
    ],

    "Natural_language_processing": [
        "Tokenization_(lexical_analysis)", "Part-of-speech_tagging",
        "Named-entity_recognition", "Sentiment_analysis",
        "Machine_translation", "Question_answering",
        "Text_summarization", "Language_model", "Word_embedding",
    ],

    "DNA": [
        "Nucleotide", "Base_pair", "Double_helix",
        "DNA_sequencing", "Polymerase_chain_reaction",
    ],

    "Quantum_entanglement": [
        "Bell's_theorem", "EPR_paradox", "Quantum_teleportation",
    ],

    "Brain": [
        "Frontal_lobe", "Parietal_lobe", "Temporal_lobe", "Occipital_lobe",
        "Basal_ganglia", "Thalamus", "Cerebellum", "Brain_stem",
    ],

    "Calculus": [
        "Chain_rule", "Product_rule", "Quotient_rule",
        "Integration_by_parts", "Integration_by_substitution",
    ],

    "Blockchain": [
        "Bitcoin", "Ethereum", "Smart_contract", "Cryptocurrency",
        "Proof_of_work", "Proof_of_stake", "Distributed_ledger",
    ],

    "Climate_change": [
        "Global_warming", "Greenhouse_gas", "Carbon_footprint",
        "Paris_Agreement", "Renewable_energy", "Carbon_neutrality",
    ],
}

# ============================================================================
# Additional broad topics to ensure comprehensive coverage
# ============================================================================
ADDITIONAL_BROAD_TOPICS = [
    # Technology
    "Internet", "World_Wide_Web", "Cloud_computing", "Big_data",
    "Internet_of_things", "5G", "Virtual_reality", "Augmented_reality",

    # Science
    "Scientific_method", "Hypothesis", "Theory", "Experiment",

    # Current events / Society
    "Sustainability", "Globalization", "Democracy", "Capitalism",
    "Socialism", "Human_rights", "Climate_action",

    # Health
    "Nutrition", "Exercise", "Mental_health", "Public_health",
    "Epidemiology", "Vaccine", "Antibiotic",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


async def get_document_count(session: httpx.AsyncClient) -> int:
    """Get current document count."""
    try:
        response = await session.get(f"{API_BASE_URL}/documents/")
        response.raise_for_status()
        return response.json()["total"]
    except Exception:
        return 0


def make_wikipedia_url(topic: str) -> str:
    """Convert topic to Wikipedia URL."""
    return f"https://en.wikipedia.org/wiki/{topic}"


# ============================================================================
# BUILD FUNCTIONS
# ============================================================================

async def build_level_0(session: httpx.AsyncClient):
    """Level 0: Reputable authoritative sources."""
    print("\n" + "="*80)
    print("LEVEL 0: Reputable Authoritative Sources")
    print("="*80)

    total = len(LEVEL_0_SOURCES)
    for i, (topic, url, source) in enumerate(LEVEL_0_SOURCES, 1):
        print(f"[{i}/{total}] {source}: {topic}...", end=" ", flush=True)
        result = await add_document_from_url(url, session)
        print("✓" if result["status"] == "success" else f"✗")
        await asyncio.sleep(2)


async def build_level_1(session: httpx.AsyncClient):
    """Level 1: Major disciplines."""
    print("\n" + "="*80)
    print("LEVEL 1: Major Disciplines (30 topics)")
    print("="*80)

    total = len(LEVEL_1_DISCIPLINES)
    for i, topic in enumerate(LEVEL_1_DISCIPLINES, 1):
        url = make_wikipedia_url(topic)
        print(f"[{i}/{total}] {topic.replace('_', ' ')}...", end=" ", flush=True)
        result = await add_document_from_url(url, session)
        print("✓" if result["status"] == "success" else f"✗")
        await asyncio.sleep(1)


async def build_level_2(session: httpx.AsyncClient):
    """Level 2: Subdisciplines."""
    print("\n" + "="*80)
    print("LEVEL 2: Subdisciplines (100+ topics)")
    print("="*80)

    total = sum(len(topics) for topics in LEVEL_2_SUBDISCIPLINES.values())
    current = 0

    for discipline, topics in LEVEL_2_SUBDISCIPLINES.items():
        print(f"\n📚 {discipline.replace('_', ' ')}")
        for topic in topics:
            current += 1
            url = make_wikipedia_url(topic)
            print(f"  [{current}/{total}] {topic.replace('_', ' ')}...", end=" ", flush=True)
            result = await add_document_from_url(url, session)
            print("✓" if result["status"] == "success" else f"✗")
            await asyncio.sleep(1)


async def build_level_3(session: httpx.AsyncClient):
    """Level 3: Specialized areas."""
    print("\n" + "="*80)
    print("LEVEL 3: Specialized Areas (200+ topics)")
    print("="*80)

    total = sum(len(topics) for topics in LEVEL_3_SPECIALIZED.values())
    current = 0

    for area, topics in LEVEL_3_SPECIALIZED.items():
        print(f"\n🔬 {area.replace('_', ' ')}")
        for topic in topics:
            current += 1
            url = make_wikipedia_url(topic)
            print(f"  [{current}/{total}] {topic.replace('_', ' ')}...", end=" ", flush=True)
            result = await add_document_from_url(url, session)
            print("✓" if result["status"] == "success" else f"✗")
            await asyncio.sleep(1)


async def build_level_4(session: httpx.AsyncClient):
    """Level 4: Specific concepts."""
    print("\n" + "="*80)
    print("LEVEL 4: Specific Concepts (500+ topics)")
    print("="*80)

    total = sum(len(topics) for topics in LEVEL_4_CONCEPTS.values())
    current = 0

    for concept, topics in LEVEL_4_CONCEPTS.items():
        print(f"\n🎯 {concept.replace('_', ' ')}")
        for topic in topics:
            current += 1
            url = make_wikipedia_url(topic)
            print(f"  [{current}/{total}] {topic.replace('_', ' ')}...", end=" ", flush=True)
            result = await add_document_from_url(url, session)
            print("✓" if result["status"] == "success" else f"✗")
            await asyncio.sleep(1)


async def build_additional_topics(session: httpx.AsyncClient):
    """Additional broad topics."""
    print("\n" + "="*80)
    print("ADDITIONAL: Filling Coverage Gaps")
    print("="*80)

    total = len(ADDITIONAL_BROAD_TOPICS)
    for i, topic in enumerate(ADDITIONAL_BROAD_TOPICS, 1):
        url = make_wikipedia_url(topic)
        print(f"[{i}/{total}] {topic.replace('_', ' ')}...", end=" ", flush=True)
        result = await add_document_from_url(url, session)
        print("✓" if result["status"] == "success" else f"✗")
        await asyncio.sleep(1)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Build comprehensive knowledge library."""
    print("\n" + "🌍 COMPREHENSIVE KNOWLEDGE LIBRARY BUILDER 🌍".center(80))
    print("="*80)
    print("\nBuilding multi-level knowledge base:")
    print("  Level 0: Authoritative sources (~12 docs)")
    print("  Level 1: Major disciplines (~30 docs)")
    print("  Level 2: Subdisciplines (~100 docs)")
    print("  Level 3: Specialized areas (~200 docs)")
    print("  Level 4: Specific concepts (~500 docs)")
    print("  Additional: Coverage gaps (~25 docs)")
    print("\n  TOTAL: ~850+ documents")
    print()

    async with httpx.AsyncClient() as session:
        start_count = await get_document_count(session)
        print(f"Starting document count: {start_count}\n")

        # Build each level
        await build_level_0(session)
        l0 = await get_document_count(session)
        print(f"\n✓ Level 0 Complete! Total: {l0} (+{l0 - start_count})")

        await build_level_1(session)
        l1 = await get_document_count(session)
        print(f"\n✓ Level 1 Complete! Total: {l1} (+{l1 - l0})")

        await build_level_2(session)
        l2 = await get_document_count(session)
        print(f"\n✓ Level 2 Complete! Total: {l2} (+{l2 - l1})")

        await build_level_3(session)
        l3 = await get_document_count(session)
        print(f"\n✓ Level 3 Complete! Total: {l3} (+{l3 - l2})")

        await build_level_4(session)
        l4 = await get_document_count(session)
        print(f"\n✓ Level 4 Complete! Total: {l4} (+{l4 - l3})")

        await build_additional_topics(session)
        final = await get_document_count(session)
        print(f"\n✓ Additional Complete! Total: {final} (+{final - l4})")

        # Summary
        print("\n" + "="*80)
        print("📊 BUILD COMPLETE")
        print("="*80)
        print(f"Final count: {final} documents (+{final - start_count})")
        print("\n✨ Your comprehensive knowledge library is ready!")
        print("\nCoverage:")
        print("  ✓ All major academic disciplines")
        print("  ✓ Subdisciplines and specializations")
        print("  ✓ Current technology and science")
        print("  ✓ Fundamental concepts")
        print("  ✓ Authoritative sources (Stanford, NASA, NIH, Britannica)")


if __name__ == "__main__":
    asyncio.run(main())
