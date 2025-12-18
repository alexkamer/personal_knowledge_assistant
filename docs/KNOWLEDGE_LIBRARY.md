# Knowledge Library Documentation

## Overview

The Personal Knowledge Assistant includes a comprehensive built-in knowledge library with **214 Wikipedia articles** covering all major domains of human knowledge. This library provides a solid foundation for AI-powered question answering without requiring extensive manual document uploads.

**Last Updated**: December 18, 2025

## Library Statistics

- **Total Documents**: 214
- **Total Size**: ~33MB (database backup)
- **Coverage**: 14 major academic categories
- **Source**: High-quality Wikipedia articles
- **Success Rate**: 100% (all documents successfully imported)

## Category Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| **Uncategorized** | 50 | 23.4% |
| **Computer Science & Technology** | 39 | 18.2% |
| **Physics & Astronomy** | 18 | 8.4% |
| **Biology & Life Sciences** | 18 | 8.4% |
| **Mathematics & Statistics** | 13 | 6.1% |
| **Philosophy & Logic** | 13 | 6.1% |
| **Psychology & Cognitive Science** | 11 | 5.1% |
| **Social Sciences** | 9 | 4.2% |
| **Chemistry & Materials** | 9 | 4.2% |
| **History & Humanities** | 8 | 3.7% |
| **Medicine & Health** | 8 | 3.7% |
| **Engineering** | 7 | 3.3% |
| **Earth & Environmental Science** | 6 | 2.8% |
| **Arts & Music** | 5 | 2.3% |

## Library Contents

### Computer Science & Technology (39 articles)
- **AI/ML**: Artificial Intelligence, Machine Learning, Deep Learning, Neural Networks, NLP, Computer Vision, Reinforcement Learning, Transformers, CNNs, RNNs, GANs, Large Language Models
- **Core CS**: Algorithms, Data Structures, Databases, Operating Systems, Computer Networks, Cryptography, Compilers, Formal Verification
- **Modern Tech**: Cloud Computing, Blockchain, Quantum Computing, Distributed Computing, Parallel Computing, IoT, 5G, Cybersecurity
- **Software**: Software Engineering, Programming Paradigms, OOP, Functional Programming, Computer Graphics, HCI

### Mathematics & Statistics (13 articles)
- **Foundations**: Mathematics, Calculus, Linear Algebra, Probability Theory, Statistics
- **Advanced**: Number Theory, Graph Theory, Topology, Abstract Algebra, Differential Equations, Real Analysis, Complex Analysis, Functional Analysis

### Physics & Astronomy (18 articles)
- **Classical**: Physics, Thermodynamics, Electromagnetism, Optics, Acoustics, Classical Mechanics
- **Modern**: Quantum Mechanics, General Relativity, Special Relativity, Quantum Field Theory
- **Specializations**: Particle Physics, Nuclear Physics, Atomic Physics, Condensed Matter Physics
- **Cosmology**: Astrophysics, Cosmology, Dark Matter, Dark Energy, Black Holes, Big Bang

### Chemistry & Materials (9 articles)
- Chemistry, Organic Chemistry, Inorganic Chemistry, Physical Chemistry, Analytical Chemistry
- Biochemistry, Quantum Chemistry, Electrochemistry, Polymer Chemistry

### Biology & Life Sciences (18 articles)
- **Foundational**: Biology, Genetics, Evolution, Cell Biology, Molecular Biology
- **Systems**: Neuroscience, Ecology, Microbiology, Immunology, Virology, Botany, Zoology
- **Advanced**: Epigenetics, Proteomics, Genomics, Bioinformatics, Synthetic Biology, CRISPR, Stem Cells

### Philosophy & Logic (13 articles)
- **Core**: Philosophy, Metaphysics, Epistemology, Ethics, Logic
- **Specializations**: Philosophy of Mind, Philosophy of Science, Philosophy of Language, Political Philosophy
- **Schools**: Existentialism, Phenomenology, Utilitarianism, Deontology, Virtue Ethics, Aesthetics

### Psychology & Cognitive Science (11 articles)
- Psychology, Cognitive Psychology, Developmental Psychology, Social Psychology, Behavioral Psychology
- Neuroscience (cross-listed with Biology)

### Social Sciences (9 articles)
- Sociology, Economics, Anthropology, Political Science
- Game Theory, Behavioral Economics, Macroeconomics, Microeconomics, International Relations

### History & Humanities (8 articles)
- History, World History, Ancient History, Medieval History, Modern History
- Renaissance, Literature, Theater

### Medicine & Health (8 articles)
- Medicine, Anatomy, Physiology, Pathology, Pharmacology
- Neurology, Cardiology, Oncology, Psychiatry, Public Health, Epidemiology, Vaccines

### Engineering (7 articles)
- Engineering, Mechanical Engineering, Electrical Engineering, Civil Engineering
- Chemical Engineering, Aerospace Engineering, Robotics

