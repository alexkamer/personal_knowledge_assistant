"""
Briefing generator service for synthesizing research findings.

Generates comprehensive research briefings from multiple sources using LLM.
"""
import logging
import json
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research_project import ResearchProject
from app.models.research_task import ResearchTask
from app.models.research_source import ResearchSource
from app.models.research_briefing import ResearchBriefing
from app.models.document import Document
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class BriefingGeneratorService:
    """Service for generating research briefings from completed tasks."""

    def __init__(self):
        """Initialize briefing generator service."""
        self.llm_service = get_llm_service()

    async def generate_briefing(
        self,
        db: AsyncSession,
        project_id: str,
        task_ids: Optional[List[str]] = None,
    ) -> ResearchBriefing:
        """
        Generate a comprehensive research briefing for a project.

        Args:
            db: Database session
            project_id: Project UUID
            task_ids: Optional list of specific task IDs to include (if None, uses all completed tasks)

        Returns:
            Generated research briefing
        """
        # Get project
        result = await db.execute(
            select(ResearchProject).where(ResearchProject.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get tasks
        if task_ids:
            tasks_query = select(ResearchTask).where(
                ResearchTask.id.in_(task_ids)
            )
        else:
            tasks_query = select(ResearchTask).where(
                ResearchTask.project_id == project_id,
                ResearchTask.status == "completed"
            )

        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()

        if not tasks:
            raise ValueError("No completed tasks found to generate briefing")

        # Collect all sources from tasks
        sources = await self._collect_sources(db, [str(task.id) for task in tasks])

        logger.info(
            f"Generating briefing for project {project_id}: {len(tasks)} tasks, {len(sources)} sources"
        )

        # Generate briefing content using LLM
        synthesis = await self._synthesize_findings(
            project_goal=project.goal,
            project_name=project.name,
            tasks=tasks,
            sources=sources,
        )

        # Create briefing record
        briefing = ResearchBriefing(
            project_id=project_id,
            title=synthesis.get("title", f"Research Briefing: {project.name}"),
            summary=synthesis.get("summary", ""),
            key_findings=synthesis.get("key_findings"),
            contradictions=synthesis.get("contradictions"),
            knowledge_gaps=synthesis.get("knowledge_gaps"),
            suggested_tasks=synthesis.get("suggested_tasks"),
            task_ids=[str(task.id) for task in tasks],
            sources_count=len(sources),
            generated_at=datetime.utcnow(),
        )

        db.add(briefing)
        await db.commit()
        await db.refresh(briefing)

        logger.info(f"Generated briefing {briefing.id} for project {project_id}")

        return briefing

    async def _collect_sources(
        self, db: AsyncSession, task_ids: List[str]
    ) -> List[Dict]:
        """
        Collect all sources with their content from specified tasks.

        Args:
            db: Database session
            task_ids: List of task UUIDs

        Returns:
            List of source dicts with metadata and content
        """
        # Get all research sources for these tasks
        sources_query = (
            select(ResearchSource)
            .where(
                ResearchSource.research_task_id.in_(task_ids),
                ResearchSource.status == "scraped"
            )
            .options(selectinload(ResearchSource.document))
        )

        result = await db.execute(sources_query)
        research_sources = result.scalars().all()

        sources = []
        for source in research_sources:
            if source.document:
                sources.append({
                    "url": source.url,
                    "title": source.title,
                    "domain": source.domain,
                    "source_type": source.source_type,
                    "credibility_score": source.credibility_score,
                    "credibility_reasons": source.credibility_reasons,
                    "content": source.document.content[:5000],  # Limit content for LLM context
                })

        return sources

    async def _synthesize_findings(
        self,
        project_goal: str,
        project_name: str,
        tasks: List[ResearchTask],
        sources: List[Dict],
    ) -> Dict:
        """
        Use LLM to synthesize findings from sources.

        Args:
            project_goal: Project research goal
            project_name: Project name
            tasks: List of completed tasks
            sources: List of source dicts with content

        Returns:
            Dict with synthesized findings
        """
        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(
            project_goal=project_goal,
            project_name=project_name,
            tasks=tasks,
            sources=sources,
        )

        try:
            # Generate synthesis
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.3,  # Lower temp for factual synthesis
                max_tokens=2000,
            )

            # Parse JSON response
            synthesis = self._parse_synthesis_response(response)

            return synthesis

        except Exception as e:
            logger.error(f"Failed to synthesize findings: {e}")
            # Fallback to simple summary
            return self._generate_simple_synthesis(project_goal, tasks, sources)

    def _build_synthesis_prompt(
        self,
        project_goal: str,
        project_name: str,
        tasks: List[ResearchTask],
        sources: List[Dict],
    ) -> str:
        """Build prompt for LLM to synthesize research findings."""
        # Format tasks
        tasks_text = "\n".join([
            f"{i+1}. {task.query} (Sources: {task.sources_added})"
            for i, task in enumerate(tasks)
        ])

        # Format sources (with truncation for context limits)
        max_sources = 20  # Limit sources to fit in context
        sources_text = ""
        for i, source in enumerate(sources[:max_sources]):
            credibility_emoji = "✅" if source["credibility_score"] >= 0.7 else "⚠️"
            sources_text += f"\n\n[{i+1}] {credibility_emoji} {source['title']}\n"
            sources_text += f"URL: {source['url']}\n"
            sources_text += f"Credibility: {source['credibility_score']:.2f}\n"
            sources_text += f"Content preview: {source['content'][:500]}...\n"

        if len(sources) > max_sources:
            sources_text += f"\n\n... and {len(sources) - max_sources} more sources"

        prompt = f"""You are a research analyst synthesizing findings from multiple sources.

PROJECT: {project_name}
RESEARCH GOAL: {project_goal}

COMPLETED RESEARCH TASKS ({len(tasks)}):
{tasks_text}

SOURCES ANALYZED ({len(sources)}):
{sources_text}

Generate a comprehensive research briefing in JSON format with these fields:

{{
  "title": "A concise title for this briefing",
  "summary": "2-3 paragraph executive summary of key findings",
  "key_findings": {{
    "finding1": {{
      "description": "Clear finding with evidence",
      "sources": [1, 3, 5],
      "confidence": "high|medium|low"
    }},
    "finding2": {{ ... }}
  }},
  "contradictions": [
    {{
      "topic": "What the contradiction is about",
      "position_a": "First perspective",
      "sources_a": [2, 4],
      "position_b": "Opposing perspective",
      "sources_b": [7, 9],
      "analysis": "Brief analysis of the contradiction"
    }}
  ],
  "knowledge_gaps": [
    "Gap 1: What's missing from the research",
    "Gap 2: Areas needing more investigation"
  ],
  "suggested_tasks": [
    "Suggested research question 1",
    "Suggested research question 2",
    "Suggested research question 3"
  ]
}}

IMPORTANT:
- Be objective and evidence-based
- Cite sources using [number] format
- Identify contradictions honestly
- Suggest 3-5 follow-up research tasks
- Keep findings concise but specific
- Use proper JSON format

Generate the briefing:"""

        return prompt

    def _parse_synthesis_response(self, response: str) -> Dict:
        """Parse JSON synthesis response from LLM."""
        try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            import re

            # Remove markdown code blocks if present
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response

            synthesis = json.loads(json_str)

            return synthesis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse synthesis JSON: {e}")
            logger.error(f"Response was: {response[:500]}...")

            # Return minimal structure
            return {
                "title": "Research Briefing",
                "summary": response[:500],
                "key_findings": {},
                "contradictions": [],
                "knowledge_gaps": [],
                "suggested_tasks": [],
            }

    def _generate_simple_synthesis(
        self,
        project_goal: str,
        tasks: List[ResearchTask],
        sources: List[Dict],
    ) -> Dict:
        """Generate a simple synthesis when LLM fails."""
        summary = f"""Research completed for: '{project_goal}'

Successfully analyzed {len(sources)} sources across {len(tasks)} research tasks.

Sources collected from domains: {', '.join(set(s['domain'] for s in sources[:10] if s['domain']))}.

Average credibility score: {sum(s['credibility_score'] for s in sources) / len(sources):.2f}

You can now ask questions about these sources in the Chat page.
"""

        return {
            "title": f"Research Briefing: {project_goal[:100]}",
            "summary": summary,
            "key_findings": {},
            "contradictions": [],
            "knowledge_gaps": [
                "Detailed analysis could not be generated",
                "Manual review of sources recommended"
            ],
            "suggested_tasks": [],
        }

    async def format_briefing_markdown(
        self, db: AsyncSession, briefing_id: str
    ) -> str:
        """
        Format a briefing as markdown for export.

        Args:
            db: Database session
            briefing_id: Briefing UUID

        Returns:
            Markdown formatted briefing
        """
        # Get briefing
        result = await db.execute(
            select(ResearchBriefing).where(ResearchBriefing.id == briefing_id)
        )
        briefing = result.scalar_one_or_none()

        if not briefing:
            raise ValueError(f"Briefing {briefing_id} not found")

        # Build markdown
        md = f"# {briefing.title}\n\n"
        md += f"**Generated**: {briefing.generated_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        md += f"**Sources**: {briefing.sources_count}\n"
        md += f"**Tasks**: {len(briefing.task_ids or [])}\n\n"

        md += "---\n\n"

        # Summary
        md += "## Executive Summary\n\n"
        md += f"{briefing.summary}\n\n"

        # Key findings
        if briefing.key_findings:
            md += "## Key Findings\n\n"
            for finding_key, finding_data in briefing.key_findings.items():
                if isinstance(finding_data, dict):
                    desc = finding_data.get("description", "")
                    confidence = finding_data.get("confidence", "unknown")
                    sources = finding_data.get("sources", [])

                    md += f"### {finding_key.replace('_', ' ').title()}\n\n"
                    md += f"{desc}\n\n"
                    md += f"*Confidence: {confidence}*\n"
                    if sources:
                        md += f"*Sources: {', '.join(f'[{s}]' for s in sources)}*\n"
                    md += "\n"

        # Contradictions
        if briefing.contradictions:
            md += "## Contradictions Found\n\n"
            for i, contradiction in enumerate(briefing.contradictions, 1):
                md += f"### {i}. {contradiction.get('topic', 'Contradiction')}\n\n"
                md += f"**Position A**: {contradiction.get('position_a', '')}\n"
                md += f"*Sources: {', '.join(f'[{s}]' for s in contradiction.get('sources_a', []))}*\n\n"
                md += f"**Position B**: {contradiction.get('position_b', '')}\n"
                md += f"*Sources: {', '.join(f'[{s}]' for s in contradiction.get('sources_b', []))}*\n\n"
                if contradiction.get('analysis'):
                    md += f"**Analysis**: {contradiction['analysis']}\n\n"

        # Knowledge gaps
        if briefing.knowledge_gaps:
            md += "## Knowledge Gaps\n\n"
            for gap in briefing.knowledge_gaps:
                md += f"- {gap}\n"
            md += "\n"

        # Suggested follow-ups
        if briefing.suggested_tasks:
            md += "## Suggested Follow-up Research\n\n"
            for i, task in enumerate(briefing.suggested_tasks, 1):
                md += f"{i}. {task}\n"
            md += "\n"

        md += "---\n\n"
        md += "*Generated by Personal Knowledge Assistant - Research Autopilot*\n"

        return md


# Global instance
_briefing_generator: Optional[BriefingGeneratorService] = None


def get_briefing_generator_service() -> BriefingGeneratorService:
    """
    Get the global briefing generator service instance.

    Returns:
        Briefing generator service singleton
    """
    global _briefing_generator
    if _briefing_generator is None:
        _briefing_generator = BriefingGeneratorService()
    return _briefing_generator
