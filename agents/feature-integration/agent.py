#!/usr/bin/env python3
"""
Feature Integration Agent

This agent handles end-to-end feature development across the full stack:
- Backend: Service + API endpoint + schemas
- Frontend: Service + components + hooks
- Database: Models + migrations (if needed)
- Tests: Backend + frontend tests
- Documentation: API docs + component docs

Usage:
    python agent.py --feature "feature-name" --spec "feature-spec.md"
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

from anthropic import Anthropic


class FeatureIntegrationAgent:
    """Agent that builds features end-to-end across the full stack."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.project_root = project_root
        self.backend_root = project_root / "backend"
        self.frontend_root = project_root / "frontend"
        self.conversation_history: List[Dict] = []

    def _add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    async def analyze_feature_spec(self, spec: str) -> Dict:
        """Analyze feature specification and break down into tasks."""
        print("📋 Analyzing feature specification...")

        prompt = f"""You are a full-stack architect analyzing a feature specification.

Feature Specification:
{spec}

Your task is to break this down into a structured implementation plan with these sections:

1. **Backend Requirements**:
   - Service methods needed
   - API endpoints (HTTP method, path, request/response schemas)
   - Database models (if any)
   - Dependencies on existing services

2. **Frontend Requirements**:
   - React components needed
   - Service methods for API calls
   - Custom hooks
   - State management needs
   - UI/UX considerations

3. **Testing Requirements**:
   - Backend unit tests
   - Backend integration tests
   - Frontend component tests
   - E2E scenarios

4. **Implementation Order**:
   - Step-by-step sequence
   - Dependencies between steps

Format your response as JSON with these keys: backend, frontend, testing, implementation_order.
Each should be a list of specific, actionable tasks.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        self._add_message("user", prompt)
        self._add_message("assistant", content)

        # Parse JSON from response
        import json
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            plan = json.loads(content)
            print("✅ Feature analysis complete")
            return plan
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse plan: {e}")
            print(f"Response was: {content}")
            return {}

    async def generate_backend_service(self, feature_name: str, requirements: List[str]) -> str:
        """Generate backend service code."""
        print(f"⚙️  Generating backend service for {feature_name}...")

        # Read existing project patterns
        rag_service = self._read_file(self.backend_root / "app/services/rag_service.py")

        prompt = f"""You are a backend Python developer working on a FastAPI project.

Feature: {feature_name}
Requirements:
{chr(10).join(f'- {req}' for req in requirements)}

Here's an example service from the project:
```python
{rag_service}
```

Generate a complete Python service file that:
1. Uses async/await for all I/O operations
2. Has proper type hints
3. Includes docstrings
4. Follows the project's patterns
5. Uses LLM service, RAG service, or database as needed
6. Handles errors gracefully

Return ONLY the Python code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=8000,
            messages=self.conversation_history + [{"role": "user", "content": prompt}]
        )

        code = response.content[0].text
        self._add_message("user", prompt)
        self._add_message("assistant", code)

        # Clean code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()

        print("✅ Backend service generated")
        return code

    async def generate_backend_endpoint(self, feature_name: str, service_code: str,
                                       endpoints: List[str]) -> str:
        """Generate backend API endpoint code."""
        print(f"🔌 Generating API endpoint for {feature_name}...")

        # Read existing endpoint pattern
        chat_endpoint = self._read_file(self.backend_root / "app/api/v1/endpoints/chat.py")

        prompt = f"""You are a backend API developer working on a FastAPI project.

Feature: {feature_name}
Service Code:
```python
{service_code}
```

Endpoints Needed:
{chr(10).join(f'- {ep}' for ep in endpoints)}

Here's an example endpoint from the project:
```python
{chat_endpoint}
```

Generate a complete FastAPI router file that:
1. Imports the service
2. Creates router with appropriate prefix
3. Implements all required endpoints
4. Uses proper Pydantic schemas
5. Has async database sessions
6. Returns proper HTTP status codes
7. Includes docstrings

Return ONLY the Python code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=8000,
            messages=self.conversation_history + [{"role": "user", "content": prompt}]
        )

        code = response.content[0].text
        self._add_message("user", prompt)
        self._add_message("assistant", code)

        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()

        print("✅ API endpoint generated")
        return code

    async def generate_backend_schemas(self, feature_name: str, endpoints: List[str]) -> str:
        """Generate Pydantic schemas for request/response."""
        print(f"📦 Generating Pydantic schemas for {feature_name}...")

        # Read existing schemas
        chat_schemas = self._read_file(self.backend_root / "app/schemas/conversation.py")

        prompt = f"""You are a backend developer creating Pydantic schemas.

