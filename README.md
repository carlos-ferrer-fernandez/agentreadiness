# AgentReadiness Platform

A platform for measuring and optimizing documentation for AI agent consumption.

## Business Model: Freemium

### Free Tier
- **Friendliness Score** (0-100) with letter grade (A+ to F)
- Component breakdown across 5 dimensions
- Top 3 issues identified
- Industry benchmark comparison

### Paid Tiers

#### Starter Plan - $49 (One-time)
- 10+ detailed recommendations
- Step-by-step improvement guide
- Code examples & templates
- PDF report download
- Email support

#### Growth Plan - $149 (One-time)
- Everything in Starter
- Unlimited recommendations
- Competitor deep-dive analysis
- Custom improvement roadmap
- 1-on-1 consultation (30 min)
- Slack support (1 week)

## User Flow

1. **Landing Page** → User enters docs URL
2. **Free Assessment** → 30-60 second analysis
3. **Results Page** → Score + basic insights (FREE)
4. **Paywall** → Unlock detailed action plan
5. **Payment** → Stripe checkout
6. **Full Access** → Complete recommendations

## Features

### Core Features

- **Friendliness Score**: Composite score (0-100) with letter grade (A+ to F)
- **Agent Simulation**: Test with realistic developer personas
- **Component Breakdown**: Detailed scoring across 5 dimensions:
  - Answer Accuracy (30%)
  - Context Utilization (25%)
  - Response Latency (20%)
  - Citation Quality (15%)
  - Code Executability (10%)
- **Recommendations**: Prioritized by impact × effort with before/after examples
- **Competitive Benchmarking**: Compare against industry leaders

### Analysis Pipeline

1. **Crawl**: Discover and extract content from documentation
2. **Chunk & Embed**: Create searchable vector representations
3. **Query Generation**: Generate realistic developer questions
4. **RAG Simulation**: Simulate agent retrieval and response generation
5. **Evaluation**: Score responses across multiple dimensions
6. **Recommendations**: Generate actionable improvement suggestions

## Architecture

```
agentreadiness/
├── apps/
│   ├── web/              # React + TypeScript + Vite frontend
│   │   ├── src/
│   │   │   ├── components/   # UI components
│   │   │   ├── sections/     # Page sections
│   │   │   │   ├── LandingPage.tsx      # Hero + assessment form
│   │   │   │   ├── AssessmentResults.tsx # Results + paywall
│   │   │   │   ├── Dashboard.tsx         # User dashboard
│   │   │   │   └── ...
│   │   │   ├── hooks/        # Custom React hooks
│   │   │   ├── lib/          # Utilities + API client
│   │   │   ├── store/        # Zustand state management
│   │   │   └── types/        # TypeScript types
│   │   └── package.json
│   └── api/              # FastAPI backend
│       ├── routers/          # API endpoints
│       ├── services/         # Business logic
│       └── main.py
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- OpenAI API key
- Stripe account (for payments)

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/your-org/agentreadiness.git
cd agentreadiness
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your values
```

3. Start services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Frontend

```bash
cd apps/web
npm install
npm run dev
```

#### Backend

```bash
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

```env
# Required
OPENAI_API_KEY=sk-your-openai-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional
DATABASE_URL=postgresql://postgres:postgres@db:5432/agentreadiness
REDIS_URL=redis://redis:6379/0
JWT_SECRET=your-secure-jwt-secret
VITE_API_URL=http://localhost:8000
```

## Friendliness Score

### Grade Scale

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 97-100 | A+ | Exceptional: best-in-class agent experience |
| 93-96 | A | Excellent: strong competitive position |
| 90-92 | A- | Very good: minor optimization opportunities |
| 87-89 | B+ | Good: some gaps relative to leaders |
| 83-86 | B | Above average: meaningful improvement potential |
| 80-82 | B- | Average: significant optimization needed |
| 77-79 | C+ | Below average: competitive disadvantage risk |
| 73-76 | C | Concerning: likely losing agent recommendations |
| 70-72 | C- | Poor: urgent improvement required |
| 60-69 | D | Critical: effectively invisible to agents |
| < 60 | F | Failing: complete restructuring needed |

### Component Weights

- **Answer Accuracy (30%)**: Correctness of generated answers
- **Context Utilization (25%)**: Efficiency of information retrieval
- **Response Latency (20%)**: Speed of query processing
- **Citation Quality (15%)**: Accuracy of source attribution
- **Code Executability (10%)**: Validity of code examples

## API Endpoints

### Sites

- `POST /api/sites` - Register a new documentation site
- `GET /api/sites` - List all sites
- `GET /api/sites/{id}` - Get site details
- `POST /api/sites/{id}/analyze` - Trigger analysis

### Analyses

- `GET /api/analyses` - List analyses
- `GET /api/analyses/{id}` - Get analysis details
- `GET /api/analyses/{id}/score` - Get friendliness score

### Payments (Stripe)

- `POST /api/payments/create-checkout` - Create Stripe checkout session
- `POST /api/payments/webhook` - Stripe webhook handler
- `GET /api/payments/verify` - Verify payment status

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

### Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: https://docs.agentreadiness.dev
- Discord: https://discord.gg/agentreadiness
- Email: support@agentreadiness.dev
