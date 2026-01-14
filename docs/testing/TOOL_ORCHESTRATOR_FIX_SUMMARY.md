# Tool Orchestrator Test Fix Summary
**Date:** 2026-01-13
**Status:** Partially Fixed (1/11 tests)

## Problem Identified ✅

All 11 tool orchestrator E2E tests were failing with generic error message:
```
"I encountered an error while processing your request: "
```

## Root Cause Analysis ✅

**The Issue:** Circuit breaker state persisting across tests

1. `ollama_circuit_breaker` is a global singleton in `app/core/retry.py:239`
2. When earlier tests run and Ollama isn't available, circuit breaker opens (5 failures threshold)
3. Circuit breaker stays open for 60 seconds (recovery_timeout)
4. Subsequent tests inherit the open circuit breaker state
5. Circuit breaker raises `CircuitBreakerOpen` exception **before** mocked methods can execute
6. Exception caught at `tool_orchestrator.py:101-103` → returns generic error message

**Code Flow:**
```python
# tool_orchestrator.py lines 95-103
try:
    llm_response = await self.llm_service._generate_response(...)
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    return f"I encountered an error while processing your request: {str(e)}"
```

When circuit breaker is open:
- `_generate_response()` decorated with `@retry_with_backoff(circuit_breaker=ollama_circuit_breaker)`
- Decorator checks circuit breaker state (line 132 in retry.py)
- Raises `CircuitBreakerOpen` before calling actual method
- Mock never gets called
- Generic error returned

## Solution Implemented ✅

### Fix 1: Reset Circuit Breakers Between Tests

**File:** `tests/conftest.py`

Added auto-use fixture to reset all circuit breakers before/after each test:

```python
@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset all circuit breakers before each test."""
    ollama_circuit_breaker.reset()
    embedding_circuit_breaker.reset()
    vector_db_circuit_breaker.reset()
    yield
    # Reset again after test to prevent state leakage
    ollama_circuit_breaker.reset()
    embedding_circuit_breaker.reset()
    vector_db_circuit_breaker.reset()
```

**Impact:** Ensures clean state for every test, prevents cascade failures

### Fix 2: Mock at Correct Level

**File:** `tests/integration/test_tool_orchestrator_e2e.py`

**Before (Incorrect):**
```python
with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
    mock_llm = Mock()
    mock_llm_service.return_value = mock_llm
    mock_llm._generate_response = AsyncMock(side_effect=[...])
```

**After (Correct):**
```python
with patch('app.services.llm_service.LLMService._generate_response') as mock_generate:
    mock_generate.side_effect = [...]
```

**Why This Works:**
- Patches the actual method before the decorator intercepts it
- Circuit breaker check happens in decorator, but mock is at method level
- Simpler, cleaner mock setup

## Tests Fixed ✅

1. ✅ `test_orchestrator_with_calculator_single_step` - FIXED

## Tests Remaining ⚠️

Need to apply same pattern to 10 more tests:

2. ⚠️ `test_orchestrator_with_multiple_tool_calls`
3. ⚠️ `test_orchestrator_max_iterations_reached`
4. ⚠️ `test_orchestrator_handles_tool_failure`
5. ⚠️ `test_orchestrator_with_code_executor`
6. ⚠️ `test_orchestrator_respects_tool_access_control`
7. ⚠️ `test_orchestrator_parses_plain_text_response`
8. ⚠️ `test_orchestrator_iteration_callbacks`
9. ⚠️ (4 more tests...)

**Fix Pattern (Apply to Each):**

```bash
# Step 1: Change patch line
- with patch('app.services.tool_orchestrator.get_llm_service') as mock_llm_service:
+ with patch('app.services.llm_service.LLMService._generate_response') as mock_generate:

# Step 2: Remove these lines
- mock_llm = Mock()
- mock_llm_service.return_value = mock_llm

# Step 3: Change AsyncMock assignment
- mock_llm._generate_response = AsyncMock(side_effect=[...])
+ mock_generate.side_effect = [...]

# Step 4: Fix call_count references
- assert mock_llm._generate_response.call_count == 2
+ assert mock_generate.call_count == 2
```

## Verification Steps

After fixing all tests:

1. **Run Tool Orchestrator Tests:**
   ```bash
   cd backend
   python -m pytest tests/integration/test_tool_orchestrator_e2e.py -v
   ```

2. **Expected Result:**
   - All 11 tests should pass
   - No "I encountered an error..." messages
   - Tool calls should execute properly

3. **Verify Circuit Breaker Reset:**
   ```bash
   # Run tests multiple times - should pass consistently
   python -m pytest tests/integration/test_tool_orchestrator_e2e.py -v --count=3
   ```

## Additional Fixes Needed

### Other Tests With Same Issue

Check these test files for similar circuit breaker problems:

- `tests/unit/test_llm_service.py` - 5 failures (circuit breaker)
- `tests/integration/test_chat_api.py` - May have similar issues

### Prevention

Consider adding to CI/CD:

```python
# In conftest.py or test base class
def pytest_configure(config):
    """Reset all circuit breakers at test session start."""
    from app.core.retry import (
        ollama_circuit_breaker,
        embedding_circuit_breaker,
        vector_db_circuit_breaker
    )
    ollama_circuit_breaker.reset()
    embedding_circuit_breaker.reset()
    vector_db_circuit_breaker.reset()
```

## Lessons Learned

1. **Global State is Dangerous in Tests**
   - Circuit breakers, caches, singletons can leak between tests
   - Always reset shared state in fixtures

2. **Mock at the Right Level**
   - Decorators intercept calls before reaching mocked methods
   - Mock the decorated method directly, not its factory

3. **Test Isolation is Critical**
   - One failing test shouldn't cascade to others
   - Use `autouse=True` fixtures for cleanup

4. **Circuit Breaker Design**
   - Consider making circuit breaker optional in tests
   - Or provide test-mode circuit breakers with shorter timeouts

## Time Estimate

**Remaining Work:** 30-45 minutes
- Apply same fix pattern to 10 remaining tests
- Run test suite to verify
- Fix any edge cases

**Automated Approach:**
Could write a script to apply the pattern automatically using regex/sed, but manual review recommended to ensure correctness.

---

**Status:** Root cause identified and fixed. Circuit breaker reset implemented. One test verified working. Pattern documented for remaining fixes.