Feature: {feature_name}
Endpoints:
{chr(10).join(f'- {ep}' for ep in endpoints)}

Example schemas from the project:
```python
{chat_schemas}
```

Generate Pydantic schema models for:
1. Request models (with validation)
2. Response models
3. Any nested models needed
4. Proper Field descriptions

Return ONLY the Python code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=6000,
            messages=self.conversation_history + [{"role": "user", "content": prompt}]
        )

        code = response.content[0].text
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()

        print("✅ Schemas generated")
        return code

    async def generate_frontend_service(self, feature_name: str, backend_endpoints: List[str]) -> str:
        """Generate frontend service for API calls."""
        print(f"🌐 Generating frontend service for {feature_name}...")

        # Read existing service
        chat_service = self._read_file(self.frontend_root / "src/services/chatService.ts")

        prompt = f"""You are a frontend TypeScript developer.

Feature: {feature_name}
Backend Endpoints:
{chr(10).join(f'- {ep}' for ep in backend_endpoints)}

Example service from the project:
```typescript
{chat_service}
```

Generate a TypeScript service file that:
1. Uses the apiClient from './api'
2. Has proper TypeScript interfaces
3. Exports service methods
4. Handles errors
5. Uses async/await
6. Matches backend API structure

Return ONLY the TypeScript code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=6000,
            messages=self.conversation_history + [{"role": "user", "content": prompt}]
        )

        code = response.content[0].text
        if "```typescript" in code:
            code = code.split("```typescript")[1].split("```")[0].strip()
        elif "```ts" in code:
            code = code.split("```ts")[1].split("```")[0].strip()

        print("✅ Frontend service generated")
        return code

    async def generate_frontend_component(self, feature_name: str,
                                         component_spec: str, service_code: str) -> str:
        """Generate React component."""
        print(f"⚛️  Generating React component for {feature_name}...")

        # Read existing component
        context_panel = self._read_file(self.frontend_root / "src/components/context/ContextPanel.tsx")

        prompt = f"""You are a React TypeScript developer.

Feature: {feature_name}
Component Specification: {component_spec}

Service Code:
```typescript
{service_code}
```

Example component from the project:
```typescript
{context_panel}
```

Generate a complete React component that:
1. Uses TypeScript with proper interfaces
2. Uses React hooks (useState, useEffect, etc.)
3. Uses Tailwind CSS for styling
4. Has proper props interface exported
5. Includes accessibility (ARIA labels)
6. Handles loading and error states
7. Follows project patterns
8. Uses lucide-react for icons

