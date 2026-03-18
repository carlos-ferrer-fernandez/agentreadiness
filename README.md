---
title: "AgentReadiness — Make your documentation AI-agent ready"
description: "SaaS that evaluates documentation against 20 agent-readiness rules and delivers optimized files"
version: "0.3.0"
last_updated: "2026-03-18"
tags: ["agentreadiness", "documentation", "ai-agents", "llms-txt", "rag", "optimization"]
prerequisites: ["Docker and Docker Compose", "Node.js 20+", "Python 3.11+", "OpenAI API key", "Stripe account"]
---

# AgentReadiness

> AI agents are how developers discover tools now. If your documentation isn't optimized for them, they can't recommend you. AgentReadiness scores your docs against 20 concrete rules and delivers the optimized files.

## What AgentReadiness Does

AgentReadiness evaluates documentation against **20 agent-readiness rules** derived from benchmarking 8 major AI agents (Claude, GPT, Gemini, Grok, Kimi, Deepseek, Manus, KimiClaw). It then rewrites every page applying all 20 rules and delivers the optimized files as a downloadable ZIP.

**The output is not a report.** It is the actual optimized documentation — structured Markdown files with YAML frontmatter, an `llms.txt` agent entry point, and a deployment guide. Users download the ZIP and deploy.

### User Flow

| Step | What Happens | Cost |
|------|-------------|------|
| 1. Enter docs URL | Free scan evaluates docs against 20 rules | Free |
| 2. See rule-by-rule results | Score (0-100), grade (A+ to F), per-rule findings | Free |
| 3. Purchase optimized docs | Exact price shown based on documentation size | From €49 |
| 4. Download ZIP | Every page rewritten + `llms.txt` + deployment guide | One-time |

### Pricing

Price is calculated based on documentation size. Starting at €49 for small docs, scaling with the number of pages that need to be rewritten. The exact price is shown after the free scan. No subscriptions, no tiers, no consulting calls.

## The 20 Agent-Readiness Rules

These rules are the consensus from 8 major AI agents on what makes documentation machine-consumable:

| # | Rule | What It Checks |
|---|------|---------------|
| 1 | Self-Contained Sections | No "see above" — every section stands alone for RAG retrieval |
| 2 | Action-Oriented Headings | Headings match user/agent intents, not topic labels |
| 3 | Structured Parameter Tables | Parameters in tables (name, type, required, default), not prose |
| 4 | Complete Code Examples | Imports, setup, call, and expected output included |
| 5 | Explicit Over Implicit | All defaults, constraints, and requirements stated |
| 6 | First-Class Error Docs | Error codes with causes, diagnosis steps, and fixes |
| 7 | Consistent Terminology | One term per concept across all pages |
| 8 | Frontmatter Metadata | YAML frontmatter on every page: title, description, version, tags |
| 9 | Prerequisites Up Front | Requirements listed at the top as a checklist |
| 10 | Expected Outputs | Success responses, status codes, and expected behavior shown |
| 11 | Cross-References with Context | Descriptive link text, never "click here" |
| 12 | Content Type Separation | Conceptual, how-to, and reference content clearly separated |
| 13 | Version Clarity | API/SDK version stated, deprecated content marked |
| 14 | Decision Documentation | "When to use X vs Y" sections for comparison questions |
| 15 | Safety Boundaries | Destructive actions, rate limits, billing implications documented |
| 16 | No Anti-Patterns | No marketing language, no "contact support" as documentation |
| 17 | Retrieval-Chunk Optimized | Good heading density, reasonable section size for RAG |
| 18 | Intent Before Mechanics | WHY before HOW — context before code |
| 19 | State Transitions | Systems documented as state machines where applicable |
| 20 | Callouts & Admonitions | Standard callout syntax for warnings, tips, important notes |

Rules are grouped into 5 scoring components:

| Component | Weight | Rules |
|-----------|--------|-------|
| Answer Accuracy | 30% | #1, #5, #7, #12, #13, #18 |
| Context Retrieval | 25% | #2, #8, #11, #17 |
| Citation & Trust | 20% | #9, #10, #14, #19 |
| Code Quality | 15% | #4, #6 |
| Doc Structure | 10% | #3, #15, #16, #20 |

## Architecture