### Earth & Environmental Science (6 articles)
- Geology, Meteorology, Oceanography, Climate Change, Environmental Science
- Renewable Energy, Sustainable Development, Conservation Biology, Biodiversity, Ecosystems

### Arts & Music (5 articles)
- Art, Literature, Music, Architecture, Film, Photography, Dance, Classical Music, Modern Art

## Building & Maintaining the Library

### Initial Build

The library was built using automated scripts that fetch content from Wikipedia:

```bash
cd backend
source venv/bin/activate

# Build baseline library (107 articles)
python scripts/build_library_batch.py

# Expand with specialized topics (95 articles)
python scripts/expand_to_200plus.py

# Categorize all documents
python scripts/categorize_existing_documents.py
```

### Backup & Restore

**Create Backup**:
```bash
cd backend
./scripts/backup_library.sh
# Creates timestamped backup in backups/ directory
```

**Restore from Backup**:
```bash
cd backend
./scripts/restore_library.sh backups/knowledge_library_complete_214docs.sql
```

**Current Backups**:
- `backups/knowledge_library_baseline.sql` (19MB) - Initial 107 documents
- `backups/knowledge_library_complete_214docs.sql` (33MB) - Complete 214 documents

### Adding More Documents

You can expand the library in three ways:

1. **Via UI**: Use the "Add from URL" button on the Documents page
2. **Bulk Import**: Create a new script in `backend/scripts/` following the pattern of existing build scripts
3. **Manual Upload**: Upload PDF, TXT, MD, or DOCX files through the UI

### Auto-Categorization

All uploaded documents are automatically categorized using a keyword-based algorithm:

- **Service**: `app/services/categorization_service.py`
- **Categories**: 14 predefined categories
- **Algorithm**: Keyword matching with scoring
- **Manual Override**: Users can filter and organize by category in the UI

## Database Structure

The library is stored in PostgreSQL:

- **Database**: `knowledge_assistant`
- **Table**: `documents`
- **Location**: `/opt/homebrew/var/postgresql@18/`
- **Persistence**: Data persists across restarts
- **Embeddings**: Stored in ChromaDB for semantic search

## Usage in RAG System

The knowledge library integrates seamlessly with the RAG (Retrieval-Augmented Generation) pipeline:

1. **Query**: User asks a question
2. **Embedding**: Question is embedded using sentence-transformers
3. **Retrieval**: Top-K relevant chunks retrieved from ChromaDB
4. **Filtering**: Results filtered by source type (documents, notes, web)
5. **Re-ranking**: Cross-encoder re-ranks results
6. **Generation**: LLM generates answer with citations

Users can toggle whether to include personal notes or only use reputable sources (documents + web).

## Maintenance Tasks

### Regular Backups

Create backups after significant library updates:

```bash
./scripts/backup_library.sh
```

The script automatically keeps the 3 most recent backups.

### Disaster Recovery

If the database is lost or corrupted:

1. Recreate database: `createdb knowledge_assistant`
2. Run migrations: `uv run alembic upgrade head`
3. Restore backup: `psql knowledge_assistant < backups/knowledge_library_complete_214docs.sql`

### Expanding Categories

To add new categories or modify the categorization algorithm:

1. Edit `app/services/categorization_service.py`
2. Update `CATEGORIES` dictionary with keywords
3. Re-run categorization: `python scripts/categorize_existing_documents.py`

## Future Enhancements

Potential improvements to the knowledge library:

- [ ] Add academic sources (Stanford Encyclopedia, IEP, ArXiv papers)
- [ ] Include government resources (NASA, NIH, CDC)
- [ ] Add textbook content for deeper coverage
- [ ] Implement version control for document updates
- [ ] Add metadata tags for better organization
- [ ] Create topic-specific sub-libraries
- [ ] Support for multilingual content
- [ ] Automated quality scoring
- [ ] Citation tracking and validation

## Troubleshooting

### Documents Not Appearing

1. Check backend is running: `curl http://localhost:8000/api/v1/documents/`
2. Verify database connection: `psql knowledge_assistant -c "SELECT count(*) FROM documents;"`
3. Check ChromaDB data: `ls -la chroma_data/`

### Import Failures

- **Network issues**: Check internet connection
- **Timeout**: Increase timeout in scripts (default: 60s)
- **Rate limiting**: Add delays between requests (currently 1.5s)

### Category Issues

- **Wrong category**: Manually update via API or re-run categorization
- **Uncategorized**: Add keywords to `categorization_service.py` for your domain

## Contributing

To contribute to the knowledge library:

1. Add URLs to appropriate script in `backend/scripts/`
2. Test with small batch first
3. Run categorization script
4. Create backup
5. Document changes in this file
6. Commit with clear message

## License & Attribution

All content is sourced from Wikipedia under Creative Commons licenses. Each document retains its original license and attribution metadata.

---

**Maintained by**: Personal Knowledge Assistant Development Team
**Contact**: See main README.md for support information
