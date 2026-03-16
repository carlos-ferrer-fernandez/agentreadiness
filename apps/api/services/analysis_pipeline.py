"""
Analysis Pipeline

Orchestrates the full analysis: crawl -> evaluate -> score -> recommend.
Runs as a background task and updates the Analysis record in the database.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import Analysis, AnalysisStatus, Site, SiteStatus, Recommendation
from services.crawler.crawler import DocumentationCrawler
from services.evaluator.scorer import FriendlinessScorer, QueryResult
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_analysis_pipeline(analysis_id: str, site_url: str) -> None:
    """
    Full analysis pipeline executed as a background task.

    Steps:
    1. Crawl the documentation site
    2. Generate synthetic queries against the content
    3. Score the documentation using the FriendlinessScorer
    4. Generate recommendations
    5. Persist results to the database
    """
    async with async_session() as db:
        try:
            analysis = await _get_analysis(db, analysis_id)
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return

            # Mark as running
            analysis.status = AnalysisStatus.RUNNING.value
            analysis.started_at = datetime.now(timezone.utc)
            analysis.current_stage = "Discovering pages"
            analysis.progress = 5
            await db.commit()

            # --- Step 1: Crawl ---
            analysis.current_stage = "Crawling documentation"
            analysis.progress = 10
            await db.commit()

            async with DocumentationCrawler(
                start_url=site_url,
                max_pages=settings.max_crawl_pages,
                delay=settings.crawl_delay_seconds,
            ) as crawler:
                pages = await crawler.crawl()

            analysis.page_count = len(pages)
            analysis.processed_pages = len(pages)
            analysis.progress = 40
            analysis.current_stage = "Analyzing structure"
            await db.commit()

            # Update site page count
            site = await db.execute(select(Site).where(Site.id == analysis.site_id))
            site_obj = site.scalar_one_or_none()
            if site_obj:
                site_obj.page_count = len(pages)
                site_obj.last_crawled_at = datetime.now(timezone.utc)
                site_obj.status = SiteStatus.READY.value

            # --- Step 2: Generate synthetic query results ---
            analysis.current_stage = "Simulating queries"
            analysis.progress = 60
            await db.commit()

            query_results = _generate_query_results(pages)

            # --- Step 3: Score ---
            analysis.current_stage = "Calculating score"
            analysis.progress = 80
            await db.commit()

            scorer = FriendlinessScorer()
            score = scorer.calculate_score(query_results)

            analysis.overall_score = score.overall
            analysis.grade = score.grade
            analysis.components = score.components
            analysis.query_count = score.query_count
            analysis.pass_rate = score.pass_rate
            analysis.avg_latency_ms = score.avg_latency_ms

            # --- Step 4: Generate recommendations ---
            analysis.current_stage = "Generating recommendations"
            analysis.progress = 90
            await db.commit()

            recommendations = _generate_recommendations(pages, score, analysis.site_id, analysis.id)
            for rec in recommendations:
                db.add(rec)

            # --- Done ---
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.progress = 100
            analysis.current_stage = None
            analysis.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                f"Analysis {analysis_id} completed: score={score.overall} grade={score.grade}"
            )

        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {e}", exc_info=True)
            try:
                analysis = await _get_analysis(db, analysis_id)
                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                logger.error(f"Failed to mark analysis {analysis_id} as failed", exc_info=True)


async def _get_analysis(db: AsyncSession, analysis_id: str) -> Analysis | None:
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    return result.scalar_one_or_none()


def _generate_query_results(pages: list) -> list[QueryResult]:
    """
    Generate synthetic query results from crawled pages.

    In a production system, this would use an LLM to generate questions
    and test them against a RAG pipeline. For now, we derive scores
    from content quality signals.
    """
    results = []
    for page in pages:
        content_length = len(page.content) if page.content else 0
        has_code = bool(page.code_blocks)
        has_headings = bool(page.heading_hierarchy and len(page.heading_hierarchy) >= 2)

        # Heuristic scoring based on content quality
        accuracy = min(1.0, 0.5 + (content_length / 5000) * 0.3 + (0.2 if has_code else 0))
        precision = min(1.0, 0.4 + (0.3 if has_headings else 0) + (content_length / 8000) * 0.3)
        latency = 800 + max(0, content_length // 10)  # Larger pages = slower
        citation = 0.7 + (0.2 if has_headings else 0) + (0.1 if page.links else 0)
        code_valid = has_code  # Assume code blocks are valid if present

        results.append(QueryResult(
            query=f"Query about: {page.title or page.url}",
            passed=accuracy > 0.6,
            confidence=accuracy,
            accuracy_score=accuracy,
            retrieval_precision=precision,
            latency_ms=min(latency, 5000),
            citation_accuracy=min(citation, 1.0),
            code_valid=code_valid,
        ))

    return results


def _generate_recommendations(
    pages: list, score, site_id: str, analysis_id: str
) -> list[Recommendation]:
    """Generate actionable recommendations based on analysis results."""
    recommendations = []
    priority = 0

    components = score.components

    # Low accuracy
    if components.get("accuracy", 100) < 80:
        priority += 1
        recommendations.append(Recommendation(
            site_id=site_id,
            analysis_id=analysis_id,
            priority=priority,
            impact="high",
            effort="medium",
            category="content_gap",
            title="Improve content depth and accuracy",
            description=(
                "Several pages lack sufficient detail for AI agents to generate accurate answers. "
                "Add more comprehensive explanations, especially for core concepts and API parameters."
            ),
            affected_pages=[{"url": p.url, "title": p.title} for p in pages[:3] if len(p.content or "") < 500],
            estimated_score_improvement=5.0,
        ))

    # Low code executability
    if components.get("code_executability", 100) < 80:
        priority += 1
        pages_without_code = [p for p in pages if not p.code_blocks]
        recommendations.append(Recommendation(
            site_id=site_id,
            analysis_id=analysis_id,
            priority=priority,
            impact="high",
            effort="low",
            category="code_quality",
            title="Add runnable code examples",
            description=(
                "Many pages are missing code examples. AI agents perform significantly better "
                "when documentation includes complete, runnable code snippets."
            ),
            affected_pages=[{"url": p.url, "title": p.title} for p in pages_without_code[:5]],
            before_example="```\n# No code example provided\nSee the API reference for details.\n```",
            after_example=(
                "```python\nimport requests\n\nresponse = requests.post(\n"
                "    'https://api.example.com/v1/resource',\n"
                "    headers={'Authorization': 'Bearer YOUR_API_KEY'},\n"
                "    json={'key': 'value'}\n)\nprint(response.json())\n```"
            ),
            estimated_score_improvement=4.0,
        ))

    # Low context utilization (poor structure)
    if components.get("context_utilization", 100) < 80:
        priority += 1
        recommendations.append(Recommendation(
            site_id=site_id,
            analysis_id=analysis_id,
            priority=priority,
            impact="medium",
            effort="medium",
            category="structure",
            title="Improve documentation hierarchy and cross-linking",
            description=(
                "The documentation structure makes it difficult for AI agents to locate relevant context. "
                "Add clear heading hierarchies and cross-references between related topics."
            ),
            affected_pages=[],
            estimated_score_improvement=3.0,
        ))

    # Low citation quality
    if components.get("citation_quality", 100) < 80:
        priority += 1
        recommendations.append(Recommendation(
            site_id=site_id,
            analysis_id=analysis_id,
            priority=priority,
            impact="medium",
            effort="low",
            category="metadata",
            title="Add descriptive page titles and meta descriptions",
            description=(
                "Pages lack clear titles and descriptions, making it harder for agents to cite sources accurately. "
                "Add unique, descriptive titles and meta descriptions to every page."
            ),
            affected_pages=[],
            estimated_score_improvement=2.0,
        ))

    # Always add at least one recommendation
    if not recommendations:
        priority += 1
        recommendations.append(Recommendation(
            site_id=site_id,
            analysis_id=analysis_id,
            priority=priority,
            impact="low",
            effort="low",
            category="optimization",
            title="Fine-tune for perfect agent experience",
            description=(
                "Your documentation is already well-optimized. Consider adding more edge-case examples "
                "and troubleshooting sections to reach a perfect score."
            ),
            affected_pages=[],
            estimated_score_improvement=1.0,
        ))

    return recommendations
