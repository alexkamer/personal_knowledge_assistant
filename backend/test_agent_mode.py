"""
Quick test script for agentic RAG mode.
Run this to verify the agent can make tool calls.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.tool_orchestrator import get_tool_orchestrator
from app.services.agent_service import AgentConfig
from app.services.tools.knowledge_search_tool import KnowledgeSearchTool
from app.core.database import AsyncSessionLocal


async def test_agent_mode():
    """Test agent mode with a simple query."""
    print("=" * 60)
    print("Testing Agentic RAG Mode")
    print("=" * 60)

    # Get orchestrator
    orchestrator = get_tool_orchestrator()

    # Configure agent
    agent_config = AgentConfig(
        model="qwen2.5:14b",
        temperature=0.7,
        tool_access_list=["knowledge_search"],
    )

    # Setup knowledge search tool with DB session
    async with AsyncSessionLocal() as db:
        knowledge_tool = orchestrator.tool_executor.registry.get_tool("knowledge_search")
        if isinstance(knowledge_tool, KnowledgeSearchTool):
            knowledge_tool.set_db_session(db)

        # Test queries
        test_queries = [
            "What is 2 + 2?",  # Should skip retrieval
            "What is agentic RAG?",  # Should search if doc uploaded
            "Compare Python async with FastAPI best practices",  # Multi-step
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Test Query {i}: {query}")
            print(f"{'='*60}\n")

            try:
                # Track tool calls
                tool_calls = []
                iterations = []

                def on_tool_call(call_info):
                    tool_calls.append(call_info)
                    print(f"🔧 Tool Call: {call_info['tool']}")
                    print(f"   Parameters: {call_info['parameters']}")

                def on_tool_result(tool_name, result):
                    print(f"✅ Tool Result: {tool_name}")
                    print(f"   Success: {result.get('success')}")
                    if result.get('result'):
                        res = result['result']
                        if isinstance(res, dict):
                            print(f"   Found: {res.get('found', False)}")
                            print(f"   Results: {res.get('num_results', 0)}")

                def on_iteration(iteration, status):
                    iterations.append(iteration)
                    print(f"💭 Iteration {iteration}: {status}")

                # Process with tools
                response = await orchestrator.process_with_tools(
                    query=query,
                    agent_config=agent_config,
                    db=db,
                    max_iterations=5,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result,
                    on_iteration=on_iteration,
                )

                print(f"\n📝 Final Answer:")
                print(f"{response[:300]}...")
                print(f"\n📊 Summary:")
                print(f"   Total iterations: {len(iterations)}")
                print(f"   Tool calls made: {len(tool_calls)}")

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent_mode())
