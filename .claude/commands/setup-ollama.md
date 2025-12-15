# Setup Ollama Models

Install and configure Ollama with the required models for the knowledge assistant.

## 1. Install Ollama

```bash
brew install ollama
```

## 2. Start Ollama Service

```bash
# Start in background
ollama serve &

# Or start as a service (recommended)
brew services start ollama
```

## 3. Pull Required Models

This will download ~18GB of models. It may take 10-30 minutes depending on your internet speed.

```bash
# Primary model for Q&A (8GB)
ollama pull qwen2.5:14b

# Reasoning model (8GB)
ollama pull phi4:14b

# Fast model for quick queries (2GB)
ollama pull llama3.2:3b
```

## 4. Verify Models

```bash
# List installed models
ollama list

# Test each model
ollama run qwen2.5:14b "Hello, how are you?"
ollama run phi4:14b "What is 2+2?"
ollama run llama3.2:3b "Hi there"
```

## 5. Configure Backend

The `.env` file is already configured with these models. If you change models, update:

```env
OLLAMA_PRIMARY_MODEL=qwen2.5:14b
OLLAMA_REASONING_MODEL=phi4:14b
OLLAMA_FAST_MODEL=llama3.2:3b
```

## Troubleshooting

### Ollama not found
```bash
which ollama
# If not found, add to PATH or reinstall
```

### Model download fails
```bash
# Check connection
curl https://ollama.com

# Try pulling again
ollama pull <model_name>
```

### Port already in use
```bash
# Check what's on port 11434
lsof -i:11434

# Kill if needed
kill -9 <PID>
```

## See Also

- `/docs/OLLAMA_MODELS.md` - Detailed model guide
- [Ollama Documentation](https://github.com/ollama/ollama)
