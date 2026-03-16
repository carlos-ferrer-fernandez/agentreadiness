# Changelog

All notable changes to the AgentReadiness platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial MVP release with core functionality
- Public score checker on landing page
- Dashboard for managing documentation sites
- Friendliness Score calculation (0-100, A+ to F)
- Component breakdown visualization
- Query results table with filtering
- Recommendations engine with impact/effort scoring
- Score trend charts
- Toast notifications
- Error boundaries for better UX
- Loading states and skeletons

### Technical
- React + TypeScript + Vite frontend
- FastAPI backend with async support
- Documentation crawler with sitemap support
- Friendliness Scorer with 5 weighted components
- Zustand for state management
- Tailwind CSS for styling
- Docker Compose for local development

## [0.1.0] - 2025-03-03

### Added
- Initial release
- Core platform architecture
- Landing page with demo score checker
- Dashboard with site management
- Site detail page with tabs
- Analysis results page
- ScoreCard and ScoreTrend components
- API client with axios
- Store with Zustand
- Toast notifications
- Error boundary

[Unreleased]: https://github.com/your-org/agentreadiness/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/agentreadiness/releases/tag/v0.1.0
