# Agentic RAG Testing Guide

## 🎯 What We Built

An **agentic RAG system** where the LLM autonomously decides:
- **When** to search your knowledge base
- **What** to search for
- **How many times** to search (multi-step reasoning)

## 🚀 How to Test

### Step 1: Open the App
Navigate to: **http://localhost:5173**

### Step 2: Upload Test Document (Optional)
I created `test_agentic_rag.md` in the project root. You can:
1. Go to Documents page
2. Upload `test_agentic_rag.md`
3. Wait for processing (creates embeddings)

### Step 3: Enable Agent Mode
In the chat interface, look for the toggle buttons at the bottom:
- Find the **blue "Standard" button** next to the Socratic mode toggle
- Click it to enable **"✓ Agent"** mode
- The button will turn blue when active

### Step 4: Choose Your Model
Agent mode works best with local Ollama models:
- **Qwen 2.5 14B** (recommended - best reasoning)
- **Phi-4 14B** (strong reasoning)
- **Llama 3.2 3B** (faster but less capable)

**Note**: Agent mode currently works with Ollama models only (not Gemini)

### Step 5: Try These Test Queries

#### Test 1: Simple Math (Should Skip Retrieval)
```
What is 2 + 2?
```
**Expected**: Agent realizes this is basic math, doesn't search knowledge base, answers directly.

#### Test 2: Knowledge Question (Should Search Once)
```
What is agentic RAG?
```
**Expected**: Agent searches knowledge base once, finds info from test document, provides answer with context.

#### Test 3: Multi-Part Question (Should Search Multiple Times)
```
First tell me about agentic RAG benefits, then explain the implementation details.
```
**Expected**: Agent performs 2 searches - one for benefits, one for implementation.

#### Test 4: Comparison Query (Complex Reasoning)
```
Compare traditional RAG with agentic RAG. What are the key differences?
```
**Expected**: Agent searches for both concepts, compares them intelligently.

#### Test 5: General Knowledge (Should Skip)
```
Who was the first president of the United States?
```
**Expected**: Agent recognizes this as general knowledge, answers without searching.

## 🔍 What to Watch For

### In the Browser
- **Status message**: "🤖 Agent mode: Analyzing your question..."
- **Response appears all at once** (non-streaming for now)
- **Sources shown** if knowledge base was searched
- **Response quality** - does it make sense?

### In Backend Logs (Terminal)
Look for these log messages:
```
INFO: Agent mode enabled - using tool orchestrator
INFO: Tool orchestration iteration 1/5
INFO: Tool knowledge_search executed: success=True
INFO: LLM response parsed: 1 tool calls, final_answer=No
INFO: Final answer received from LLM
```

## ✅ Success Criteria

The agent mode is working if:
1. ✅ Simple queries don't trigger knowledge search
2. ✅ Knowledge questions trigger appropriate searches
3. ✅ Multi-step queries trigger multiple searches
4. ✅ Responses are coherent and cite sources when used
5. ✅ Backend logs show tool calls and iterations

## 🐛 Troubleshooting

### "Agent mode not working"
- Check that you selected an Ollama model (not Gemini)
- Ensure backend is running (`uvicorn app.main:app --reload --port 8000`)
- Check backend logs for errors

### "No results from knowledge search"
- Upload a document first (or it searches empty database)
- Try enabling "Docs" mode (includes personal notes)
- Check if the query is relevant to uploaded documents

### "Response is slow"
- Agent mode uses non-streaming (waits for complete response)
- Multiple tool calls take longer
- Qwen 2.5 14B is slower but more accurate than Llama 3.2 3B

### "Agent searches when it shouldn't"
- This is a tuning issue with the prompt
- The agent is being cautious (better safe than sorry)
- Can be improved with better prompts

## 📊 How It Works (Behind the Scenes)

```
User Query
    ↓
Agent Analyzes Query
    ↓
Decision: Need Knowledge?
    ├─ No → Answer Directly
    └─ Yes → Search Knowledge Base
            ↓
        Get Results
            ↓
        More Searches Needed?
            ├─ Yes → Refine Query & Search Again
            └─ No → Generate Final Answer
```

## 🎨 UI Elements

**Agent Mode Toggle**:
- Location: Bottom of chat input, next to Socratic mode
- Icon: 🤖 Bot icon
- Colors: Blue when active, gray when inactive
- Label: "✓ Agent" or "Standard"

**Source Filter** (affects what agent searches):
- **General**: Skips RAG entirely (general knowledge only)
- **Docs**: Searches documents + notes
- **Web**: Searches documents + web (agent can't use web search yet)

## 🚧 Current Limitations

1. **No streaming**: Agent mode uses non-streaming for now
2. **No tool visibility**: You don't see individual tool calls yet
3. **Ollama only**: Doesn't work with Gemini models yet
4. **Single tool**: Only knowledge search tool (no web, calculator, etc.)
5. **Max 5 iterations**: Prevents infinite loops

## 🔮 Future Enhancements

- **Streaming support**: Real-time tool call visibility
- **More tools**: Web search, calculator, code execution
- **Better prompts**: Smarter decision-making
- **Gemini support**: Use Gemini's native function calling
- **Tool call history**: See what the agent searched for

## 📝 Example Conversation

```
User: What is 2+2?
Agent: [Thinks] This is basic math, no search needed
Agent: 4

User: What is agentic RAG?
Agent: [Searches: "agentic RAG"]
Agent: [Found 3 sources]
Agent: Agentic RAG is an advanced retrieval-augmented generation approach where the LLM autonomously decides when and how to retrieve information... [continues with context from your documents]
Sources: test_agentic_rag.md
```

---

**Ready to test!** Open http://localhost:5173 and start chatting 🚀
