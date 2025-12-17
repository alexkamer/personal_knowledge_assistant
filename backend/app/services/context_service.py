"""
Context Intelligence Service.

Finds related content across YouTube videos, notes, and documents,
generates AI-powered synthesis, and suggests relevant questions.
"""
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.note import Note
from app.models.youtube_video import YouTubeVideo
from app.schemas.context import RelatedContentItem
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import LLMService, get_llm_service
from app.services.vector_service import get_vector_service

logger = logging.getLogger(__name__)


class ContextSynthesisService:
    """Service for generating contextual intelligence across content types."""

    def __init__(self):
        """Initialize the context synthesis service."""
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()
        self.llm_service = get_llm_service()

    async def get_related_content(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str,
        top_k: int = 5,
    ) -> List[RelatedContentItem]:
        """
        Find semantically related content across all source types.

        Steps:
        1. Fetch source content (note/document/youtube)
        2. Generate embedding for source
        3. Search ChromaDB for similar chunks (all source types)
        4. Group by (source_type, source_id) and rank
        5. Return top K related items with similarity scores

        Args:
            db: Database session
            source_type: Type of source ("note", "document", or "youtube")
            source_id: ID of the source
            top_k: Number of related items to return

        Returns:
            List of related content items with similarity scores
        """
        try:
            # Step 1: Fetch source content
            source_content = await self._fetch_source_content(
                db, source_type, source_id
            )
            if not source_content:
                logger.warning(
                    f"Source content not found: {source_type}/{source_id}"
                )
                return []

            source_text = source_content.get("text", "")
            source_title = source_content.get("title", "Unknown")

            if not source_text:
                logger.warning(f"Empty content for {source_type}/{source_id}")
                return []

            # Step 2: Generate embedding for source content
            # Use first 1000 chars to avoid token limits
            query_text = source_text[:1000]
            query_embedding = self.embedding_service.embed(query_text)

            # Step 3: Search ChromaDB for similar chunks (all source types)
            # Retrieve more results than top_k to account for grouping
            search_results = await self.vector_service.search_similar_chunks(
                query_embedding=query_embedding,
                n_results=top_k * 5,  # Get 5x to have enough after grouping
            )

            # Step 4: Group by (source_type, source_id) and aggregate
            grouped_results = await self._group_and_rank_results(
                db, search_results, source_type, source_id
            )

            # Step 5: Return top K items
            return grouped_results[:top_k]

        except Exception as e:
            logger.error(
                f"Error finding related content for {source_type}/{source_id}: {e}",
                exc_info=True,
            )
            return []

    async def _fetch_source_content(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str,
    ) -> Optional[Dict[str, str]]:
        """
        Fetch the content and title of a source.

        Args:
            db: Database session
            source_type: Type of source
            source_id: ID of the source

        Returns:
            Dict with "title" and "text" keys, or None if not found
        """
        try:
            if source_type == "note":
                result = await db.execute(
                    select(Note).where(Note.id == source_id)
                )
                note = result.scalar_one_or_none()
                if note:
                    return {"title": note.title, "text": note.content}

            elif source_type == "document":
                result = await db.execute(
                    select(Document).where(Document.id == source_id)
                )
                document = result.scalar_one_or_none()
                if document:
                    return {"title": document.filename, "text": document.content}

            elif source_type == "youtube":
                result = await db.execute(
                    select(YouTubeVideo).where(YouTubeVideo.id == source_id)
                )
                video = result.scalar_one_or_none()
                if video:
                    # Get all chunks for the video and concatenate
                    chunk_result = await db.execute(
                        select(Chunk.content)
                        .where(Chunk.youtube_video_id == source_id)
                        .order_by(Chunk.chunk_index)
                    )
                    chunks = chunk_result.scalars().all()
                    text = " ".join(chunks) if chunks else ""
                    return {"title": video.title, "text": text}

            return None

        except Exception as e:
            logger.error(
                f"Error fetching source content {source_type}/{source_id}: {e}"
            )
            return None

    async def _group_and_rank_results(
        self,
        db: AsyncSession,
        search_results: dict,
        exclude_source_type: str,
        exclude_source_id: str,
    ) -> List[RelatedContentItem]:
        """
        Group search results by source and rank by similarity.

        Args:
            db: Database session
            search_results: Raw ChromaDB search results
            exclude_source_type: Source type to exclude (the current source)
            exclude_source_id: Source ID to exclude (the current source)

        Returns:
            List of RelatedContentItem sorted by similarity
        """
        # Extract results
        ids = search_results["ids"][0] if search_results["ids"] else []
        distances = (
            search_results["distances"][0] if search_results["distances"] else []
        )
        metadatas = (
            search_results["metadatas"][0] if search_results["metadatas"] else []
        )
        documents = (
            search_results["documents"][0] if search_results["documents"] else []
        )

        if not ids:
            return []

        # Group by (source_type, source_id)
        grouped = defaultdict(
            lambda: {
                "source_type": "",
                "source_id": "",
                "chunk_ids": [],
                "min_distance": float("inf"),
                "preview": "",
                "timestamp": None,
            }
        )

        for chunk_id, distance, metadata, document in zip(
            ids, distances, metadatas, documents
        ):
            source_type = metadata.get("source_type")
            source_id = metadata.get("source_id")

            # Skip the current source
            if (
                source_type == exclude_source_type
                and source_id == exclude_source_id
            ):
                continue

            key = (source_type, source_id)

            # Initialize or update group
            if not grouped[key]["source_type"]:
                grouped[key]["source_type"] = source_type
                grouped[key]["source_id"] = source_id
                grouped[key]["preview"] = document[:200] if document else ""
                grouped[key]["timestamp"] = metadata.get("timestamp")

            grouped[key]["chunk_ids"].append(chunk_id)
            grouped[key]["min_distance"] = min(
                grouped[key]["min_distance"], distance
            )

        # Fetch source titles
        related_items = []
        for key, data in grouped.items():
            source_type = data["source_type"]
            source_id = data["source_id"]

            # Fetch title
            title = await self._fetch_source_title(db, source_type, source_id)

            # Convert distance to similarity score (1 - normalized_distance)
            # ChromaDB distances are L2, typically in range [0, 2]
            # Normalize to [0, 1] and invert
            similarity_score = max(0.0, 1.0 - (data["min_distance"] / 2.0))

            related_items.append(
                RelatedContentItem(
                    source_type=source_type,
                    source_id=source_id,
                    source_title=title,
                    similarity_score=round(similarity_score, 3),
                    preview=data["preview"],
                    timestamp=data["timestamp"],
                    chunk_count=len(data["chunk_ids"]),
                )
            )

        # Sort by similarity score (descending)
        related_items.sort(key=lambda x: x.similarity_score, reverse=True)

        return related_items

    async def _fetch_source_title(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str,
    ) -> str:
        """
        Fetch the title of a source.

        Args:
            db: Database session
            source_type: Type of source
            source_id: ID of the source

        Returns:
            Title string or "Unknown [Type]"
        """
        try:
            if source_type == "note":
                result = await db.execute(
                    select(Note.title).where(Note.id == source_id)
                )
                title = result.scalar_one_or_none()
                return title or "Unknown Note"

            elif source_type == "document":
                result = await db.execute(
                    select(Document.filename).where(Document.id == source_id)
                )
                filename = result.scalar_one_or_none()
                return filename or "Unknown Document"

            elif source_type == "youtube":
                result = await db.execute(
                    select(YouTubeVideo.title).where(YouTubeVideo.id == source_id)
                )
                title = result.scalar_one_or_none()
                return title or "Unknown Video"

            return f"Unknown {source_type.title()}"

        except Exception as e:
            logger.error(f"Error fetching title for {source_type}/{source_id}: {e}")
            return f"Unknown {source_type.title()}"

    async def generate_synthesis(
        self,
        db: AsyncSession,
        current_content: Dict[str, str],
        related_content: List[RelatedContentItem],
        synthesis_type: str = "connections",
    ) -> str:
        """
        Use LLM to generate intelligent synthesis.

        Args:
            db: Database session
            current_content: Dict with "title" and "text" of current source
            related_content: List of related items
            synthesis_type: Type of synthesis ("connections", "comparison", "gaps")

        Returns:
            Generated synthesis text
        """
        if not related_content:
            return ""

        try:
            # Build context with related content
            related_summaries = []
            for idx, item in enumerate(related_content[:3], 1):  # Top 3 items
                source_label = {
                    "note": "Note",
                    "document": "Document",
                    "youtube": "YouTube Video",
                }.get(item.source_type, "Content")

                preview_text = item.preview[:200] if item.preview else ""
                related_summaries.append(
                    f"{idx}. {source_label}: \"{item.source_title}\" "
                    f"(similarity: {item.similarity_score:.2f})\n"
                    f"   Preview: {preview_text}..."
                )

            related_context = "\n\n".join(related_summaries)

            # Build synthesis prompt based on type
            if synthesis_type == "connections":
                prompt = f"""Analyze the connections between the current content and related content.

Current Content: "{current_content['title']}"
Preview: {current_content['text'][:500]}...

Related Content:
{related_context}

Task: Write a brief 2-3 sentence synthesis explaining how the current content relates to the related items. Focus on:
- Thematic connections and overlapping concepts
- How the related content might expand or complement the current content
- Potential insights from viewing these together

Keep it concise and actionable. Do not use bullet points or markdown formatting."""

            elif synthesis_type == "comparison":
                prompt = f"""Compare and contrast the current content with related content.

Current Content: "{current_content['title']}"
Preview: {current_content['text'][:500]}...

Related Content:
{related_context}

Task: Write a brief 2-3 sentence comparison highlighting:
- Key similarities and differences
- Complementary or contrasting perspectives
- Areas of agreement or disagreement

Keep it concise and actionable. Do not use bullet points or markdown formatting."""

            elif synthesis_type == "gaps":
                prompt = f"""Identify knowledge gaps and questions.

Current Content: "{current_content['title']}"
Preview: {current_content['text'][:500]}...

Related Content:
{related_context}

Task: Write a brief 2-3 sentence analysis identifying:
- What questions remain unanswered across these sources
- Topics that need deeper exploration
- Potential areas for further learning

Keep it concise and actionable. Do not use bullet points or markdown formatting."""

            else:
                # Default to connections
                synthesis_type = "connections"
                prompt = f"""Analyze the connections between the current content and related content.

Current Content: "{current_content['title']}"
Preview: {current_content['text'][:500]}...

Related Content:
{related_context}

Task: Write a brief 2-3 sentence synthesis explaining how the current content relates to the related items.

Keep it concise and actionable. Do not use bullet points or markdown formatting."""

            # Generate synthesis using LLM
            synthesis = await self.llm_service.generate_answer(
                query=prompt,
                context="",  # No RAG context needed
                conversation_history=[],
                model="qwen2.5:14b",  # Use Qwen for reasoning
                temperature=0.7,
                system_prompt="You are a knowledge synthesis assistant. Your role is to identify meaningful connections between different pieces of content and help users understand how their knowledge relates. Be concise, insightful, and avoid generic statements.",
            )

            return synthesis.strip()

        except Exception as e:
            logger.error(f"Error generating synthesis: {e}", exc_info=True)
            return ""

    async def suggest_questions(
        self,
        db: AsyncSession,
        current_content: Dict[str, str],
        related_content: List[RelatedContentItem],
    ) -> List[str]:
        """
        Generate 3-5 suggested questions based on content analysis.

        Args:
            db: Database session
            current_content: Dict with "title" and "text" of current source
            related_content: List of related items

        Returns:
            List of suggested questions
        """
        if not related_content:
            return []

        try:
            # Build context with related content
            related_summaries = []
            for idx, item in enumerate(related_content[:3], 1):  # Top 3 items
                source_label = {
                    "note": "Note",
                    "document": "Document",
                    "youtube": "YouTube Video",
                }.get(item.source_type, "Content")

                preview_text = item.preview[:200] if item.preview else ""
                related_summaries.append(
                    f"{idx}. {source_label}: \"{item.source_title}\" "
                    f"(similarity: {item.similarity_score:.2f})\n"
                    f"   Preview: {preview_text}..."
                )

            related_context = "\n\n".join(related_summaries)

            # Build question generation prompt
            prompt = f"""Based on the current content and related sources, generate 3-5 insightful questions that would help deepen understanding.

Current Content: "{current_content['title']}"
Preview: {current_content['text'][:500]}...

Related Content:
{related_context}

Task: Generate 3-5 questions that:
- Explore knowledge gaps or unanswered aspects
- Connect concepts across these sources
- Encourage deeper exploration of the topic
- Are specific and actionable (not generic)
- Build on what's already covered

Format: Return ONLY the questions, one per line, without numbering or bullet points."""

            # Generate questions using LLM
            response = await self.llm_service.generate_answer(
                query=prompt,
                context="",  # No RAG context needed
                conversation_history=[],
                model="qwen2.5:14b",  # Use Qwen for reasoning
                temperature=0.8,  # Higher temperature for diverse questions
                system_prompt="You are a learning assistant that helps users explore topics more deeply. Generate thoughtful, specific questions that encourage critical thinking and connect related knowledge. Focus on questions that lead to insights, not just facts.",
            )

            # Parse questions from response (split by newlines, filter empty)
            questions = [
                q.strip()
                for q in response.strip().split("\n")
                if q.strip() and len(q.strip()) > 10  # Filter out empty/short lines
            ]

            # Limit to 5 questions
            return questions[:5]

        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            return []


# Global instance
_context_service: Optional[ContextSynthesisService] = None


def get_context_service() -> ContextSynthesisService:
    """
    Get the global context synthesis service instance.

    Returns:
        ContextSynthesisService singleton
    """
    global _context_service
    if _context_service is None:
        _context_service = ContextSynthesisService()
    return _context_service
