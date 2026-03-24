# GrounDocs — Claude Code Instructions

## Project Overview
GrounDocs is a B2B SaaS tool that scores developer documentation against 20 AI-readiness rules and delivers optimized files as a one-time download. Built with React/Vite/TypeScript (frontend) and Python/FastAPI (backend).

## Repository Structure
```
apps/web/    — React/Vite/TypeScript frontend (landing page + assessment SPA)
apps/api/    — Python/FastAPI backend
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

All font choices, colors, spacing, border-radius, and aesthetic direction are defined there. Do not deviate without explicit approval.

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
- `apps/web/src/sections/LandingPage.tsx` — main marketing page + assessment form
- `apps/web/src/sections/AssessmentResults.tsx` — score results page
- `apps/web/src/lib/api.ts` — API client (Axios, 120s timeout)
- `apps/web/index.html` — OG/Twitter meta tags
- `apps/api/routers/assessments.py` — assessment API endpoint

## Known Architecture Notes
- Assessment scan has a 45-second client-side AbortController timeout
- HTTP 400 from scan API = crawlable URL failure (show specific message)
- Email validation mirrors server-side: requires `@` and `.`
- Interval/timeout cleanup is in a `finally` block — don't regress this
