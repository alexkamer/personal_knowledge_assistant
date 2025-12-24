#!/usr/bin/env python3
"""
Benchmark different LLM models for prompt refinement question generation.
Tests speed and quality of generated questions.
"""
import asyncio
import time
import json
from app.services.prompt_refinement_service import PromptRefinementService
import ollama

# Test prompts covering different categories
TEST_PROMPTS = [
    "A red sports car",
    "A blue ocean wave",
    "A cyberpunk street market at night",
    "A portrait of an elderly woman",
]

# Models to test
MODELS = [
    "llama3.2:3b",      # Fast local model
    "qwen2.5:14b",      # Reasoning local model
    "phi4:14b",         # Reasoning local model
]

async def test_model(model_name: str, prompt: str):
    """Test a single model with a prompt."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}")

    # Initialize service with specific model
    service = PromptRefinementService()
    service.llm_model = model_name

    start_time = time.time()

    try:
        # Detect category
        category = service.detect_category(prompt)

        # Generate questions
        questions = await service.generate_dynamic_questions(prompt, category)

        elapsed = time.time() - start_time

        if questions:
            print(f"✓ SUCCESS - Generated {len(questions)} questions in {elapsed:.2f}s")
            print(f"Category: {category}")
            print(f"\nSample questions:")
            for i, q in enumerate(questions[:3], 1):
                print(f"  {i}. {q.get('question', 'N/A')}")
                if q.get('options'):
                    print(f"     Options: {', '.join(q['options'][:3])}...")

            return {
                'model': model_name,
                'prompt': prompt,
                'success': True,
                'time': elapsed,
                'num_questions': len(questions),
                'category': category,
                'questions': questions
            }
        else:
            print(f"✗ FAILED - No questions generated")
            return {
                'model': model_name,
                'prompt': prompt,
                'success': False,
                'time': elapsed,
                'error': 'No questions returned'
            }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ ERROR - {str(e)}")
        return {
            'model': model_name,
            'prompt': prompt,
            'success': False,
            'time': elapsed,
            'error': str(e)
        }

async def main():
    """Run all tests."""
    print("="*60)
    print("PROMPT REFINEMENT MODEL BENCHMARK")
    print("="*60)

    # Check which models are available
    print("\nChecking available models...")
    try:
        client = ollama.AsyncClient()
        response = await client.list()
        available_models = response.get('models', [])
        available_names = [m.get('model', m.get('name', '')) for m in available_models]
        print(f"Available models: {', '.join(available_names)}")
    except Exception as e:
        print(f"Error listing models: {e}")
        import traceback
        traceback.print_exc()
        available_names = []

    # Filter to only test available models
    models_to_test = [m for m in MODELS if m in available_names]

    if not models_to_test:
        print("\n⚠️  No models available for testing!")
        print("Please ensure Ollama is running and models are installed.")
        return

    print(f"\nTesting {len(models_to_test)} models with {len(TEST_PROMPTS)} prompts each")
    print(f"Total tests: {len(models_to_test) * len(TEST_PROMPTS)}")

    results = []

    # Test each model with each prompt
    for model in models_to_test:
        for prompt in TEST_PROMPTS:
            result = await test_model(model, prompt)
            results.append(result)
            await asyncio.sleep(1)  # Brief pause between tests

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    # Group by model
    for model in models_to_test:
        model_results = [r for r in results if r['model'] == model]
        successes = [r for r in model_results if r['success']]

        if successes:
            avg_time = sum(r['time'] for r in successes) / len(successes)
            avg_questions = sum(r['num_questions'] for r in successes) / len(successes)

            print(f"\n{model}:")
            print(f"  Success rate: {len(successes)}/{len(model_results)}")
            print(f"  Average time: {avg_time:.2f}s")
            print(f"  Average questions: {avg_questions:.1f}")
            print(f"  Speed rating: {'🚀 Fast' if avg_time < 5 else '⚡ Medium' if avg_time < 15 else '🐢 Slow'}")
        else:
            print(f"\n{model}: ✗ All tests failed")

    # Overall recommendation
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)

    successful_results = [r for r in results if r['success']]
    if successful_results:
        # Find fastest model
        model_times = {}
        for model in models_to_test:
            model_results = [r for r in successful_results if r['model'] == model]
            if model_results:
                model_times[model] = sum(r['time'] for r in model_results) / len(model_results)

        if model_times:
            fastest = min(model_times.items(), key=lambda x: x[1])
            print(f"\n🏆 Fastest model: {fastest[0]} ({fastest[1]:.2f}s average)")
            print(f"\nRecommended for production use.")

if __name__ == "__main__":
    asyncio.run(main())
