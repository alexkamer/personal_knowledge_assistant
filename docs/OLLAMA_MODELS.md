# Ollama Models Guide

This project uses a mixture of local Ollama models optimized for different tasks.

## Configured Models (16GB RAM)

### Qwen 2.5:14b (Primary Model)
- **Use**: Complex Q&A, detailed explanations, reasoning tasks
- **Size**: ~8GB
- **Context**: 32k tokens
- **Strengths**: Excellent reasoning, multilingual, handles long contexts well
- **When to use**: Default for most user queries

### Phi-4:14b (Reasoning Model)
- **Use**: Advanced reasoning, math, code understanding
- **Size**: ~8GB
- **Context**: 16k tokens
- **Strengths**: Rivals much larger models in reasoning, very efficient
- **When to use**: Complex analysis, technical questions, code explanations

### Llama 3.2:3b (Fast Model)
- **Use**: Quick lookups, simple queries, fallback
- **Size**: ~2GB
- **Context**: 4k tokens
- **Strengths**: Very fast responses, low memory usage
- **When to use**: Simple factual queries, quick searches

## Installation

```bash
# Pull all models (will take time, ~18GB total)
ollama pull qwen2.5:14b
ollama pull phi4:14b
ollama pull llama3.2:3b
```

## Testing Models

```bash
# Test each model
ollama run qwen2.5:14b "What is machine learning?"
ollama run phi4:14b "Explain recursion with an example"
ollama run llama3.2:3b "What is Python?"
```

## Model Selection Strategy

The application automatically selects models based on query type:

- **Complex questions** → Qwen 2.5:14b
- **Reasoning/math** → Phi-4:14b
- **Simple lookups** → Llama 3.2:3b

You can override this by configuring `OLLAMA_PRIMARY_MODEL` in `.env`.

## Alternative Model Options

If you have more/less RAM, consider these alternatives:

### For 32GB+ RAM (Better Performance)
```env
OLLAMA_PRIMARY_MODEL=qwen2.5:32b
OLLAMA_REASONING_MODEL=llama3.3:70b
OLLAMA_FAST_MODEL=phi4:14b
```

### For 8-12GB RAM (Lower Memory)
```env
OLLAMA_PRIMARY_MODEL=qwen2.5:7b
OLLAMA_REASONING_MODEL=phi4:14b
OLLAMA_FAST_MODEL=llama3.2:1b
```

### For Maximum Quality (if you have 64GB+ RAM)
```env
OLLAMA_PRIMARY_MODEL=llama3.3:70b
OLLAMA_REASONING_MODEL=qwen2.5:32b
OLLAMA_FAST_MODEL=qwen2.5:14b
```

## Model Performance Comparison

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| Qwen 2.5:14b | 8GB | 16GB+ | Medium | High | General Q&A |
| Phi-4:14b | 8GB | 16GB+ | Medium | Very High | Reasoning |
| Llama 3.2:3b | 2GB | 8GB+ | Fast | Medium | Quick queries |
| Llama 3.3:70b | 40GB | 64GB+ | Slow | Excellent | Complex tasks |

## Managing Ollama

### Check running models
```bash
ollama ps
```

### Stop a model
```bash
ollama stop <model_name>
```

### Remove a model
```bash
ollama rm <model_name>
```

### Update models
```bash
ollama pull <model_name>
```

## Troubleshooting

### Model won't load
- Check available RAM: `vm_stat`
- Stop other models: `ollama ps` then `ollama stop <model>`
- Try smaller model variants

### Slow responses
- Use faster model (Llama 3.2:3b)
- Reduce context length
- Close other applications

### Out of memory
- Switch to smaller models (7b or 3b variants)
- Reduce concurrent models
- Increase swap space

## Latest Models (December 2024)

Ollama is constantly adding new models. Check for updates:

```bash
ollama list
```

Notable recent additions:
- **DeepSeek-R1**: Advanced reasoning (requires 32GB+)
- **Gemma 3**: Google's latest open models
- **Phi-4**: Microsoft's efficient reasoning model (included)

## Resources

- [Ollama Library](https://ollama.com/library)
- [Model Cards](https://ollama.com/library) - Full specs and benchmarks
- [Ollama GitHub](https://github.com/ollama/ollama)
