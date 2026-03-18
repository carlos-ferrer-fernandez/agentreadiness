---
title: "Contribute to AgentReadiness"
description: "Development setup, code style, testing, and PR guidelines for contributing to AgentReadiness"
version: "0.3.0"
last_updated: "2026-03-18"
tags: ["contributing", "development", "testing", "code-style"]
prerequisites: ["Node.js 20+", "Python 3.11+", "Docker and Docker Compose", "Git"]
---

# Contribute to AgentReadiness

> To contribute, you need a working local development environment and familiarity with React/TypeScript (frontend) or Python/FastAPI (backend).

## Prerequisites

Before starting, ensure you have:

- [ ] Node.js 20+ installed
- [ ] Python 3.11+ installed
- [ ] Docker and Docker Compose installed
- [ ] Git installed
- [ ] The repository cloned (see [README.md](README.md) for setup)

## Set Up Your Development Environment

```bash
# Clone the repository
git clone https://github.com/carlos-ferrer-fernandez/agentreadiness.git
cd agentreadiness

# Start all services (database, Redis, API, frontend)
docker-compose up -d
```

Expected result:
```
✔ Container agentreadiness-db-1     Started
✔ Container agentreadiness-redis-1  Started
✔ Container agentreadiness-api-1    Started
✔ Container agentreadiness-web-1    Started
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

## Project Structure

```
agentreadiness/
├── apps/
│   ├── web/              # React + TypeScript + Vite frontend
│   │   ├── src/
│   │   │   ├── components/   # Reusable UI components (shadcn/ui based)
│   │   │   ├── sections/     # Full page sections (LandingPage, AssessmentResults)
│   │   │   ├── lib/          # API client (axios), utilities
│   │   │   └── store/        # Zustand state management
│   │   └── package.json
│   └── api/              # FastAPI backend
│       ├── routers/          # API route handlers
│       ├── services/         # Business logic (evaluator, optimizer, crawler)
│       ├── models.py         # SQLAlchemy ORM models
│       ├── config.py         # Pydantic settings (env vars)
│       └── main.py           # FastAPI app entry point
├── docker-compose.yml
└── .github/workflows/    # CI pipeline (lint, type-check, test, build)
```

## Development Workflow

### Step 1: Create a branch

```bash
git checkout -b feature/your-feature-name
```

### Step 2: Make changes

Follow the code style guidelines below. Key files you'll likely work with:

| Area | Key Files |
|------|-----------|
| Landing page UI | `apps/web/src/sections/LandingPage.tsx` |
| Assessment results | `apps/web/src/sections/AssessmentResults.tsx` |
| 20-rule evaluation engine | `apps/api/services/evaluator/rule_analyzer.py` |
| Documentation optimizer | `apps/api/services/optimizer/document_optimizer.py` |
| API endpoints | `apps/api/routers/assessments.py`, `apps/api/routers/optimizer.py` |
| Pricing logic | `apps/api/pricing.py` |
| State management | `apps/web/src/store/assessment.ts` |

### Step 3: Run tests and checks

```bash
# Frontend: TypeScript type check
cd apps/web && npx tsc --noEmit

# Backend: Lint with flake8
cd apps/api && flake8 .

# Backend: Type check with mypy
cd apps/api && mypy .

# Backend: Run tests
cd apps/api && pytest
```

> **⚠️ Warning:** CI runs all of these checks on every push. If any check fails, the build fails. Always run locally before pushing.

### Step 4: Commit using conventional commits

```bash
git commit -m "feat: add new rule to evaluation engine"
git commit -m "fix: resolve pricing calculation edge case"
git commit -m "docs: update README with new API endpoints"
git commit -m "refactor: simplify optimizer prompt construction"
```

### Step 5: Push and create a pull request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub targeting the `main` branch.

## Code Style

### Frontend (TypeScript / React)

| Convention | Example |
|-----------|---------|
| Functional components with hooks | `export function ScoreCard({ score }: Props) {}` |
| Tailwind CSS for styling | `className="text-sm text-muted-foreground"` |
| `cn()` utility for conditional classes | `cn("text-sm", isActive && "font-bold")` |
| Zustand for state management | `useAssessmentStore()` |
| Axios for API calls | `assessmentsApi.analyze({ url })` |

```tsx
import { cn } from '@/lib/utils'

interface ScoreDisplayProps {
  score: number
  grade: string
}

export function ScoreDisplay({ score, grade }: ScoreDisplayProps) {
  return (
    <div className={cn(
      "text-3xl font-bold",
      score >= 80 ? "text-green-600" :
      score >= 60 ? "text-yellow-600" : "text-red-600"
    )}>
      {score} ({grade})
    </div>
  )
}
```

### Backend (Python / FastAPI)

| Convention | Example |
|-----------|---------|
| PEP 8 style | `def calculate_score(pages: list) -> int:` |
| Type hints on all functions | `async def analyze(url: str) -> RuleAnalysisResult:` |
| Docstrings on public functions | `"""Evaluate docs against 20 rules."""` |
| Async/await for I/O | `await client.get(url)` |
| Pydantic for request/response models | `class AnalyzeRequest(BaseModel):` |

```python
from typing import List
from dataclasses import dataclass

@dataclass
class RuleResult:
    """Result of evaluating one rule across all pages."""
    rule_id: int
    name: str
    score: int      # 0-100
    status: str     # 'pass', 'warning', 'fail'
    finding: str    # Human-readable explanation

async def evaluate_rule(pages: List[Page]) -> RuleResult:
    """Evaluate a single agent-readiness rule across all crawled pages.

    Args:
        pages: List of crawled documentation pages

    Returns:
        RuleResult with score, status, and finding
    """
    # Implementation
```

## Add a New Agent-Readiness Rule

To add rule #21 (or modify an existing rule):

1. **Add the evaluation logic** in `apps/api/services/evaluator/rule_analyzer.py`:
   - Create method `_rule_21_your_rule(self, pages)` returning a `RuleResult`
   - Add it to the `analyze()` method's rule list

2. **Add the optimization prompt** in `apps/api/services/optimizer/document_optimizer.py`:
   - Add `### RULE 21: YOUR RULE NAME` to the `OPTIMIZATION_RULES` constant

3. **Map to a component** in `rule_analyzer.py`:
   - Add rule ID 21 to the appropriate component in `RULE_COMPONENTS`

4. **Update the frontend rule list** in `apps/web/src/sections/LandingPage.tsx`:
   - Add entry to the `agentReadinessRules` array

5. **Run tests** to verify nothing breaks

## Database Migrations

```bash
cd apps/api

# Create a new migration
alembic revision --autogenerate -m "add column to assessments"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

> **⚠️ Warning:** Always review auto-generated migrations before applying. Alembic can miss some changes or generate destructive operations.

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Add screenshots for UI changes
- Ensure CI passes (lint + type-check + tests + build)
- Link related GitHub issues
- Describe what changed and why in the PR description

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
