# Test Document for Agentic RAG

## What is Agentic RAG?

Agentic RAG is an advanced retrieval-augmented generation approach where the LLM autonomously decides when and how to retrieve information from a knowledge base. Unlike traditional RAG that always retrieves context upfront, agentic RAG gives the model control over:

1. **When to search**: The LLM can determine if it needs external knowledge or can answer from its training
2. **What to search for**: The LLM can formulate specific search queries based on what it needs
3. **Iterative retrieval**: The LLM can perform multiple searches, refining queries based on previous results
4. **Multi-step reasoning**: The LLM can chain together searches and reasoning steps

## Benefits of Agentic RAG

- **Reduced latency**: Only retrieves when actually needed
- **Better accuracy**: Can retrieve multiple times with refined queries
- **Complex queries**: Can break down multi-part questions into sequential searches
- **Cost effective**: Doesn't waste tokens on irrelevant context

## Example Use Cases

### Multi-step query
"Compare the Python async programming patterns in my notes with the FastAPI best practices from my documents"

The agent would:
1. Search for "Python async programming patterns"
2. Search for "FastAPI best practices"
3. Compare and synthesize the results

### Conditional retrieval
"What is 2+2?"

The agent would realize this is basic math and not search the knowledge base.

## Implementation Details

Our implementation uses:
- **Tool orchestrator**: Manages the agentic reasoning loop
- **Knowledge search tool**: Wraps the RAG pipeline as a callable tool
- **Ollama models**: Local LLMs (Qwen 2.5, Phi-4) for privacy
- **JSON parsing**: LLM outputs structured tool calls via prompt engineering
