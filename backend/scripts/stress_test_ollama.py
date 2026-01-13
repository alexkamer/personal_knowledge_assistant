#!/usr/bin/env python3
"""
Ollama Stress Test Script
Tests external hard drive stability by running concurrent Ollama model requests
"""
import asyncio
import time
import json
from datetime import datetime
import aiohttp
from typing import List, Dict, Any
import sys

# Test configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODELS_TO_TEST = ["llama3.2:3b", "phi4:14b", "qwen2.5:14b"]
CONCURRENT_REQUESTS = 5  # Number of concurrent requests per model
ITERATIONS = 10  # Number of test iterations
PROMPT_LENGTH = "medium"  # short, medium, long

# Test prompts of varying lengths
PROMPTS = {
    "short": "What is machine learning?",
    "medium": "Explain the concept of retrieval-augmented generation (RAG) and how it improves large language model outputs by incorporating external knowledge sources.",
    "long": """Write a detailed technical explanation of how vector databases work in semantic search systems.
    Cover the following topics: embedding generation, similarity metrics (cosine, euclidean),
    indexing strategies (HNSW, IVF), query optimization, and trade-offs between accuracy and speed.
    Include specific examples of when to use different approaches and how to tune parameters for optimal performance."""
}

class StressTestResults:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens = 0
        self.total_time = 0
        self.errors: List[str] = []
        self.model_stats: Dict[str, Dict[str, Any]] = {}

    def add_result(self, model: str, success: bool, duration: float, tokens: int = 0, error: str = None):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.total_tokens += tokens
        else:
            self.failed_requests += 1
            if error:
                self.errors.append(f"[{model}] {error}")

        self.total_time += duration

        if model not in self.model_stats:
            self.model_stats[model] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0,
                "total_tokens": 0
            }

        stats = self.model_stats[model]
        stats["requests"] += 1
        stats["total_time"] += duration
        if success:
            stats["successes"] += 1
            stats["total_tokens"] += tokens
        else:
            stats["failures"] += 1

    def print_summary(self):
        print("\n" + "="*60)
        print("STRESS TEST SUMMARY")
        print("="*60)
        print(f"Total Requests: {self.total_requests}")
        print(f"Successful: {self.successful_requests} ({self.successful_requests/self.total_requests*100:.1f}%)")
        print(f"Failed: {self.failed_requests} ({self.failed_requests/self.total_requests*100:.1f}%)")
        print(f"Total Tokens Generated: {self.total_tokens:,}")
        print(f"Total Time: {self.total_time:.2f}s")
        print(f"Avg Time per Request: {self.total_time/self.total_requests:.2f}s")

        print("\n" + "-"*60)
        print("PER-MODEL STATISTICS")
        print("-"*60)
        for model, stats in self.model_stats.items():
            print(f"\n{model}:")
            print(f"  Requests: {stats['requests']}")
            print(f"  Success Rate: {stats['successes']}/{stats['requests']} ({stats['successes']/stats['requests']*100:.1f}%)")
            print(f"  Avg Time: {stats['total_time']/stats['requests']:.2f}s")
            print(f"  Tokens: {stats['total_tokens']:,}")
            if stats['requests'] > 0:
                print(f"  Tokens/sec: {stats['total_tokens']/(stats['total_time'] or 1):.1f}")

        if self.errors:
            print("\n" + "-"*60)
            print("ERRORS")
            print("-"*60)
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  • {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors)-10} more errors")

async def test_model_request(session: aiohttp.ClientSession, model: str, prompt: str,
                             iteration: int, request_num: int) -> Dict[str, Any]:
    """Make a single request to Ollama and measure performance"""
    start_time = time.time()

    try:
        async with session.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            duration = time.time() - start_time

            if response.status == 200:
                data = await response.json()
                tokens = len(data.get("response", "").split())

                print(f"✓ [{model}] Iter {iteration}, Req {request_num}: {duration:.2f}s, {tokens} tokens")

                return {
                    "success": True,
                    "duration": duration,
                    "tokens": tokens,
                    "model": model
                }
            else:
                error_text = await response.text()
                print(f"✗ [{model}] Iter {iteration}, Req {request_num}: HTTP {response.status}")
                return {
                    "success": False,
                    "duration": duration,
                    "error": f"HTTP {response.status}: {error_text[:100]}",
                    "model": model
                }

    except asyncio.TimeoutError:
        duration = time.time() - start_time
        print(f"✗ [{model}] Iter {iteration}, Req {request_num}: TIMEOUT")
        return {
            "success": False,
            "duration": duration,
            "error": "Request timeout (>120s)",
            "model": model
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"✗ [{model}] Iter {iteration}, Req {request_num}: {type(e).__name__}")
        return {
            "success": False,
            "duration": duration,
            "error": f"{type(e).__name__}: {str(e)[:100]}",
            "model": model
        }

async def run_stress_test():
    """Run the stress test with concurrent requests"""
    print("="*60)
    print("OLLAMA STRESS TEST - EXTERNAL DRIVE STABILITY CHECK")
    print("="*60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Models: {', '.join(MODELS_TO_TEST)}")
    print(f"Concurrent Requests per Model: {CONCURRENT_REQUESTS}")
    print(f"Iterations: {ITERATIONS}")
    print(f"Prompt Length: {PROMPT_LENGTH}")
    print("="*60 + "\n")

    results = StressTestResults()
    prompt = PROMPTS[PROMPT_LENGTH]

    async with aiohttp.ClientSession() as session:
        for iteration in range(1, ITERATIONS + 1):
            print(f"\n{'='*60}")
            print(f"ITERATION {iteration}/{ITERATIONS}")
            print(f"{'='*60}")

            # Create concurrent requests for all models
            tasks = []
            for model in MODELS_TO_TEST:
                for req_num in range(1, CONCURRENT_REQUESTS + 1):
                    task = test_model_request(session, model, prompt, iteration, req_num)
                    tasks.append(task)

            # Run all requests concurrently
            iteration_start = time.time()
            responses = await asyncio.gather(*tasks)
            iteration_time = time.time() - iteration_start

            # Process results
            for response in responses:
                results.add_result(
                    model=response["model"],
                    success=response["success"],
                    duration=response["duration"],
                    tokens=response.get("tokens", 0),
                    error=response.get("error")
                )

            print(f"\nIteration {iteration} completed in {iteration_time:.2f}s")
            print(f"Progress: {results.successful_requests}/{results.total_requests} successful")

    # Print final summary
    results.print_summary()

    print("\n" + "="*60)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Return exit code based on success rate
    success_rate = results.successful_requests / results.total_requests
    if success_rate < 0.9:
        print(f"\n⚠️  WARNING: Low success rate ({success_rate*100:.1f}%) - Drive may be unstable!")
        return 1
    elif results.failed_requests > 0:
        print(f"\n⚠️  WARNING: {results.failed_requests} failed requests detected")
        return 1
    else:
        print(f"\n✅ All tests passed! Drive appears stable.")
        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_stress_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)
