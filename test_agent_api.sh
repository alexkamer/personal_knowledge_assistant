#!/bin/bash
# Test agentic RAG via API

echo "============================================"
echo "Testing Agentic RAG via Chat API"
echo "============================================"

# Test 1: Simple math (should NOT use knowledge search)
echo ""
echo "Test 1: Simple math query (should skip retrieval)"
echo "Query: What is 2 + 2?"
echo "---"
curl -s -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is 2 + 2?",
    "model": "qwen2.5:14b",
    "agent_mode": true
  }' | head -20

echo ""
echo ""

# Test 2: Knowledge question (should use knowledge search)
echo "Test 2: Knowledge question (should search if doc exists)"
echo "Query: What is agentic RAG?"
echo "---"
curl -s -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is agentic RAG?",
    "model": "qwen2.5:14b",
    "agent_mode": true
  }' | head -20

echo ""
echo ""
echo "============================================"
echo "Check backend logs for tool call details"
echo "============================================"
