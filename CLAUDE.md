# GrounDocs — Claude Code Instructions

## Project Overview
GrounDocs is a B2B SaaS that generates dedicated /agents pages for software products. Customers submit their product name + documentation URL + email, and GrounDocs crawls the docs, uses OpenAI to generate structured content, and renders a hosted agent-ready page at `/agent-pages/<company-slug>`. Two tiers: free draft preview and paid ($99) full page.

Built with React/Vite/TypeScript (frontend) and Python/FastAPI (backend).

## Repository Structure
```
apps/web/    — React/Vite/TypeScript frontend (landing page + agent page viewer)
apps/api/    — Python/FastAPI backend (generation pipeline, Stripe, API)
render.yaml  — Render.com deployment config
```

## Development
```bash
# Frontend
cd apps/web && npm run dev      # dev server
cd apps/web && npm run build    # production build

# Backend
cd apps/api && python main.py   # dev server (port 8000)
```

## Design System
Always read `apps/web/DESIGN.md` before making any visual or UI decisions.

**Key rules:**
- Display/hero text: Instrument Serif
- Body/UI text: Plus Jakarta Sans
- All data, scores, rule names, code: Berkeley Mono (dev: JetBrains Mono)
- Background: `#FAFAF8` (warm off-white — never pure white)
- Brand accent: `#1A7A4C` (deep forest green)
- Border radius is hierarchical — see DESIGN.md for the scale
- No purple gradients, no generic icon grids, no blob decorations

In QA mode, flag any code that doesn't match DESIGN.md.

## Key Files
- `apps/web/src/sections/LandingPage.tsx` — main marketing page + submission form
- `apps/web/src/sections/AgentPageView.tsx` — agent page viewer (iframe + payment flow)
- `apps/web/src/lib/api.ts` — API client (Axios, 120s timeout)
- `apps/api/routers/agent_pages.py` — agent page API endpoints
- `apps/api/services/agent_page_generator.py` — core pipeline: crawl → OpenAI → HTML
- `apps/api/services/seed_examples.py` — pre-built example pages (Stripe, Vercel, Notion, Slack)
- `apps/api/models.py` — AgentPage model (+ legacy Assessment model)
- `apps/web/index.html` — OG/Twitter meta tags

## Architecture
- Generation pipeline: crawl docs (httpx+BS4) → OpenAI structured JSON → render HTML template
- Draft: 5-page crawl, partial sections, free
- Full: 20-page crawl, all sections, $99 via Stripe
- Agent pages served at `/agent-pages/<slug>` as self-contained HTML
- Seed examples auto-created on startup for Stripe, Vercel, Notion, Slack
- Promo code `FREE100` bypasses payment for testing

## Known Architecture Notes
- Email validation mirrors server-side: requires `@` and `.`
- Interval/timeout cleanup is in a `finally` block — don't regress this
- Agent page HTML is stored in DB (survives Render redeploys)
- Legacy assessment routes still exist but are not linked from homepage
