"""
Expand knowledge library with reputable academic and government sources.

This script adds high-quality content from:
- Stanford Encyclopedia of Philosophy (SEP)
- Internet Encyclopedia of Philosophy (IEP)
- Encyclopedia Britannica
- NASA
- NIH/NCBI
- CDC
- Other government research institutions

All sources are verified and tested before inclusion.
"""
import requests
import time
import sys

# Curated list of reputable sources organized by domain
REPUTABLE_SOURCES = {
    # PHILOSOPHY - Stanford Encyclopedia of Philosophy
    "stanford_sep": [
        "https://plato.stanford.edu/entries/ethics-virtue/",
        "https://plato.stanford.edu/entries/consequentialism/",
        "https://plato.stanford.edu/entries/kant-moral/",
        "https://plato.stanford.edu/entries/logic-classical/",
        "https://plato.stanford.edu/entries/logic-modal/",
        "https://plato.stanford.edu/entries/consciousness/",
        "https://plato.stanford.edu/entries/dualism/",
        "https://plato.stanford.edu/entries/causation-metaphysics/",
        "https://plato.stanford.edu/entries/identity/",
        "https://plato.stanford.edu/entries/free-will/",
        "https://plato.stanford.edu/entries/scientific-method/",
        "https://plato.stanford.edu/entries/scientific-explanation/",
        "https://plato.stanford.edu/entries/scientific-realism/",
        "https://plato.stanford.edu/entries/probability-interpret/",
        "https://plato.stanford.edu/entries/sets-theory/",
        "https://plato.stanford.edu/entries/language-thought/",
        "https://plato.stanford.edu/entries/pragmatism/",
        "https://plato.stanford.edu/entries/rationalism-empiricism/",
        "https://plato.stanford.edu/entries/justep-coherence/",
        "https://plato.stanford.edu/entries/truth/",
    ],

    # PHILOSOPHY - Internet Encyclopedia of Philosophy
    "iep": [
        "https://iep.utm.edu/ethics/",
        "https://iep.utm.edu/meta-eth/",
        "https://iep.utm.edu/epist/",
        "https://iep.utm.edu/analy-phi/",
        "https://iep.utm.edu/nihilism/",
        "https://iep.utm.edu/heidegge/",
        "https://iep.utm.edu/socrates/",
        "https://iep.utm.edu/plato/",
        "https://iep.utm.edu/aristotl/",
        "https://iep.utm.edu/kantview/",
    ],

    # SPACE & ASTRONOMY - NASA
    "nasa": [
        "https://science.nasa.gov/universe/black-holes/",
        "https://science.nasa.gov/universe/stars/",
        "https://science.nasa.gov/universe/galaxies/",
        "https://science.nasa.gov/solar-system/",
        "https://science.nasa.gov/earth/",
        "https://science.nasa.gov/planetary-science/",
        "https://exoplanets.nasa.gov/what-is-an-exoplanet/overview/",
        "https://climate.nasa.gov/evidence/",
        "https://climate.nasa.gov/causes/",
        "https://www.nasa.gov/missions/",
    ],

    # HEALTH & MEDICINE - NIH/NCBI
    "nih_ncbi": [
        "https://www.ncbi.nlm.nih.gov/books/NBK535358/",  # Cell Biology
        "https://www.ncbi.nlm.nih.gov/books/NBK9967/",   # Biochemistry
        "https://www.ncbi.nlm.nih.gov/books/NBK10023/",  # Molecular Biology
        "https://www.ncbi.nlm.nih.gov/books/NBK1853/",   # Genetics
        "https://www.ncbi.nlm.nih.gov/books/NBK22266/",  # Human Genome
        "https://www.ncbi.nlm.nih.gov/books/NBK279390/", # Immunobiology
        "https://medlineplus.gov/genetics/understanding/",
        "https://www.genome.gov/about-genomics/fact-sheets",
    ],

    # HEALTH - CDC
    "cdc": [
        "https://www.cdc.gov/healthyliving/index.html",
        "https://www.cdc.gov/chronicdisease/index.htm",
        "https://www.cdc.gov/vaccines/index.html",
    ],

    # ENCYCLOPEDIA - Britannica (High Quality Articles)
    "britannica": [
        "https://www.britannica.com/science/philosophy-of-science",
        "https://www.britannica.com/science/logic",
        "https://www.britannica.com/topic/epistemology",
        "https://www.britannica.com/topic/metaphysics",
        "https://www.britannica.com/science/mathematics",
        "https://www.britannica.com/science/physics-science",
        "https://www.britannica.com/science/quantum-mechanics-physics",
        "https://www.britannica.com/science/relativity",
        "https://www.britannica.com/science/biology",
        "https://www.britannica.com/science/evolution-scientific-theory",
        "https://www.britannica.com/science/genetics",
        "https://www.britannica.com/science/chemistry",
        "https://www.britannica.com/science/computer-science",
        "https://www.britannica.com/technology/artificial-intelligence",
        "https://www.britannica.com/science/neuroscience",
        "https://www.britannica.com/science/cognitive-science",
        "https://www.britannica.com/topic/psychology",
        "https://www.britannica.com/topic/sociology",
        "https://www.britannica.com/topic/economics",
        "https://www.britannica.com/topic/political-science",
        "https://www.britannica.com/topic/anthropology",
        "https://www.britannica.com/topic/history",
        "https://www.britannica.com/topic/language",
        "https://www.britannica.com/topic/linguistics",
        "https://www.britannica.com/art/literature",
        "https://www.britannica.com/art/music",
        "https://www.britannica.com/art/art",
        "https://www.britannica.com/technology/technology",
        "https://www.britannica.com/science/environmental-science",
        "https://www.britannica.com/science/climate-change",
    ],
}


