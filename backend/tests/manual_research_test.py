"""
Manual test script for research API.

Run this to test the research feature end-to-end.
Usage: python tests/manual_research_test.py
"""
import asyncio
import httpx


async def test_research_api():
    """Test the research API end-to-end."""
    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
        print("=" * 60)
        print("Testing Web Researcher Agent")
        print("=" * 60)

        # 1. Start research
        print("\n1. Starting research task...")
        response = await client.post(
            f"{base_url}/research/start",
            json={
                "query": "What is FastAPI and how does it work?",
                "max_sources": 3,  # Small for testing
                "depth": "quick",
            },
        )

        if response.status_code != 201:
            print(f"❌ Failed to start research: {response.status_code}")
            print(response.text)
            return

        data = response.json()
        task_id = data["task_id"]
        print(f"✅ Research task created: {task_id}")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")

        # 2. Poll for progress
        print("\n2. Polling for progress...")
        max_polls = 30  # 5 minutes max
        for i in range(max_polls):
            await asyncio.sleep(10)  # Poll every 10 seconds

            response = await client.get(f"{base_url}/research/tasks/{task_id}")

            if response.status_code != 200:
                print(f"❌ Failed to get task: {response.status_code}")
                break

            task = response.json()
            status = task["status"]
            progress = task["progress_percentage"]
            current_step = task.get("current_step", "")

            print(f"   [{i+1}/{max_polls}] Status: {status}, Progress: {progress}%, Step: {current_step}")

            if status in ["completed", "failed", "cancelled"]:
                break

        # 3. Get results
        print("\n3. Getting research results...")
        if task["status"] == "completed":
            response = await client.get(f"{base_url}/research/tasks/{task_id}/results")

            if response.status_code != 200:
                print(f"❌ Failed to get results: {response.status_code}")
                return

            results = response.json()

            print(f"\n✅ Research completed!")
            print(f"   Query: {results['query']}")
            print(f"   Sources added: {results['sources_added']}")
            print(f"   Sources failed: {results['sources_failed']}")
            print(f"   Sources skipped: {results['sources_skipped']}")
            print(f"\n   Summary:\n   {results['summary']}")

            if results['sources']:
                print(f"\n   Sources:")
                for source in results['sources']:
                    print(f"   - [{source['source_type']}] {source['title']}")
                    print(f"     URL: {source['url']}")
                    print(f"     Credibility: {source['credibility_score']:.2f}")
                    print(f"     Status: {source['status']}")

        elif task["status"] == "failed":
            print(f"❌ Research failed: {task.get('error_message', 'Unknown error')}")
        else:
            print(f"⏱️ Research did not complete in time (status: {task['status']})")

        print("\n" + "=" * 60)
        print("Test complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_research_api())
