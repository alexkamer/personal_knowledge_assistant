"""
Contradiction Detection Service

Scans knowledge base for logical contradictions and inconsistencies.
Helps users maintain intellectual honesty and rigorous thinking.
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.note import Note
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ContradictionItem:
    """Represents a detected contradiction between two pieces of content."""

    def __init__(
        self,
        source1_type: str,
        source1_id: str,
        source1_title: str,
        source1_excerpt: str,
        source2_type: str,
        source2_id: str,
        source2_title: str,
        source2_excerpt: str,
        contradiction_type: str,
        explanation: str,
        severity: str,  # "high", "medium", "low"
        confidence: float  # 0.0 to 1.0
    ):
        self.source1_type = source1_type
        self.source1_id = source1_id
        self.source1_title = source1_title
        self.source1_excerpt = source1_excerpt
        self.source2_type = source2_type
        self.source2_id = source2_id
        self.source2_title = source2_title
        self.source2_excerpt = source2_excerpt
        self.contradiction_type = contradiction_type
        self.explanation = explanation
        self.severity = severity
        self.confidence = confidence

    def to_dict(self) -> Dict:
        return {
            "source1": {
                "type": self.source1_type,
                "id": self.source1_id,
                "title": self.source1_title,
                "excerpt": self.source1_excerpt
            },
            "source2": {
                "type": self.source2_type,
                "id": self.source2_id,
                "title": self.source2_title,
                "excerpt": self.source2_excerpt
            },
            "contradiction_type": self.contradiction_type,
            "explanation": self.explanation,
            "severity": self.severity,
            "confidence": self.confidence
        }


class ContradictionDetectionService:
    """Service for detecting contradictions in knowledge base."""

    def __init__(self, llm_service: LLMService, rag_service: RAGService):
        self.llm_service = llm_service
        self.rag_service = rag_service

    async def detect_contradictions_for_source(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str,
        top_k: int = 5
    ) -> List[ContradictionItem]:
        """
        Detect contradictions for a specific source by finding semantically
        similar content and analyzing for logical inconsistencies.

        Args:
            db: Database session
            source_type: Type of source ("note", "document")
            source_id: ID of the source
            top_k: Number of similar sources to check

        Returns:
            List of detected contradictions
        """
        try:
            # Get the source content
            source_content = await self._get_source_content(db, source_type, source_id)
            if not source_content:
                return []

            # Find semantically similar content using RAG
            similar_chunks = await self.rag_service.search_relevant_chunks(
                query=source_content["text"][:1000],  # Use first 1000 chars
                top_k=top_k * 3,  # Get more to have options
                source_type=None  # Search all types
            )

            # Group chunks by source
            similar_sources = self._group_chunks_by_source(similar_chunks, source_id)

            # Limit to top_k sources
            similar_sources = similar_sources[:top_k]

            # Analyze each similar source for contradictions
            contradictions = []
            for similar_source in similar_sources:
                contradiction = await self._analyze_for_contradiction(
                    db,
                    source_content,
                    similar_source
                )
                if contradiction:
                    contradictions.append(contradiction)

            return contradictions

        except Exception as e:
            logger.error(f"Error detecting contradictions for {source_type}/{source_id}: {e}", exc_info=True)
            return []

    async def _get_source_content(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str
    ) -> Optional[Dict[str, str]]:
        """Get the content of a source."""
        try:
            if source_type == "note":
                result = await db.execute(
                    select(Note).where(Note.id == source_id)
                )
                note = result.scalar_one_or_none()
                if note:
                    return {
                        "type": "note",
                        "id": str(note.id),
                        "title": note.title or "Untitled",
                        "text": note.content or ""
                    }

            elif source_type == "document":
                result = await db.execute(
                    select(Document).where(Document.id == source_id)
                )
                document = result.scalar_one_or_none()
                if document:
                    return {
                        "type": "document",
                        "id": str(document.id),
                        "title": document.filename,
                        "text": document.extracted_text or ""
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting source content: {e}", exc_info=True)
            return None

    def _group_chunks_by_source(
        self,
        chunks: List[Dict],
        exclude_source_id: str
    ) -> List[Dict[str, str]]:
        """Group chunks by their source and exclude the original source."""
        sources_map = {}

        for chunk in chunks:
            source_type = chunk.get("source_type")
            source_id = chunk.get("source_id")

            # Skip the source we're analyzing
            if source_id == exclude_source_id:
                continue

            key = f"{source_type}:{source_id}"
            if key not in sources_map:
                sources_map[key] = {
                    "type": source_type,
                    "id": source_id,
                    "title": chunk.get("source_title", ""),
                    "chunks": []
                }

            sources_map[key]["chunks"].append(chunk.get("text", ""))

        # Convert to list and combine chunks
        sources = []
        for source_data in sources_map.values():
            sources.append({
                "type": source_data["type"],
                "id": source_data["id"],
                "title": source_data["title"],
                "text": " ".join(source_data["chunks"][:3])  # Use first 3 chunks
            })

        return sources

    async def _analyze_for_contradiction(
        self,
        db: AsyncSession,
        source1: Dict[str, str],
        source2: Dict[str, str]
    ) -> Optional[ContradictionItem]:
        """
        Use LLM to analyze two sources for contradictions.

        Returns ContradictionItem if contradiction found, None otherwise.
        """
        try:
            # Build prompt for contradiction detection
            prompt = f"""Analyze these two pieces of content for logical contradictions or inconsistencies.

