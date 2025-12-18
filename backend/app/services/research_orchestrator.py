"""
Research orchestrator service - coordinates autonomous web research.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.research_task import ResearchTask
from app.models.research_source import ResearchSource
from app.models.document import Document
from app.services.web_search_service import get_web_search_service
from app.services.web_scraper_service import get_web_scraper_service
from app.services.credibility_service import get_credibility_service
from app.services.chunk_processing_service import get_chunk_processing_service
from app.services.llm_service import get_llm_service
from app.services.content_formatter_service import get_content_formatter_service

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """
    Orchestrates the autonomous web research workflow.

    Steps:
    1. Web search for sources
    2. Filter by credibility
    3. Scrape content
    4. Create documents
    5. Process for RAG (chunk + embed)
    6. Generate summary (future: Phase 2)
    """

    def __init__(self):
        """Initialize research orchestrator."""
        self.web_search = get_web_search_service()
        self.web_scraper = get_web_scraper_service()
        self.credibility = get_credibility_service()
        self.chunk_service = get_chunk_processing_service()
        self.llm_service = get_llm_service()
        self.content_formatter = get_content_formatter_service()

    async def deep_research(
        self,
        db: AsyncSession,
        task_id: str,
        query: str,
        max_sources: int = 10,
        depth: str = "thorough",
        source_types: List[str] = None,
    ) -> Dict:
        """
        Perform deep research on a query.

        Args:
            db: Database session
            task_id: Research task UUID
            query: Research question
            max_sources: Max sources to process
            depth: 'quick' (5 sources), 'thorough' (10), 'deep' (20)
            source_types: Filter by type (academic, news, blogs, etc.)

        Returns:
            Research results summary
        """
        logger.info(f"Starting deep research for task {task_id}: {query}")

        try:
            # Update task status to running
            await self._update_task_status(
                db,
                task_id,
                status="running",
                current_step="Searching web...",
                started_at=datetime.utcnow(),
            )

            # Step 1: Web Search
            search_count = max_sources * 2  # Get 2x for filtering
            search_results = await self.web_search.search(
                query=query, max_results=search_count
            )

            await self._update_task_progress(
                db, task_id, sources_found=len(search_results), progress_percentage=10
            )

            if not search_results:
                logger.warning(f"No search results for query: {query}")
                await self._update_task_status(
                    db,
                    task_id,
                    status="completed",
                    current_step="Complete",
                    summary="No search results found for this query.",
                    completed_at=datetime.utcnow(),
                )
                return {"task_id": task_id, "sources_added": 0, "message": "No results"}

            # Step 2: Score and filter by credibility
            await self._update_task_status(
                db, task_id, current_step="Filtering sources by credibility..."
            )

            scored_sources = []
            for result in search_results:
                cred = self.credibility.score_source(
                    url=result["href"], title=result["title"], snippet=result["body"]
                )
                scored_sources.append(
                    {
                        "url": result["href"],
                        "title": result["title"],
                        "snippet": result["body"],
                        "credibility_score": cred["score"],
                        "credibility_reasons": cred["reasons"],
                        "source_type": cred["source_type"],
                    }
                )

            # Filter by minimum credibility (0.5) and source types
            min_credibility = 0.5
            filtered_sources = self.credibility.filter_by_credibility(
                scored_sources, min_score=min_credibility, source_types=source_types
            )

            # Sort by credibility (highest first) and take max_sources
            filtered_sources = sorted(
                filtered_sources, key=lambda x: x["credibility_score"], reverse=True
            )[:max_sources]

            await self._update_task_progress(db, task_id, progress_percentage=20)

            # Step 3: Scrape and process each source
            documents_created = []
            failed_count = 0
            skipped_count = 0

            for i, source in enumerate(filtered_sources):
                step_msg = f"Scraping source {i+1}/{len(filtered_sources)}: {source['title'][:50]}..."
                progress = 20 + int((i / len(filtered_sources)) * 60)  # 20% to 80%

                await self._update_task_status(
                    db,
                    task_id,
                    current_step=step_msg,
                    progress_percentage=progress,
                    sources_scraped=i,
                )

                try:
                    # Create research_source record
                    research_source = await self._create_research_source(
                        db,
                        task_id=task_id,
                        url=source["url"],
                        title=source["title"],
                        credibility_score=source["credibility_score"],
                        credibility_reasons=source["credibility_reasons"],
                        source_type=source["source_type"],
                    )

                    # Scrape content
                    content = await self.web_scraper.scrape(source["url"])

                    if not content or len(content) < 100:
                        logger.warning(
                            f"Content too short or empty for {source['url']}, skipping"
                        )
                        await self._update_research_source_status(
                            db,
                            research_source.id,
                            status="skipped",
                            failure_reason="Content too short or empty",
                        )
                        skipped_count += 1
                        continue

                    # Format content into clean markdown
                    try:
                        formatted_content = await self.content_formatter.format_content(
                            raw_content=content,
                            url=source["url"],
                            title=source["title"],
                        )
                        logger.info(f"Formatted content for {source['url']}")
                    except Exception as e:
                        logger.warning(f"Failed to format content for {source['url']}: {e}, using raw content")
                        formatted_content = content

                    # Create document
                    document = await self._create_document_from_web(
                        db,
                        task_id=task_id,
                        url=source["url"],
                        title=source["title"],
                        content=formatted_content,
                        credibility_score=source["credibility_score"],
                        source_type=source["source_type"],
                    )

                    # Link research_source to document
                    await self._link_source_to_document(
                        db, research_source.id, document.id
                    )

                    # Process for RAG (chunk + embed)
                    try:
                        await self.chunk_service.process_document(
                            db, str(document.id), document.content
                        )
                        logger.info(f"Processed chunks for document {document.id}")
                    except Exception as e:
                        logger.error(
                            f"Failed to process chunks for {document.id}: {e}"
                        )
                        # Continue anyway - document is still saved

                    documents_created.append(document)
                    await self._update_task_progress(
                        db, task_id, sources_added=len(documents_created)
                    )
                    await self._update_research_source_status(
                        db, research_source.id, status="scraped"
                    )

                except Exception as e:
                    logger.error(f"Failed to process source {source['url']}: {e}")
                    failed_count += 1
                    await self._update_task_progress(
                        db, task_id, sources_failed=failed_count
                    )
                    await self._update_research_source_status(
                        db,
                        research_source.id,
                        status="failed",
                        failure_reason=str(e),
                    )

            # Step 4: Generate summary (MVP: simple summary)
            await self._update_task_status(
                db,
                task_id,
                current_step="Generating summary...",
                progress_percentage=90,
            )

            summary = await self._generate_simple_summary(
                query, documents_created, failed_count, skipped_count
            )

            # Complete task
            await self._update_task_status(
                db,
                task_id,
                status="completed",
                current_step="Complete",
                progress_percentage=100,
                summary=summary,
                sources_skipped=skipped_count,
                completed_at=datetime.utcnow(),
            )

            logger.info(
                f"Research complete for task {task_id}: {len(documents_created)} sources added"
            )

            return {
                "task_id": task_id,
                "sources_added": len(documents_created),
                "sources_failed": failed_count,
                "sources_skipped": skipped_count,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"Research failed for task {task_id}: {e}")
            await self._update_task_status(
                db,
                task_id,
                status="failed",
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )
            raise

    async def _update_task_status(
        self, db: AsyncSession, task_id: str, **kwargs
    ) -> None:
        """Update research task fields."""
        result = await db.execute(
            select(ResearchTask).where(ResearchTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            logger.error(f"Research task {task_id} not found")
            return

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        await db.commit()
        await db.refresh(task)

    async def _update_task_progress(
        self, db: AsyncSession, task_id: str, **kwargs
    ) -> None:
        """Update research task progress fields."""
        await self._update_task_status(db, task_id, **kwargs)

    async def _create_research_source(
        self,
        db: AsyncSession,
        task_id: str,
        url: str,
        title: str,
        credibility_score: float,
        credibility_reasons: List[str],
        source_type: str,
    ) -> ResearchSource:
        """Create a research source record."""
        parsed = urlparse(url)
        domain = parsed.netloc

        source = ResearchSource(
            research_task_id=task_id,
            url=url,
            title=title,
            domain=domain,
            source_type=source_type,
            credibility_score=credibility_score,
            credibility_reasons=credibility_reasons,
            status="pending",
        )

        db.add(source)
        await db.commit()
        await db.refresh(source)

        return source

    async def _update_research_source_status(
        self, db: AsyncSession, source_id: str, status: str, failure_reason: str = None
    ) -> None:
        """Update research source status."""
        result = await db.execute(
            select(ResearchSource).where(ResearchSource.id == source_id)
        )
        source = result.scalar_one_or_none()

        if source:
            source.status = status
            if failure_reason:
                source.failure_reason = failure_reason
            await db.commit()

    async def _create_document_from_web(
        self,
        db: AsyncSession,
        task_id: str,
        url: str,
        title: str,
        content: str,
        credibility_score: float,
        source_type: str,
    ) -> Document:
        """Create a document from scraped web content."""
        # Generate filename from title
        filename = title[:100] + ".txt" if title else "web_source.txt"
        filename = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_", "."))

        document = Document(
            filename=filename,
            file_path=url,  # Use URL as path for web sources
            file_type="text/plain",
            file_size=len(content),
            content=content,
            source_type="web_research",
            source_url=url,
            credibility_score=credibility_score,
            research_task_id=task_id,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    async def _link_source_to_document(
        self, db: AsyncSession, source_id: str, document_id: str
    ) -> None:
        """Link research source to created document."""
        result = await db.execute(
            select(ResearchSource).where(ResearchSource.id == source_id)
        )
        source = result.scalar_one_or_none()

        if source:
            source.document_id = document_id
            await db.commit()

    async def _generate_simple_summary(
        self,
        query: str,
        documents: List[Document],
        failed_count: int,
        skipped_count: int,
    ) -> str:
        """Generate a simple text summary of research results."""
        if not documents:
            return f"No sources were successfully added for the query: '{query}'"

        summary_parts = [
            f"Research completed for: '{query}'",
            f"Successfully added {len(documents)} sources to your knowledge base.",
        ]

        if failed_count > 0:
            summary_parts.append(f"{failed_count} sources failed to scrape.")

        if skipped_count > 0:
            summary_parts.append(f"{skipped_count} sources were skipped (insufficient content).")

        summary_parts.append(
            "\nYou can now ask questions about these sources in the Chat page."
        )

        return " ".join(summary_parts)


# Global instance
_research_orchestrator: Optional[ResearchOrchestrator] = None


def get_research_orchestrator() -> ResearchOrchestrator:
    """
    Get the global research orchestrator instance.

    Returns:
        Research orchestrator singleton
    """
    global _research_orchestrator
    if _research_orchestrator is None:
        _research_orchestrator = ResearchOrchestrator()
    return _research_orchestrator
