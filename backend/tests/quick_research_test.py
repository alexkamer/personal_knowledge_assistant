"""
Quick test - directly call the research orchestrator.
"""
import asyncio
from app.core.database import async_session_maker
from app.services.research_orchestrator import get_research_orchestrator
from app.models.research_task import ResearchTask


async def test_direct():
    """Test research orchestrator directly."""
    print("=" * 60)
    print("Direct Research Orchestrator Test")
    print("=" * 60)

    async with async_session_maker() as db:
        # Create task
        task = ResearchTask(
            query="What is FastAPI?",
            max_sources=3,
            depth="quick",
            status="queued",
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        print(f"\n✅ Task created: {task.id}")
        print(f"   Query: {task.query}")
        print(f"   Max sources: {task.max_sources}")

        # Run research
        print("\n🔍 Starting research...")
        orchestrator = get_research_orchestrator()

        try:
            result = await orchestrator.deep_research(
                db=db,
                task_id=str(task.id),
                query=task.query,
                max_sources=task.max_sources,
                depth=task.depth,
            )

            print("\n" + "=" * 60)
            print("✅ RESEARCH COMPLETE!")
            print("=" * 60)
            print(f"Task ID: {result['task_id']}")
            print(f"Sources added: {result['sources_added']}")
            print(f"Sources failed: {result['sources_failed']}")
            print(f"Sources skipped: {result['sources_skipped']}")
            print(f"\nSummary:\n{result['summary']}")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Research failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct())
