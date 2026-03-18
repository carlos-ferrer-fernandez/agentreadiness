---
title: "AgentReadiness Changelog"
description: "All notable changes to the AgentReadiness platform"
version: "0.3.0"
last_updated: "2026-03-18"
tags: ["changelog", "releases", "versioning"]
---

# Changelog

All notable changes to AgentReadiness are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-03-18

### Added
- **20 Agent-Readiness Rules**: Core evaluation engine derived from benchmarking 8 major AI agents (Claude, GPT, Gemini, Grok, Kimi, Deepseek, Manus, KimiClaw)
- **Rule-based assessment**: `AgentReadinessAnalyzer` evaluates documentation against all 20 rules with per-rule scores, findings, and page counts
- **Documentation optimizer**: GPT-4 rewrites every page applying all 20 rules — output is production-ready Markdown
- **llms.txt generation**: Auto-generated agent entry point following the emerging llms.txt standard
- **ZIP deliverable**: Optimized docs packaged as downloadable ZIP (docs/, llms.txt, README.md, DEPLOY.md, _metadata.json)
- **Dynamic pricing**: Price calculated from documentation size. Starting at €49, scaling with page count
- **20-rule showcase on landing page**: Full visual grid of all rules with icons and descriptions
- **Diana Hu (YC GP) video embed**: Real social proof from Y Combinator AI Startup School 2025
- **Live progress animation**: 11 granular stages + rotating status messages during assessment scan
- **Rule-by-rule results view**: Expandable rule checklist showing score, status, finding, and pages passing per rule

### Changed
- **Renamed "Friendliness Score" to "Agent-Readiness Score"** — reflects the 20-rule methodology
- **Replaced heuristic scoring with rule-based evaluation** — each rule checks specific patterns across crawled pages
- **Product pivot**: Output is now optimized documentation files (not reports or recommendations)
- **Pricing**: Dynamic pricing based on documentation size replaces flat tiers
- **Component weights rebalanced**: Citation Quality 15% → 20%, Response Latency 20% → 10%
- **Landing page humanized**: Removed fake stats, removed builder jargon, added methodology showcase
- **Hero copy**: Customer-facing language focused on agent discovery, not services market thesis

### Removed
- Fake social proof (company logos)
- Static urgency stats bar (6x, 68%, 2025)
- `OptimizationConfig` — no user choices needed, all 20 rules always applied
- Margin/cost details from API price breakdown response

## [0.2.0] - 2025-03-10

### Added
- Dynamic pricing engine (3x API cost, min €49, max €499)
- Stripe integration with `price_data` for dynamic checkout amounts
- Documentation crawler with sitemap support
- Assessment results page with component breakdown
- Paywall modal with promo code support
- Optimization status polling with progress bar

### Changed
- Moved from flat pricing tiers to dynamic pricing based on page count
- Replaced static Stripe Price objects with dynamic `price_data`

## [0.1.0] - 2025-03-03

### Added
- Initial release
- React + TypeScript + Vite frontend
- FastAPI backend with async support
- Landing page with assessment form
- Dashboard with site management
- ScoreCard and ScoreTrend components
- Zustand state management
- Tailwind CSS styling
- Docker Compose for local development
- CI pipeline (lint, type-check, test, build)

[0.3.0]: https://github.com/carlos-ferrer-fernandez/agentreadiness/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/carlos-ferrer-fernandez/agentreadiness/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/carlos-ferrer-fernandez/agentreadiness/releases/tag/v0.1.0