```
agentreadiness/
├── apps/
│   ├── web/                    # React + TypeScript + Vite frontend
│   │   ├── src/
│   │   │   ├── components/     # UI components (shadcn/ui)
│   │   │   ├── sections/       # Page sections
│   │   │   │   ├── LandingPage.tsx        # Hero + 20 rules + assessment form
│   │   │   │   └── AssessmentResults.tsx   # Rule-by-rule results + paywall + download
│   │   │   ├── lib/            # API client + utilities
│   │   │   └── store/          # Zustand state management
│   │   └── package.json
│   └── api/                    # FastAPI backend
│       ├── routers/
│       │   ├── assessments.py  # POST /api/assessments/analyze (20-rule evaluation)
│       │   └── optimizer.py    # POST /api/optimizer/start (rewrite + ZIP)
│       ├── services/
│       │   ├── evaluator/
│       │   │   ├── rule_analyzer.py    # 20-rule evaluation engine
│       │   │   └── scorer.py           # Component scoring + grading
│       │   ├── optimizer/
│       │   │   └── document_optimizer.py  # GPT-4 page rewriting + ZIP packaging
│       │   └── crawler/
│       │       └── crawler.py          # Documentation site crawler
│       ├── pricing.py          # Dynamic pricing (page count → price)
│       ├── models.py           # SQLAlchemy ORM models
│       ├── config.py           # Pydantic settings
│       └── main.py             # FastAPI app entry point
├── docker-compose.yml
├── render.yaml                 # Render deployment config
├── llms.txt                    # Agent entry point for this repository
└── README.md
```

## Prerequisites

Before starting, ensure you have:

- [ ] Docker and Docker Compose installed
- [ ] Node.js 20+ installed
- [ ] Python 3.11+ installed
- [ ] An OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- [ ] A Stripe account ([create one here](https://stripe.com)) — for accepting payments

## Set Up Local Development

### Step 1: Clone the repository

```bash
git clone https://github.com/carlos-ferrer-fernandez/agentreadiness.git
cd agentreadiness
```

### Step 2: Set environment variables

```bash
cp .env.example .env
```

Then edit `.env` with your values:

```env
# Required
OPENAI_API_KEY=sk-your-openai-key
STRIPE_SECRET_KEY=sk_test_your-stripe-secret
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Optional (defaults work for local dev)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agentreadiness
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me-in-production
```

> **ℹ️ Info:** No Stripe products or prices need to be created. Pricing is dynamic — the app uses Stripe's `price_data` to set the amount at checkout time based on documentation size.

### Step 3: Start with Docker Compose

```bash
docker-compose up -d
```

Expected output:
```
✔ Container agentreadiness-db-1     Started
✔ Container agentreadiness-redis-1  Started
✔ Container agentreadiness-api-1    Started
✔ Container agentreadiness-web-1    Started
```

### Step 4: Verify everything is running

| Service | URL | Expected Response |
|---------|-----|-------------------|
| Frontend | http://localhost:3000 | Landing page with assessment form |
| API | http://localhost:8000 | `{"status": "healthy"}` |
| API Docs | http://localhost:8000/docs | Swagger UI |

### Alternative: Run services individually (without Docker)

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
# Expected: Vite dev server at http://localhost:5173
```

**Backend:**
```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# Expected: FastAPI server at http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/assessments/analyze` | Evaluate docs URL against 20 rules. Returns score, grade, rule results |
| `POST` | `/api/optimizer/pricing` | Get price estimate based on documentation size |
| `POST` | `/api/optimizer/start` | Start optimization job (rewrites all pages) |
| `GET` | `/api/optimizer/status/{job_id}` | Poll optimization progress |
| `GET` | `/api/optimizer/download/{job_id}` | Download optimized docs as ZIP |
| `POST` | `/api/payments/create-checkout` | Create Stripe checkout session |
| `POST` | `/api/payments/webhook` | Stripe webhook handler |
| `GET` | `/api/payments/verify` | Verify payment status |

## Grade Scale

| Score | Grade | What It Means |
|-------|-------|--------------|
| 97-100 | A+ | Exceptional — best-in-class agent experience |
| 93-96 | A | Excellent — agents recommend you confidently |
| 90-92 | A- | Very good — minor optimization opportunities |
| 87-89 | B+ | Good — some gaps in agent-readiness |
| 83-86 | B | Above average — meaningful improvement potential |
| 80-82 | B- | Average — significant optimization needed |
| 77-79 | C+ | Below average — agents struggle with your docs |
| 73-76 | C | Concerning — likely losing agent recommendations |
| 70-72 | C- | Poor — urgent improvement required |
| 60-69 | D | Critical — effectively invisible to agents |
| < 60 | F | Failing — complete restructuring needed |

## Deploy to Production

AgentReadiness deploys to Render via GitHub push. See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions.

**Live URL:** https://agentreadiness-web.onrender.com/

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, code style, and testing guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.