Return ONLY the TypeScript code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=10000,
            messages=self.conversation_history + [{"role": "user", "content": prompt}]
        )

        code = response.content[0].text
        if "```typescript" in code:
            code = code.split("```typescript")[1].split("```")[0].strip()
        elif "```tsx" in code:
            code = code.split("```tsx")[1].split("```")[0].strip()

        print("✅ React component generated")
        return code

    async def generate_tests(self, feature_name: str, code: str, test_type: str) -> str:
        """Generate tests for backend or frontend."""
        print(f"🧪 Generating {test_type} tests for {feature_name}...")

        if test_type == "backend":
            example_test = self._read_file(self.backend_root / "tests/unit/test_rag_service.py")
            framework = "pytest"
        else:
            example_test = self._read_file(self.frontend_root / "src/components/MessageList.test.tsx")
            framework = "vitest + Testing Library"

        prompt = f"""You are a test engineer writing {test_type} tests.

Feature: {feature_name}
Code to Test:
```
{code}
```

Example test from the project:
```
{example_test}
```

Generate comprehensive tests using {framework} that:
1. Test happy paths
2. Test edge cases
3. Test error handling
4. Use proper mocks
5. Have clear test names
6. Follow project patterns
7. Aim for >80% coverage

Return ONLY the test code, no explanations.
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```typescript" in code:
            code = code.split("```typescript")[1].split("```")[0].strip()
        elif "```tsx" in code:
            code = code.split("```tsx")[1].split("```")[0].strip()

        print("✅ Tests generated")
        return code

    def _read_file(self, path: Path) -> str:
        """Read file contents."""
        try:
            return path.read_text()
        except Exception as e:
            print(f"⚠️  Could not read {path}: {e}")
            return ""

    def _write_file(self, path: Path, content: str):
        """Write file contents."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"✅ Written: {path}")

    async def build_feature(self, feature_name: str, spec: str):
        """Build a complete feature end-to-end."""
        print(f"\n{'='*60}")
        print(f"🚀 Building Feature: {feature_name}")
        print(f"{'='*60}\n")

        # Step 1: Analyze spec
        plan = await self.analyze_feature_spec(spec)

        if not plan:
            print("❌ Failed to create plan. Exiting.")
            return

        print("\n📋 Implementation Plan:")
        print(f"Backend tasks: {len(plan.get('backend', []))}")
        print(f"Frontend tasks: {len(plan.get('frontend', []))}")
        print(f"Testing tasks: {len(plan.get('testing', []))}")

        # Step 2: Generate backend
        backend_reqs = plan.get('backend', [])
        if backend_reqs:
            service_code = await self.generate_backend_service(feature_name, backend_reqs)
            service_path = self.backend_root / f"app/services/{feature_name}_service.py"
            self._write_file(service_path, service_code)

            endpoints = [req for req in backend_reqs if 'endpoint' in req.lower() or 'API' in req]
            if endpoints:
                endpoint_code = await self.generate_backend_endpoint(feature_name, service_code, endpoints)
                endpoint_path = self.backend_root / f"app/api/v1/endpoints/{feature_name}.py"
                self._write_file(endpoint_path, endpoint_code)

                schema_code = await self.generate_backend_schemas(feature_name, endpoints)
                schema_path = self.backend_root / f"app/schemas/{feature_name}.py"
                self._write_file(schema_path, schema_code)

        # Step 3: Generate frontend
        frontend_reqs = plan.get('frontend', [])
        if frontend_reqs:
            api_endpoints = [req for req in backend_reqs if 'endpoint' in req.lower()]
            service_code = await self.generate_frontend_service(feature_name, api_endpoints)
            service_path = self.frontend_root / f"src/services/{feature_name}Service.ts"
            self._write_file(service_path, service_code)

            component_reqs = [req for req in frontend_reqs if 'component' in req.lower()]
            for component_req in component_reqs:
                component_code = await self.generate_frontend_component(
                    feature_name, component_req, service_code
                )
                # Extract component name from requirement
                component_name = feature_name.title().replace('_', '') + 'Component'
                component_path = self.frontend_root / f"src/components/{feature_name}/{component_name}.tsx"
                self._write_file(component_path, component_code)

        # Step 4: Generate tests
        testing_reqs = plan.get('testing', [])
        if testing_reqs and backend_reqs:
            backend_tests = await self.generate_tests(feature_name, service_code, "backend")
            test_path = self.backend_root / f"tests/unit/test_{feature_name}_service.py"
            self._write_file(test_path, backend_tests)

        print(f"\n{'='*60}")
        print(f"✅ Feature '{feature_name}' built successfully!")
        print(f"{'='*60}\n")

        print("📝 Next steps:")
        print("1. Review generated code")
        print("2. Run tests: pytest tests/ (backend), npm test (frontend)")
        print("3. Register new router in backend/app/api/v1/api.py")
        print("4. Import and use components in frontend pages")
        print("5. Create database migration if models were added")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Feature Integration Agent")
    parser.add_argument("--feature", required=True, help="Feature name (snake_case)")
    parser.add_argument("--spec", required=True, help="Path to feature specification file")

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Read spec file
    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"❌ Spec file not found: {spec_path}")
        sys.exit(1)

    spec = spec_path.read_text()

    # Build feature
    agent = FeatureIntegrationAgent(api_key)
    await agent.build_feature(args.feature, spec)


if __name__ == "__main__":
    asyncio.run(main())