Source 1 - {source1['title']}:
{source1['text'][:800]}

Source 2 - {source2['title']}:
{source2['text'][:800]}

Task: Determine if there are any contradictions between these sources.

A contradiction exists when:
1. Both sources make claims about the same topic
2. The claims are mutually exclusive or logically incompatible
3. It's not just a matter of emphasis or perspective

Respond in this EXACT format:
CONTRADICTION: [YES or NO]
TYPE: [factual/methodological/conceptual/temporal/none]
SEVERITY: [high/medium/low/none]
CONFIDENCE: [0.0-1.0]
EXCERPT1: [short quote from source 1]
EXCERPT2: [short quote from source 2]
EXPLANATION: [one-sentence explanation of the contradiction]

Be rigorous. Only flag genuine contradictions, not different perspectives or complementary information."""

            # Use LLM to analyze
            response = await self.llm_service.generate_answer(
                query=prompt,
                context="",
                conversation_history=[],
                model="qwen2.5:14b",
                temperature=0.3,  # Lower temp for more consistent analysis
                system_prompt="You are a critical thinking expert who identifies logical contradictions. Be precise and only flag genuine contradictions."
            )

            # Parse the response
            parsed = self._parse_contradiction_response(response)

            if parsed and parsed["has_contradiction"]:
                return ContradictionItem(
                    source1_type=source1["type"],
                    source1_id=source1["id"],
                    source1_title=source1["title"],
                    source1_excerpt=parsed["excerpt1"],
                    source2_type=source2["type"],
                    source2_id=source2["id"],
                    source2_title=source2["title"],
                    source2_excerpt=parsed["excerpt2"],
                    contradiction_type=parsed["type"],
                    explanation=parsed["explanation"],
                    severity=parsed["severity"],
                    confidence=parsed["confidence"]
                )

            return None

        except Exception as e:
            logger.error(f"Error analyzing contradiction: {e}", exc_info=True)
            return None

    def _parse_contradiction_response(self, response: str) -> Optional[Dict]:
        """Parse the LLM response for contradiction detection."""
        try:
            lines = response.strip().split("\n")
            parsed = {}

            for line in lines:
                if line.startswith("CONTRADICTION:"):
                    parsed["has_contradiction"] = "YES" in line.upper()
                elif line.startswith("TYPE:"):
                    parsed["type"] = line.split(":", 1)[1].strip()
                elif line.startswith("SEVERITY:"):
                    parsed["severity"] = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        parsed["confidence"] = float(line.split(":", 1)[1].strip())
                    except:
                        parsed["confidence"] = 0.5
                elif line.startswith("EXCERPT1:"):
                    parsed["excerpt1"] = line.split(":", 1)[1].strip()
                elif line.startswith("EXCERPT2:"):
                    parsed["excerpt2"] = line.split(":", 1)[1].strip()
                elif line.startswith("EXPLANATION:"):
                    parsed["explanation"] = line.split(":", 1)[1].strip()

            # Validate required fields
            if not parsed.get("has_contradiction"):
                return None

            # Set defaults for missing fields
            parsed.setdefault("type", "unknown")
            parsed.setdefault("severity", "medium")
            parsed.setdefault("confidence", 0.5)
            parsed.setdefault("excerpt1", "")
            parsed.setdefault("excerpt2", "")
            parsed.setdefault("explanation", "Potential contradiction detected")

            return parsed

        except Exception as e:
            logger.error(f"Error parsing contradiction response: {e}", exc_info=True)
            return None
