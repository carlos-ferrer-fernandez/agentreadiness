# Contributing to AgentReadiness

Thank you for your interest in contributing to AgentReadiness! This guide will help you get started.

## Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker and Docker Compose
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/agentreadiness.git
cd agentreadiness

# Install dependencies
make install

# Start development servers
make dev
```

This will start:
- Frontend at http://localhost:3000
- Backend at http://localhost:8000
- API docs at http://localhost:8000/docs

## Project Structure

```
agentreadiness/
├── apps/
│   ├── web/              # React + TypeScript + Vite frontend
│   └── api/              # FastAPI backend
├── packages/
│   └── shared/           # Shared types and utilities
├── infra/
│   └── docker/           # Docker configurations
└── docs/                 # Documentation
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the existing code style
- Write tests for new features
- Update documentation

### 3. Test

```bash
# Frontend tests
cd apps/web && npm test

# Backend tests
cd apps/api && pytest

# Type checking
cd apps/web && npx tsc --noEmit
cd apps/api && mypy .
```

### 4. Commit

We use conventional commits:

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update readme"
git commit -m "refactor: improve code structure"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Frontend (TypeScript/React)

- Use functional components with hooks
- Follow the existing component patterns
- Use Tailwind CSS for styling
- Use `cn()` utility for conditional classes

Example:
```tsx
import { cn } from '@/lib/utils'

interface ButtonProps {
  variant?: 'primary' | 'secondary'
  children: React.ReactNode
}

export function Button({ variant = 'primary', children }: ButtonProps) {
  return (
    <button className={cn(
      'px-4 py-2 rounded',
      variant === 'primary' && 'bg-blue-500',
      variant === 'secondary' && 'bg-gray-500'
    )}>
      {children}
    </button>
  )
}
```

### Backend (Python)

- Follow PEP 8
- Use type hints
- Write docstrings for functions
- Use async/await for I/O operations

Example:
```python
from typing import List, Optional

async def get_sites(
    organization_id: str,
    status: Optional[str] = None
) -> List[Site]:
    """Get sites for an organization.
    
    Args:
        organization_id: The organization ID
        status: Optional status filter
        
    Returns:
        List of sites
    """
    # Implementation
```

## Testing

### Frontend Tests

```bash
cd apps/web
npm test
```

Write tests using Vitest and React Testing Library:

```tsx
import { render, screen } from '@testing-library/react'
import { Button } from './Button'

test('renders button', () => {
  render(<Button>Click me</Button>)
  expect(screen.getByText('Click me')).toBeInTheDocument()
})
```

### Backend Tests

```bash
cd apps/api
pytest
```

Write tests using pytest:

```python
import pytest
from services.evaluator.scorer import FriendlinessScorer

def test_score_calculation():
    scorer = FriendlinessScorer()
    results = [
        QueryResult(query="test", passed=True, confidence=0.9, ...)
    ]
    score = scorer.calculate_score(results)
    assert score.overall > 0
```

## Database Migrations

```bash
# Create migration
cd apps/api
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

Create a `.env.local` file for local development:

```env
# Frontend
VITE_API_URL=http://localhost:8000

# Backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentreadiness
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
```

## Debugging

### Frontend

- Use React DevTools browser extension
- Check console for errors
- Use `debugger` statement or VS Code debugger

### Backend

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger
```

## Common Tasks

### Add a New API Endpoint

1. Create route in `apps/api/routers/`
2. Add Pydantic models for request/response
3. Implement business logic
4. Add tests
5. Update API docs (auto-generated)

### Add a New UI Component

1. Create component in `apps/web/src/components/ui/`
2. Follow existing patterns
3. Add to exports if needed
4. Add Storybook story (optional)

### Add a Database Model

1. Define model in `apps/api/models/`
2. Create migration
3. Add CRUD operations
4. Update API endpoints

## Pull Request Guidelines

- Keep PRs focused and small
- Add screenshots for UI changes
- Link related issues
- Ensure CI passes
- Request review from at least one team member

## Release Process

1. Update version in `package.json` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Push to trigger deployment

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Getting Help

- Check the [Documentation](https://docs.agentreadiness.dev)
- Ask in [Discord](https://discord.gg/agentreadiness)
- Email: dev@agentreadiness.dev

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