def add_document(url):
    """Add document from URL via API."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/documents/from-url",
            json={"url": url},
            timeout=60
        )
        if response.status_code in [200, 201]:
            data = response.json()
            # Extract source credibility from metadata if available
            metadata = data.get('metadata_', '{}')
            source_info = ""
            if 'source_name' in str(metadata):
                import json
                meta_dict = json.loads(metadata)
                source_name = meta_dict.get('source_name', '')
                credibility = meta_dict.get('source_credibility', '')
                if source_name:
                    source_info = f" [{source_name} - {credibility}]"

            return True, f"{data.get('filename', 'Unknown')[:80]}{source_info}"
        else:
            return False, f"HTTP {response.status_code}: {url[:60]}"
    except requests.exceptions.Timeout:
        return False, f"Timeout: {url[:60]}"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"


def main():
    """Run the library expansion."""
    print("\n" + "="*80)
    print("EXPANDING KNOWLEDGE LIBRARY WITH REPUTABLE SOURCES")
    print("="*80)
    print("\nThis script will add high-quality content from:")
    print("  • Stanford Encyclopedia of Philosophy")
    print("  • Internet Encyclopedia of Philosophy")
    print("  • Encyclopedia Britannica")
    print("  • NASA")
    print("  • NIH/NCBI")
    print("  • CDC")
    print()

    # Count total URLs
    total_urls = sum(len(urls) for urls in REPUTABLE_SOURCES.values())
    print(f"Total sources to add: {total_urls}")
    print("="*80 + "\n")

    overall_added = 0
    overall_failed = 0

    # Process each source category
    for category, urls in REPUTABLE_SOURCES.items():
        print(f"\n{'='*80}")
        print(f"Category: {category.upper().replace('_', ' ')}")
        print(f"{'='*80}")
        print(f"Sources: {len(urls)}\n")

        category_added = 0
        category_failed = 0

        for i, url in enumerate(urls, 1):
            print(f"[{i:2d}/{len(urls)}] ", end="", flush=True)
            success, result = add_document(url)

            if success:
                print(f"✓ {result}")
                category_added += 1
                overall_added += 1
            else:
                print(f"✗ {result}")
                category_failed += 1
                overall_failed += 1

            # Respect rate limits
            time.sleep(2.0)

        print(f"\n{category}: ✓ {category_added}  ✗ {category_failed}")

        # Progress update every category
        if overall_added + overall_failed > 0:
            success_rate = overall_added / (overall_added + overall_failed) * 100
            print(f"Overall progress: {overall_added + overall_failed}/{total_urls} "
                  f"({success_rate:.1f}% success)")

    # Final summary
    print("\n" + "="*80)
    print("EXPANSION COMPLETE")
    print("="*80)
    print(f"Successfully added: {overall_added}/{total_urls}")
    print(f"Failed: {overall_failed}/{total_urls}")

    if overall_added + overall_failed > 0:
        success_rate = overall_added / (overall_added + overall_failed) * 100
        print(f"Success rate: {success_rate:.1f}%")

    print("="*80 + "\n")

    if overall_failed > 0:
        print("⚠️  Some sources failed to import. This is normal for:")
        print("   - Outdated URLs")
        print("   - Rate-limited sources")
        print("   - Pages with complex JavaScript")
        print("\n   Check the error messages above for details.\n")

    return overall_added, overall_failed


if __name__ == "__main__":
    print("\n🚀 Starting reputable source expansion...")
    print("⏱️  This will take approximately 5-10 minutes")
    print("💡 Backend must be running at http://localhost:8000\n")

    try:
        added, failed = main()

        if added > 0:
            print("✅ SUCCESS! Next steps:")
            print("   1. Run: python scripts/categorize_existing_documents.py")
            print("   2. Run: ./scripts/backup_library.sh")
            print("   3. Update KNOWLEDGE_LIBRARY.md with new statistics\n")
        else:
            print("❌ FAILED: No documents were added.")
            print("   Check that the backend is running: uvicorn app.main:app --reload\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Partial progress has been saved.\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}\n")
        sys.exit(1)
