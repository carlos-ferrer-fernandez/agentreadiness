"""
Documentation Optimizer Service

Optimizes documentation for AI agent consumption based on a multi-agent
benchmark (Claude, GPT, Kimi, Grok, Deepseek, Manus, Gemini, KimiClaw).

This encodes the concrete, consensus best practices that ALL major AI agents
agree make documentation effective for machine consumption.
"""

import os
import re
import json
import zipfile
import tempfile
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
import logging

import httpx
from bs4 import BeautifulSoup
import openai
import markdown

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger(__name__)

# API key is passed to AsyncOpenAI constructor (not the deprecated module-level assignment)


# =============================================================================
# THE AGENT-READINESS DOCTRINE
# Distilled from multi-agent benchmark (Claude, GPT, Kimi, Grok,
# Deepseek, Manus, Gemini, KimiClaw)
#
# Documentation is agent-ready when it is:
#   Findable   — relevant content is easy to retrieve
#   Atomic     — sections make sense in isolation
#   Explicit   — no crucial fact is implied
#   Executable — examples actually work
#   Groundable — claims can be cited to source
#   Versioned  — current and historical states are clear
#   Recoverable — failures and fixes are documented
#   Structured  — humans and machines can parse it reliably
# =============================================================================

OPTIMIZATION_RULES = """
## AGENT-READINESS OPTIMIZATION RULES
## Based on consensus from 8 major AI agents (Claude, GPT, Kimi, Grok, Deepseek, Manus, Gemini, KimiClaw)

You are rewriting documentation to be optimized for AI agent consumption.
Apply ALL of the following rules. These are not suggestions — they are
requirements derived from how agents actually process documentation.

### RULE 1: SELF-CONTAINED SECTIONS (Highest priority — unanimous across all agents)
- Every section MUST make sense if read in complete isolation
- NEVER use "as mentioned above", "see previous section", "as described earlier"
- Re-state context at the start of each section. Redundancy is a FEATURE, not a bug
- Each important workflow should have ONE canonical section that stands on its own
- Think: "If a RAG system retrieves ONLY this section, can it answer the question?"

### RULE 2: ACTION-ORIENTED, TASK-SHAPED HEADINGS
- Headings should resemble actual user/agent intents and questions
- GOOD: "Authenticate with an API key", "Send your first transactional email"
- BAD: "Authentication", "Emails", "Getting Started", "Advanced Topics"
- Headings are retrieval anchors — agents use them to decide relevance
- Use strict H1 → H2 → H3 hierarchy. Never skip levels. Never use headings for styling

### RULE 3: STRUCTURED PARAMETER TABLES (Not prose)
- ALWAYS use tables for parameters, options, return values, config settings
- Table format: | Parameter | Type | Required | Default | Description |
- NEVER describe parameters in running prose paragraphs
- Include constraints, valid ranges, enum values in the Description column

### RULE 4: COMPLETE, RUNNABLE CODE EXAMPLES
- Every code example MUST include: imports, setup/init, the actual call, expected output
- Code blocks MUST have explicit language tags (```python, ```javascript, etc.)
- NEVER use "..." or "// ..." to skip code. Show the FULL working example
- Add inline comments explaining WHY (not what) for key lines
- If the product has multiple SDKs, provide examples in each language
- Add a "Minimal Reproducible Example" that can be copy-pasted and run immediately

### RULE 5: EXPLICIT OVER IMPLICIT (Agents have zero intuition)
- State ALL defaults explicitly: "Default timeout is 30 seconds"
- State ALL constraints: "Maximum 100 items per request"
- State ALL requirements: "The region parameter is required"
- NEVER use: "typically...", "usually...", "you may want to...", "simply..."
- Replace EVERY vague pronoun ("it", "this", "that") with the explicit subject
- If something matters operationally, say it in plain text, not in a footnote

### RULE 6: FIRST-CLASS ERROR DOCUMENTATION
- Document EVERY error code with: exact error message string, likely causes,
  diagnosis steps, fix steps, and whether retrying is safe
- Create dedicated troubleshooting sections, not afterthoughts
- Include the exact literal error strings users will see (for retrieval matching)
- Structure as: Error Code → When it happens → How to fix it
- Document: auth failures, rate limits, invalid payloads, permission issues,
  webhook failures, migration breakages

### RULE 7: CONSISTENT TERMINOLOGY
- Use ONE term per concept throughout the ENTIRE documentation
- NEVER alternate between synonyms (e.g., "user"/"account"/"customer" for same thing)
- If original docs have inconsistent terms, pick the most precise one and use it everywhere
- Create a terminology note at the top if the original used multiple terms

### RULE 8: FRONTMATTER METADATA ON EVERY PAGE
- Add YAML frontmatter to every document:
  ---
  title: "Action-oriented title"
  description: "One-sentence summary of what this page helps you do"
  version: "API/SDK version this applies to"
  last_updated: "YYYY-MM-DD"
  tags: ["relevant", "search", "terms"]
  prerequisites: ["What the reader needs before starting"]
  ---

### RULE 9: PREREQUISITES UP FRONT
- State ALL prerequisites at the very start of each page/section:
  account requirements, permissions/scopes, API keys needed,
  SDK version, runtime requirements, feature flags, plan/tier restrictions
- Format as a clear checklist, not buried in prose

### RULE 10: EXPECTED OUTPUTS (Not just inputs)
- For EVERY API call or code example, show what SUCCESS looks like:
  expected response body, expected status code, expected logs, expected behavior
- This enables agents to verify their understanding and help users confirm correct operation

### RULE 11: CROSS-REFERENCES WITH FULL CONTEXT
- NEVER write: "See the Authentication guide" or "Click here"
- ALWAYS write: "For authentication details, see [Authentication Guide](/auth)
  which covers API keys, OAuth2, and JWT tokens"
- Every link must have enough context that the reader understands what they'll find

### RULE 12: SEPARATE CONCEPTUAL / HOW-TO / REFERENCE CONTENT
- Conceptual: What it is, why it exists, when to use it
- How-to: Step-by-step task completion with full examples
- Reference: Exact schema, parameters, limits, return types, enum values
- Never mix these in a confusing way. Each section should be clearly one type

### RULE 13: VERSION CLARITY
- State the API/SDK version prominently at the top of every page
- If content applies to specific versions, say so explicitly
- Mark deprecated content with clear warnings and migration paths
- Never let old examples exist without version context

### RULE 14: DECISION DOCUMENTATION
- Include "When should I use X vs Y?" sections where relevant
- Structure as: use X when..., use Y when..., trade-offs, limits, migration path
- Agents frequently need to answer comparative questions

### RULE 15: SAFETY BOUNDARIES
- Clearly document: destructive actions, irreversible operations, billing implications,
  side effects, rate limits, quotas
- Use callout/admonition syntax: > **⚠️ Warning:** This action is irreversible.
- If an action can send emails, delete data, trigger workflows, or incur cost, say it plainly

### RULE 16: STRIP ANTI-PATTERNS
- REMOVE all marketing language from technical docs ("seamlessly", "world-class", "unlock")
- REMOVE "Contact support" as documentation — replace with actual self-service resolution
- REMOVE content that depends on JavaScript rendering, tabs, accordions, or UI widgets
- REPLACE "see section above" with actual re-statement of the information
- REPLACE vague link text ("click here", "learn more") with descriptive text
- REMOVE image-only or UI-only content — ensure all critical info exists as text

### RULE 17: OPTIMIZE FOR RETRIEVAL CHUNKS
- Each section should have: clear heading, clear scope, enough context to stand alone
- Keep sections focused — not too long, not too dependent on previous paragraphs
- Include concrete nouns and exact identifiers (not just pronouns)
- Useful rule: Each chunk should still make sense if read completely alone

### RULE 18: STATE INTENT BEFORE MECHANICS
- ALWAYS explain WHY before HOW
- BAD: "Call POST /webhooks to create a webhook"
- GOOD: "To receive real-time notifications when events occur, create a webhook
  by calling POST /webhooks"

### RULE 19: DOCUMENT STATE TRANSITIONS & LIFECYCLE
- Where applicable, document systems as state machines:
  draft → scheduled → sent → delivered → bounced
- Include: state meanings, transitions, triggers, terminal states,
  retry semantics, webhook/event emissions

### RULE 20: CALLOUTS & ADMONITIONS
- Use standard callout syntax for warnings, tips, important notes
- These become natural prioritization signals for agents
- Format: > **ℹ️ Info:** / > **⚠️ Warning:** / > **❌ Error:** / > **💡 Tip:**

### OUTPUT QUALITY STANDARDS (Inspired by Mintlify-quality documentation)
- Write clear, scannable prose. Short paragraphs (2-3 sentences max)
- Use bullet lists for anything with 3+ items
- Lead each section with a one-sentence summary of what it covers
- For multi-step procedures, use numbered lists with clear step titles
- For code examples in multiple languages, show each language variant
- For configuration options, always include: name, type, default, description
- Every page should feel complete and professional, like premium docs
- Callout hierarchy: Tip (helpful), Note/Info (important), Warning (caution), Danger (destructive)
"""


@dataclass
class DocPage:
    """Represents a crawled documentation page."""
    url: str
    title: str
    content: str
    code_blocks: List[Dict]
    headings: List[str]
    links: List[str]
    file_path: Optional[str] = None


@dataclass
class PageAnalysis:
    """Detailed analysis of a documentation page against agent-readiness rules."""
    has_code_examples: bool = False
    code_count: int = 0
    has_complete_examples: bool = False
    has_parameter_tables: bool = False
    has_frontmatter: bool = False
    has_error_docs: bool = False
    has_prerequisites: bool = False
    has_expected_output: bool = False
    has_version_info: bool = False
    word_count: int = 0
    heading_count: int = 0
    has_vague_references: bool = False
    has_marketing_language: bool = False
    has_implicit_pronouns: bool = False
    has_action_headings: bool = False
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class OptimizedDoc:
    """Represents an optimized document."""
    original_url: str
    title: str
    optimized_content: str
    improvements: List[str]
    file_name: str


class DocumentationOptimizer:
    """Optimizes documentation for AI agent consumption.

    Encodes the consensus best practices from 8 major AI agents into
    concrete optimization rules applied to every page.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._playwright = None
        self._browser = None
        self._needs_js_rendering = False  # Set to True after first JS-rendered page detected

    async def _notify_progress(self, callback, stage: str, progress: float):
        """Call progress callback, handling both sync and async callbacks."""
        if not callback:
            return
        import asyncio
        result = callback(stage, progress)
        if asyncio.iscoroutine(result):
            await result

    async def optimize_documentation(
        self,
        start_url: str,
        progress_callback=None
    ) -> Tuple[List[OptimizedDoc], Dict]:
        """
        Main entry point: crawl, analyze, and optimize documentation.

        Returns:
            Tuple of (optimized documents, metadata including llms.txt)
        """
        logger.info(f"Starting optimization of {start_url}")

        # Step 1: Crawl documentation
        await self._notify_progress(progress_callback, "crawling", 0.1)

        try:
            pages = await self._crawl_documentation(start_url)
        finally:
            # Always close the Playwright browser after crawling
            await self._close_browser()
        logger.info(f"Crawled {len(pages)} pages")

        if len(pages) == 0:
            raise ValueError(
                f"Crawling {start_url} produced 0 pages with usable content. "
                "The site may be JavaScript-rendered, behind authentication, "
                "or have no accessible documentation content. "
                "Please verify the URL points to a public documentation site."
            )

        # Step 2: Deep analysis of each page against agent-readiness rules
        await self._notify_progress(progress_callback, "analyzing", 0.3)

        analyzed_pages = []
        for i, page in enumerate(pages):
            analysis = self._analyze_page_deep(page)
            analyzed_pages.append((page, analysis))
            await self._notify_progress(
                progress_callback, "analyzing", 0.3 + (0.2 * (i + 1) / len(pages))
            )

        # Step 3: Build terminology map across all pages
        terminology_context = self._build_terminology_context(pages)

        # Step 4: Generate optimized content
        await self._notify_progress(progress_callback, "optimizing", 0.5)

        optimized_docs = []
        for i, (page, analysis) in enumerate(analyzed_pages):
            optimized = await self._optimize_page(page, analysis, terminology_context)
            optimized_docs.append(optimized)
            await self._notify_progress(
                progress_callback, "optimizing", 0.5 + (0.35 * (i + 1) / len(analyzed_pages))
            )

        # Step 5: Generate llms.txt
        await self._notify_progress(progress_callback, "generating_llms_txt", 0.9)

        llms_txt = self._generate_llms_txt(start_url, optimized_docs)

        # Step 6: Generate metadata
        await self._notify_progress(progress_callback, "finalizing", 0.95)

        metadata = self._generate_metadata(optimized_docs)

        await self._notify_progress(progress_callback, "complete", 1.0)

        # Attach llms.txt to metadata for packaging
        metadata['llms_txt'] = llms_txt

        return optimized_docs, metadata

    # =========================================================================
    # CRAWLING
    # =========================================================================

    async def _crawl_documentation(self, start_url: str) -> List[DocPage]:
        """Crawl documentation site and extract pages.

        Follows both absolute and relative links within the same domain.
        Normalizes URLs to avoid duplicates. Skips non-content pages
        (anchors, query params, auth pages, assets).
        """
        from urllib.parse import urljoin, urldefrag

        from config import get_settings
        settings = get_settings()

        pages = []
        visited = set()
        to_visit = [start_url]
        max_pages = settings.max_crawl_pages

        parsed_base = urlparse(start_url)
        base_domain = parsed_base.netloc
        # Keep the base path prefix for scoping (e.g., /docs/ stays within /docs/)
        base_path = parsed_base.path.rstrip('/')

        while to_visit and len(pages) < max_pages:
            url = to_visit.pop(0)

            # Normalize: remove fragment, trailing slash
            url = urldefrag(url)[0].rstrip('/')
            if not url:
                continue
            if url in visited:
                continue

            try:
                page = await self._fetch_page(url)
                visited.add(url)  # Always mark visited, even on failure

                if page:
                    # Only add pages with meaningful content (not just nav/landing)
                    if page.content and len(page.content.strip()) > 50:
                        pages.append(page)

                    # Discover new links (both absolute and relative)
                    for link in page.links:
                        normalized = urldefrag(link)[0].rstrip('/')
                        if normalized and normalized not in visited:
                            parsed_link = urlparse(normalized)
                            if parsed_link.netloc == base_domain:
                                # Stay within the docs scope
                                if not base_path or parsed_link.path.startswith(base_path):
                                    to_visit.append(normalized)

            except Exception as e:
                visited.add(url)  # Mark visited on error too
                logger.warning(f"Failed to fetch {url}: {e}")

        logger.info(f"Crawled {len(pages)} content pages from {len(visited)} URLs visited")
        return pages

    async def _fetch_page(self, url: str) -> Optional[DocPage]:
        """Fetch and parse a single page.

        First tries a fast httpx fetch. If the rendered content is too thin
        (< 100 chars — typical for JS-rendered SPAs), falls back to a
        headless Playwright browser that executes JavaScript before parsing.
        """
        from urllib.parse import urljoin

        try:
            # If we already know this site is JS-rendered, go straight to Playwright
            if self._needs_js_rendering and HAS_PLAYWRIGHT:
                return await self._fetch_page_with_playwright(url)

            # --- Fast path: plain HTTP ---
            response = await self.client.get(url, follow_redirects=True)
            if response.status_code != 200:
                return None

            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type and 'text/plain' not in content_type:
                return None

            page = self._parse_html_to_page(response.text, url)

            # --- Fallback: JS rendering via Playwright ---
            if page and len(page.content.strip()) < 100 and HAS_PLAYWRIGHT:
                logger.info(f"Thin content from {url} — retrying with Playwright (JS rendering)")
                rendered_page = await self._fetch_page_with_playwright(url)
                if rendered_page and len(rendered_page.content.strip()) > len(page.content.strip()):
                    # This site needs JS — skip httpx for future pages
                    self._needs_js_rendering = True
                    return rendered_page

            return page

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def _ensure_browser(self):
        """Lazily start a shared Playwright browser (one per optimization run)."""
        if self._browser is None and HAS_PLAYWRIGHT:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.info("Playwright browser launched for JS rendering")

    async def _close_browser(self):
        """Close the shared Playwright browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _fetch_page_with_playwright(self, url: str) -> Optional[DocPage]:
        """Fetch a page using the shared headless browser for JS rendering.

        Uses 'domcontentloaded' (not 'networkidle') because sites like Stripe
        have endless analytics/tracking requests that prevent networkidle from
        ever firing, causing 30s hangs per page.
        """
        try:
            await self._ensure_browser()
            if not self._browser:
                return None

            context = await self._browser.new_context(
                user_agent="AgentReadinessBot/1.0 (Documentation Analysis)"
            )
            page = await context.new_page()

            # Block analytics/tracking to speed up page loads
            await page.route("**/{analytics,tracking,gtag,gtm,segment,hotjar,intercom,mixpanel,sentry}**", lambda route: route.abort())
            await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf}", lambda route: route.abort())

            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            # Short wait for JS frameworks to render content after DOM is ready
            await page.wait_for_timeout(1500)

            html = await page.content()
            await context.close()

            return self._parse_html_to_page(html, url)

        except Exception as e:
            logger.warning(f"Playwright fetch failed for {url}: {e}")
            return None

    def _parse_html_to_page(self, html: str, url: str) -> DocPage:
        """Parse raw HTML string into a DocPage with content, headings, links."""
        from urllib.parse import urljoin

        soup = BeautifulSoup(html, 'html.parser')

        # Remove nav, footer, sidebar, cookie banners etc
        for tag in soup.find_all(['nav', 'footer', 'aside', 'header']):
            tag.decompose()
        for tag in soup.find_all(class_=re.compile(
            r'(nav|footer|sidebar|cookie|banner|menu|breadcrumb|toc)',
            re.IGNORECASE
        )):
            tag.decompose()

        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else "Untitled"

        main = (soup.find('main') or soup.find('article') or
                soup.find('div', class_='content') or
                soup.find('div', role='main') or
                soup.find('div', class_=re.compile(r'(docs|documentation|page-content|markdown)', re.IGNORECASE)))
        if not main:
            main = soup.find('body')

        content = main.get_text(separator='\n', strip=True) if main else ""

        code_blocks = []
        for pre in (main or soup).find_all('pre'):
            code = pre.find('code')
            if code:
                language = self._detect_language(code.get('class', []))
                code_blocks.append({
                    'language': language,
                    'code': code.get_text(strip=True)
                })

        headings = []
        for h in (main or soup).find_all(['h1', 'h2', 'h3', 'h4']):
            headings.append(h.get_text(strip=True))

        # Collect ALL links: resolve relative links to absolute
        links = []
        skip_patterns = re.compile(
            r'(\.png|\.jpg|\.gif|\.svg|\.css|\.js|\.woff|\.pdf|'
            r'mailto:|javascript:|#$|/login|/signup|/auth|/console|'
            r'/search\?|/changelog|/blog)',
            re.IGNORECASE
        )
        for a in soup.find_all('a', href=True):
            href = a['href']
            if skip_patterns.search(href):
                continue
            absolute = urljoin(url, href)
            if absolute.startswith('http'):
                links.append(absolute)

        return DocPage(
            url=url,
            title=title_text,
            content=content,
            code_blocks=code_blocks,
            headings=headings,
            links=links
        )

    # =========================================================================
    # DEEP ANALYSIS
    # =========================================================================

    def _analyze_page_deep(self, page: DocPage) -> PageAnalysis:
        """Analyze a page against ALL agent-readiness rules."""
        content_lower = page.content.lower()
        analysis = PageAnalysis()

        # Basic metrics
        analysis.word_count = len(page.content.split())
        analysis.heading_count = len(page.headings)
        analysis.has_code_examples = len(page.code_blocks) > 0
        analysis.code_count = len(page.code_blocks)

        # Rule 1: Self-contained sections
        vague_refs = [
            'as mentioned above', 'see previous section', 'as described earlier',
            'refer to the above', 'as noted above', 'see above',
            'as shown above', 'as discussed', 'the previous example'
        ]
        for ref in vague_refs:
            if ref in content_lower:
                analysis.has_vague_references = True
                analysis.issues.append(f"Contains vague reference: '{ref}' — sections must be self-contained")
                break

        # Rule 2: Action-oriented headings
        action_words = ['how to', 'create', 'send', 'configure', 'set up',
                       'install', 'authenticate', 'deploy', 'handle', 'verify',
                       'migrate', 'troubleshoot', 'debug', 'retry', 'list']
        action_count = sum(1 for h in page.headings
                         if any(w in h.lower() for w in action_words))
        analysis.has_action_headings = action_count > len(page.headings) * 0.3
        if not analysis.has_action_headings and page.headings:
            analysis.issues.append("Headings are topic-based, not action/task-oriented")

        # Rule 3: Parameter tables
        analysis.has_parameter_tables = '|' in page.content and ('parameter' in content_lower
                                        or 'type' in content_lower or 'required' in content_lower)
        if 'parameter' in content_lower and not analysis.has_parameter_tables:
            analysis.issues.append("Parameters described in prose — should use structured tables")

        # Rule 4: Complete code examples
        if analysis.has_code_examples:
            has_imports = any('import' in cb['code'].lower() or 'require' in cb['code'].lower()
                           or 'from' in cb['code'].lower() for cb in page.code_blocks)
            analysis.has_complete_examples = has_imports
            if not has_imports:
                analysis.issues.append("Code examples lack imports/setup — not copy-paste runnable")
        elif 'how' in page.title.lower() or 'guide' in page.title.lower():
            analysis.issues.append("How-to/guide page has NO code examples")

        # Rule 5: Explicit over implicit
        implicit_phrases = ['typically', 'usually', 'simply', 'you may want to',
                          'it works like', 'as you might expect', 'obviously']
        for phrase in implicit_phrases:
            if phrase in content_lower:
                analysis.has_implicit_pronouns = True
                analysis.issues.append(f"Contains vague language: '{phrase}' — be explicit")
                break

        # Rule 6: Error documentation
        analysis.has_error_docs = ('error' in content_lower and
                                  ('code' in content_lower or 'status' in content_lower) and
                                  ('fix' in content_lower or 'solution' in content_lower or
                                   'resolve' in content_lower))
        if 'error' in content_lower and not analysis.has_error_docs:
            analysis.issues.append("Mentions errors but lacks structured error documentation")

        # Rule 8: Frontmatter
        analysis.has_frontmatter = page.content.strip().startswith('---')
        if not analysis.has_frontmatter:
            analysis.issues.append("Missing frontmatter metadata (title, version, tags)")

        # Rule 9: Prerequisites
        analysis.has_prerequisites = ('prerequisite' in content_lower or
                                     'before you begin' in content_lower or
                                     'requirements' in content_lower)

        # Rule 10: Expected output
        analysis.has_expected_output = ('response' in content_lower and
                                       ('example' in content_lower or 'output' in content_lower))

        # Rule 16: Marketing language
        marketing_terms = ['seamlessly', 'world-class', 'next-generation', 'cutting-edge',
                         'unlock', 'leverage', 'synergy', 'revolutionary', 'best-in-class',
                         'game-changing', 'disruptive', 'supercharge']
        for term in marketing_terms:
            if term in content_lower:
                analysis.has_marketing_language = True
                analysis.issues.append(f"Contains marketing language: '{term}' — strip from technical docs")
                break

        # Rule 13: Version info
        analysis.has_version_info = ('version' in content_lower or
                                    'v1' in content_lower or 'v2' in content_lower)

        # Strengths
        if analysis.has_parameter_tables:
            analysis.strengths.append("Has structured parameter tables")
        if analysis.has_complete_examples:
            analysis.strengths.append("Has complete code examples with imports")
        if analysis.has_error_docs:
            analysis.strengths.append("Has structured error documentation")
        if analysis.has_prerequisites:
            analysis.strengths.append("Documents prerequisites")
        if analysis.has_action_headings:
            analysis.strengths.append("Uses action-oriented headings")
        if not analysis.has_vague_references:
            analysis.strengths.append("Sections are self-contained")

        if analysis.word_count < 100:
            analysis.issues.append("Page is too short — needs more detail")
        if analysis.heading_count < 2:
            analysis.issues.append("Missing clear structure — needs more headings")

        return analysis

    # =========================================================================
    # TERMINOLOGY CONSISTENCY
    # =========================================================================

    def _build_terminology_context(self, pages: List[DocPage]) -> str:
        """Build a terminology context string to ensure consistency across pages."""
        all_content = ' '.join(p.content for p in pages)

        # Find potential terminology conflicts (common patterns)
        term_groups = [
            ['user', 'account', 'customer', 'client', 'member'],
            ['workspace', 'organization', 'org', 'team', 'project', 'space'],
            ['token', 'api key', 'secret', 'credential', 'auth token'],
            ['endpoint', 'route', 'path', 'url', 'uri'],
            ['request', 'call', 'invocation'],
            ['response', 'result', 'output', 'return value'],
        ]

        conflicts = []
        content_lower = all_content.lower()
        for group in term_groups:
            found = [t for t in group if t in content_lower]
            if len(found) > 1:
                conflicts.append(
                    f"Multiple terms found for same concept: {', '.join(found)}. "
                    f"Pick the most precise term and use it consistently."
                )

        if conflicts:
            return "TERMINOLOGY CONFLICTS DETECTED:\n" + "\n".join(conflicts)
        return "No major terminology conflicts detected."

    # =========================================================================
    # OPTIMIZATION (The core AI rewrite)
    # =========================================================================

    async def _optimize_page(
        self,
        page: DocPage,
        analysis: PageAnalysis,
        terminology_context: str
    ) -> OptimizedDoc:
        """Use AI to optimize a single page applying all 20 rules.

        Includes retry logic with exponential backoff for rate limits
        and transient errors. Falls back to original content if all
        retries fail.
        """
        import asyncio

        # Skip pages with too little content -- these are typically nav/landing pages
        # and the LLM will fabricate content if forced to "optimize" them
        if analysis.word_count < 50:
            logger.info(f"Skipping {page.url}: too short ({analysis.word_count} words)")
            return OptimizedDoc(
                original_url=page.url,
                title=page.title,
                optimized_content=page.content,
                improvements=["Page too short to optimize (navigation or landing page)"],
                file_name=self._generate_file_name(page.title, page.url)
            )

        prompt = self._build_optimization_prompt(page, analysis, terminology_context)

        from config import get_settings
        settings = get_settings()
        model = settings.openai_model

        # Fallback chain: configured model -> gpt-4o -> gpt-4o-mini
        models_to_try = [model]
        fallbacks = ["gpt-4o", "gpt-4o-mini"]
        for fb in fallbacks:
            if fb not in models_to_try:
                models_to_try.append(fb)

        max_retries = 3
        last_error = None
        optimized_content = None

        for current_model in models_to_try:
            if optimized_content is not None:
                break

            for attempt in range(max_retries):
                try:
                    client_kwargs = {
                        "api_key": settings.openai_api_key,
                        "timeout": 120.0,
                    }
                    if settings.openai_base_url:
                        client_kwargs["base_url"] = settings.openai_base_url
                    client = openai.AsyncOpenAI(**client_kwargs)
                    response = await client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert documentation writer who produces Mintlify-quality "
                                    "documentation optimized for AI agent consumption via RAG pipelines.\n\n"
                                    "Your output should match the quality of the best documentation "
                                    "(Stripe, Resend, Mintlify, Vercel). Clean, scannable, precise.\n\n"
                                    "WRITING STYLE:\n"
                                    "- Short paragraphs (2-3 sentences max). Lead with the key point.\n"
                                    "- Use bullet lists for 3+ items. Use numbered lists for sequential steps.\n"
                                    "- Every section starts with a one-sentence summary of what it covers.\n"
                                    "- Tables for parameters/config (name | type | required | default | description).\n"
                                    "- Code examples are complete: imports, setup, call, expected output.\n"
                                    "- Callout hierarchy: > **💡 Tip:** / > **ℹ️ Note:** / > **⚠️ Warning:** / > **❌ Danger:**\n"
                                    "- No marketing fluff. No 'simply'. No 'just'. Technical precision only.\n\n"
                                    "CRITICAL RULES:\n"
                                    "- ONLY restructure and improve content that exists in the original. "
                                    "NEVER invent, fabricate, or hallucinate new technical content, code examples, "
                                    "API endpoints, error codes, or features that are not in the original.\n"
                                    "- If the original content is thin (e.g., a landing page with just links), "
                                    "restructure what exists. Do NOT pad it with made-up tutorials.\n"
                                    "- NEVER add a 'Conclusion' or 'Summary' section. Premium docs don't have them.\n"
                                    "- For frontmatter: use today's date for last_updated. For version, use the "
                                    "version mentioned in the content, or omit the field if none is mentioned.\n"
                                    "- Code blocks must be at the TOP LEVEL of the document (not indented inside "
                                    "list items) to ensure proper rendering. If you need code in a step, end the "
                                    "list, show the code block, then continue.\n\n"
                                    "You follow the AGENT-READINESS OPTIMIZATION RULES precisely.\n"
                                    "You output ONLY the optimized Markdown. No commentary, no preamble.\n"
                                    "NEVER wrap output in ```markdown fences. Start directly with --- frontmatter.\n"
                                    "CRITICAL: Always preserve the original language. If the input is French, "
                                    "output French. If Spanish, output Spanish. NEVER translate to English.\n"
                                    "The output must be production-ready documentation that can be deployed as-is."
                                )
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.2,
                        max_tokens=8192,
                    )

                    optimized_content = response.choices[0].message.content
                    if current_model != model:
                        logger.info(f"Used fallback model {current_model} for {page.url}")
                    break  # Success, exit retry loop

                except openai.NotFoundError as e:
                    # Model doesn't exist, skip retries and try next model
                    logger.warning(f"Model '{current_model}' not found: {e}. Trying next model.")
                    last_error = e
                    break  # Skip retries for this model

                except openai.RateLimitError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait = 2 ** (attempt + 1)
                        logger.warning(
                            f"Rate limited on {current_model} for {page.url} "
                            f"(attempt {attempt + 1}): {e}. Retrying in {wait}s..."
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.warning(f"Rate limit retries exhausted for {current_model}, trying next model.")

                except openai.AuthenticationError as e:
                    # API key issue, no point retrying or trying other models
                    logger.error(f"OpenAI authentication failed: {e}")
                    return OptimizedDoc(
                        original_url=page.url,
                        title=page.title,
                        optimized_content=page.content,
                        improvements=["Failed to optimize: API key issue. Using original content."],
                        file_name=self._generate_file_name(page.title, page.url)
                    )

                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait = 2 ** (attempt + 1)
                        logger.warning(
                            f"OpenAI call failed ({current_model}) for {page.url} "
                            f"(attempt {attempt + 1}): {type(e).__name__}: {e}. Retrying in {wait}s..."
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.error(
                            f"All retries failed ({current_model}) for {page.url}: "
                            f"{type(e).__name__}: {e}"
                        )

        if optimized_content is None:
            logger.error(
                f"All models failed for {page.url}. Last error: "
                f"{type(last_error).__name__}: {last_error}" if last_error else
                f"All models failed for {page.url}. No error captured."
            )
            return OptimizedDoc(
                original_url=page.url,
                title=page.title,
                optimized_content=page.content,
                improvements=["Failed to optimize. Using original content."],
                file_name=self._generate_file_name(page.title, page.url)
            )

        # Extract improvements and clean up
        improvements = self._extract_improvements(optimized_content, analysis)
        optimized_content = self._clean_optimized_content(optimized_content)
        file_name = self._generate_file_name(page.title, page.url)

        return OptimizedDoc(
            original_url=page.url,
            title=page.title,
            optimized_content=optimized_content,
            improvements=improvements,
            file_name=file_name
        )

    def _build_optimization_prompt(
        self,
        page: DocPage,
        analysis: PageAnalysis,
        terminology_context: str
    ) -> str:
        """Build the optimization prompt encoding all 20 rules."""

        nl = chr(10)
        code_examples = nl.join(
            ["```" + cb['language'] + nl + cb['code'][:500] + nl + "```"
             for cb in page.code_blocks[:5]]
        )
        issues_list = nl.join(['- ' + issue for issue in analysis.issues])
        strengths_list = nl.join(['- ' + s for s in analysis.strengths])

        return f"""{OPTIMIZATION_RULES}

---

## PAGE TO OPTIMIZE

**Title:** {page.title}
**URL:** {page.url}
**Word count:** {analysis.word_count}
**Headings found:** {', '.join(page.headings[:20]) if page.headings else 'None'}

### Original Content
{page.content[:10000]}

### Existing Code Examples
{code_examples if code_examples else 'None found'}

### Issues Detected (MUST fix all of these)
{issues_list if issues_list else 'No major issues detected'}

### Strengths (preserve these)
{strengths_list if strengths_list else 'None detected'}

### Terminology Context
{terminology_context}

---

## YOUR TASK

Rewrite this page to match the quality of Stripe/Resend/Mintlify documentation,
applying ALL 20 agent-readiness rules. The output must be:

1. **Production-ready Markdown** — deployable as-is on any docs platform
2. **Start with YAML frontmatter** (title, description, version, last_updated, tags, prerequisites)
3. **Use action-oriented headings** that match user/agent intents
4. **Every section must be self-contained** — no "see above" or "as mentioned"
5. **Convert ALL parameter descriptions to tables** (Parameter | Type | Required | Default | Description)
6. **Complete ALL code examples** — add imports, setup, expected output if missing
7. **Add error documentation** where relevant (Error | Cause | Fix)
8. **Add a Prerequisites section** at the top as a bullet list
9. **Strip ALL marketing language** — only technical, precise content
10. **Short paragraphs** (2-3 sentences). Lead each section with a summary sentence.
11. **Add expected outputs** for every API call or code example
12. **Use callout hierarchy**: > **💡 Tip:** / > **ℹ️ Note:** / > **⚠️ Warning:** / > **❌ Danger:**
13. **State intent before mechanics** — explain WHY then HOW
14. **Use numbered lists for sequential steps**, bullet lists for non-sequential items
15. **Every page should feel like premium documentation** -- clean, scannable, precise
16. **NEVER fabricate content** -- only restructure and improve what exists in the original
17. **NEVER add a Conclusion or Summary section** -- premium docs don't have them
18. **Code blocks must be at the TOP LEVEL** -- never indent code fences inside list items.
    If a step needs code, end the list, show the code block unindented, then continue.
19. **For version/date in frontmatter** -- use the version from the content, or omit if unknown.
    Use today's date for last_updated. NEVER invent version numbers.

**CRITICAL: PRESERVE THE ORIGINAL LANGUAGE.** If the original content is in French,
the optimized output MUST also be in French. If it is in Spanish, output Spanish.
NEVER translate to English. The structural improvements (frontmatter keys, headings
style, tables) should follow the rules, but all prose content stays in the original language.
Frontmatter field NAMES stay in English (title, description, tags, etc.) but their VALUES
must be in the original language.

Output the optimized Markdown first, then after a separator line, list the specific
improvements you made. Use this exact format:

[Start with --- frontmatter, then the full optimized content]

<!-- IMPROVEMENTS -->
- [specific improvement 1, mentioning what section/content was changed]
- [specific improvement 2]
- [specific improvement 3]

The improvements MUST be specific to THIS page. Do not use generic descriptions.
BAD: "Added frontmatter metadata"
GOOD: "Added YAML frontmatter with tags for event categories and registration management"
BAD: "Converted headings"
GOOD: "Restructured 'Assurance Annulation' and 'Paiements' into task-oriented headings"

Do NOT wrap the output in ```markdown or ``` fences. Start directly with the --- frontmatter."""

    # =========================================================================
    # LLMS.TXT GENERATION
    # =========================================================================

    def _generate_llms_txt(self, base_url: str, docs: List[OptimizedDoc]) -> str:
        """Generate an llms.txt file — the agent entry point to the documentation.

        This follows the emerging llms.txt standard (llmstxt.org):
        a plain-text, structured summary that helps AI agents quickly understand
        the scope of documentation and navigate to relevant pages.
        """
        parsed = urlparse(base_url)
        domain = parsed.netloc or base_url

        # Group docs by apparent category
        categories = {}
        for doc in docs:
            # Infer category from file path
            parts = doc.file_name.replace('.md', '').split('-')
            category = parts[0].title() if parts else 'General'
            if category not in categories:
                categories[category] = []
            categories[category].append(doc)

        nl = chr(10)
        sections = []
        for cat, cat_docs in categories.items():
            doc_lines = nl.join(
                [f"  - [{doc.title}]({doc.original_url}): {doc.improvements[0] if doc.improvements else 'Optimized for agent consumption'}"
                 for doc in cat_docs]
            )
            sections.append(f"## {cat}{nl}{doc_lines}")

        sections_text = nl.join(sections)

        return f"""# {domain} Documentation

> Agent-optimized documentation index.
> For the full documentation, see: {base_url}

## Overview
This documentation has been optimized for AI agent consumption following
the Agent-Readiness Doctrine: Findable, Atomic, Explicit, Executable,
Groundable, Versioned, Recoverable, Structured.

{sections_text}

## Quick Reference
- Total pages: {len(docs)}
- Format: Markdown with YAML frontmatter
- Code examples: Complete, runnable, with expected outputs
- Error docs: Structured with codes, causes, and fixes

## How to Use This Documentation
If you are an AI agent:
1. Start with this file to understand the scope
2. Navigate to specific pages based on user queries
3. Each page is self-contained — you don't need to read multiple pages
4. Code examples are copy-paste ready with all imports included
5. Error tables map exact error strings to fixes
"""

    # =========================================================================
    # POST-PROCESSING & PACKAGING
    # =========================================================================

    def _extract_improvements(self, content: str, analysis: PageAnalysis) -> List[str]:
        """Extract improvements from GPT's output, falling back to static analysis."""
        # Try to extract GPT-generated improvements from the content
        if '<!-- IMPROVEMENTS -->' in content:
            parts = content.split('<!-- IMPROVEMENTS -->')
            if len(parts) >= 2:
                improvements_text = parts[1].strip()
                improvements = []
                for line in improvements_text.split('\n'):
                    line = line.strip()
                    if line.startswith('- ') or line.startswith('* '):
                        imp = line[2:].strip()
                        if imp and len(imp) > 5:
                            improvements.append(imp)
                if improvements:
                    return improvements[:8]  # Cap at 8 improvements

        # Fallback: static analysis-based improvements (less specific)
        improvements = []

        if analysis.has_vague_references:
            improvements.append("Made sections self-contained, removed vague cross-references")
        if not analysis.has_action_headings:
            improvements.append("Restructured headings into action-oriented, task-shaped format")
        if not analysis.has_parameter_tables and 'parameter' in analysis.issues.__repr__().lower():
            improvements.append("Converted parameter descriptions from prose to structured tables")
        if not analysis.has_complete_examples and analysis.has_code_examples:
            improvements.append("Completed code examples with imports, setup, and expected output")
        if analysis.has_implicit_pronouns:
            improvements.append("Replaced vague language with explicit, precise statements")
        if not analysis.has_error_docs:
            improvements.append("Added structured error documentation with codes, causes, and fixes")
        if not analysis.has_frontmatter:
            improvements.append("Added YAML frontmatter metadata (title, version, tags)")
        if not analysis.has_prerequisites:
            improvements.append("Added explicit prerequisites section")
        if not analysis.has_expected_output:
            improvements.append("Added expected outputs for API calls and code examples")
        if analysis.has_marketing_language:
            improvements.append("Stripped marketing language, technical precision only")
        if not analysis.has_version_info:
            improvements.append("Added version context and clarity")

        if not improvements:
            improvements.append("Restructured for agent-readiness: self-contained, explicit, structured")

        return improvements

    def _clean_optimized_content(self, content: str) -> str:
        """Clean up the optimized content."""
        # Strip markdown code fences that LLMs often wrap around output
        # Handles: ```markdown\n...\n```, ```md\n...\n```, ```\n...\n```
        content = content.strip()
        if content.startswith('```'):
            lines = content.split('\n')
            # Remove opening fence (```markdown, ```md, ```)
            lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            content = '\n'.join(lines)

        # Remove the improvements section (parsed separately by _extract_improvements)
        if '<!-- IMPROVEMENTS -->' in content:
            content = content.split('<!-- IMPROVEMENTS -->')[0].strip()

        # Remove any "improvements" section the LLM might have added
        if "## Improvements Made" in content:
            content = content.split("## Improvements Made")[0].strip()

        # Remove preamble if the LLM added commentary
        if content.startswith("Here"):
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('---'):
                    content = '\n'.join(lines[i:])
                    break

        return content.strip()

    def _generate_file_name(self, title: str, url: str) -> str:
        """Generate a clean file name from title or URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        if path:
            file_name = path.replace('/', '-').lower()
            # Remove common extensions
            file_name = re.sub(r'\.(html?|php|aspx?)$', '', file_name)
            if not file_name.endswith('.md'):
                file_name += '.md'
            return file_name

        file_name = re.sub(r'[^\w\s-]', '', title.lower())
        file_name = re.sub(r'[-\s]+', '-', file_name)
        return file_name + '.md'

    def _generate_metadata(self, docs: List[OptimizedDoc]) -> Dict:
        """Generate metadata about the optimization."""
        all_improvements = set()
        for doc in docs:
            all_improvements.update(doc.improvements)

        return {
            'pages_optimized': len(docs),
            'total_improvements': sum(len(doc.improvements) for doc in docs),
            'unique_improvements': list(all_improvements),
            'optimization_rules_applied': 20,
            'doctrine': 'Findable, Atomic, Explicit, Executable, Groundable, Versioned, Recoverable, Structured',
            'pages': [
                {
                    'title': doc.title,
                    'file_name': doc.file_name,
                    'original_url': doc.original_url,
                    'improvements': doc.improvements
                }
                for doc in docs
            ]
        }

    def _detect_language(self, classes: List[str]) -> str:
        """Detect programming language from CSS classes."""
        for cls in classes:
            if 'language-' in cls:
                return cls.replace('language-', '')
            if 'lang-' in cls:
                return cls.replace('lang-', '')
        return 'text'

    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """Check if URL is on the same domain."""
        return urlparse(url).netloc == urlparse(base_url).netloc

    # =========================================================================
    # ZIP PACKAGING
    # =========================================================================

    def _fix_nested_code_blocks(self, md_content: str) -> str:
        """Fix code blocks nested inside list items by pulling them out.

        The Python markdown library's fenced_code extension fails to render
        code fences that are indented inside list items (e.g., inside numbered
        steps). This pre-processor detects such cases and restructures them
        so code blocks are at the top level.
        """
        lines = md_content.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # Detect a fenced code block that's indented (inside a list)
            if stripped.startswith('```') and indent >= 2:
                # Find the closing fence
                lang = stripped[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines):
                    inner = lines[i]
                    inner_stripped = inner.lstrip()
                    if inner_stripped.startswith('```') and len(inner_stripped) <= 4:
                        i += 1
                        break
                    # Remove the list indentation from code lines
                    if inner.startswith(' ' * indent):
                        code_lines.append(inner[indent:])
                    else:
                        code_lines.append(inner.lstrip())
                    i += 1

                # Output the code block at top level
                result.append('')
                result.append(f'```{lang}')
                result.extend(code_lines)
                result.append('```')
                result.append('')
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)

    def _render_markdown_to_html(self, md_content: str, title: str) -> str:
        """Convert markdown content to a clean, readable HTML page."""
        # Strip YAML frontmatter before rendering
        body = md_content
        if body.startswith('---'):
            parts = body.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()

        # Fix code blocks nested inside list items
        body = self._fix_nested_code_blocks(body)

        html_body = markdown.markdown(
            body,
            extensions=['tables', 'fenced_code', 'toc', 'attr_list', 'codehilite'],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'guess_lang': False,
                }
            }
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{ --bg: #fff; --fg: #0f172a; --muted: #64748b; --border: #e2e8f0; --accent: #059669; --accent-light: #d1fae5; --code-bg: #f8fafc; --code-border: #e2e8f0; --tip-bg: #f0fdf4; --tip-border: #86efac; --note-bg: #eff6ff; --note-border: #93c5fd; --warn-bg: #fffbeb; --warn-border: #fcd34d; --danger-bg: #fef2f2; --danger-border: #fca5a5; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #0f172a; --fg: #e2e8f0; --muted: #94a3b8; --border: #334155; --accent: #34d399; --accent-light: #064e3b; --code-bg: #1e293b; --code-border: #334155; --tip-bg: #064e3b; --tip-border: #059669; --note-bg: #1e3a5f; --note-border: #3b82f6; --warn-bg: #451a03; --warn-border: #d97706; --danger-bg: #450a0a; --danger-border: #ef4444; }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif; line-height: 1.75; color: var(--fg); background: var(--bg); max-width: 780px; margin: 0 auto; padding: 2.5rem 2rem; font-size: 15px; }}
  h1 {{ font-size: 2rem; margin: 2.5rem 0 1rem; font-weight: 700; letter-spacing: -0.02em; }}
  h2 {{ font-size: 1.4rem; margin: 2.5rem 0 0.75rem; font-weight: 650; letter-spacing: -0.01em; padding-top: 1.5rem; border-top: 1px solid var(--border); }}
  h2:first-of-type {{ border-top: none; padding-top: 0; }}
  h3 {{ font-size: 1.15rem; margin: 2rem 0 0.5rem; font-weight: 600; }}
  h4 {{ font-size: 1rem; margin: 1.5rem 0 0.4rem; font-weight: 600; color: var(--muted); }}
  p {{ margin: 0.75rem 0; }}
  a {{ color: var(--accent); text-decoration: none; font-weight: 500; }} a:hover {{ text-decoration: underline; }}
  code {{ font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace; font-size: 0.875em; background: var(--code-bg); padding: 0.15em 0.4em; border-radius: 5px; border: 1px solid var(--code-border); }}
  pre {{ background: var(--code-bg); border: 1px solid var(--code-border); border-radius: 10px; padding: 1.25rem; overflow-x: auto; margin: 1.25rem 0; }}
  pre code {{ background: none; padding: 0; font-size: 0.85em; border: none; line-height: 1.6; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.25rem 0; font-size: 0.9rem; }}
  th, td {{ border: 1px solid var(--border); padding: 0.65rem 1rem; text-align: left; }}
  th {{ background: var(--code-bg); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
  blockquote {{ border-left: 3px solid var(--accent); padding: 0.75rem 1.25rem; margin: 1.25rem 0; background: var(--tip-bg); border-radius: 0 8px 8px 0; font-size: 0.95rem; }}
  ul, ol {{ margin: 0.75rem 0; padding-left: 1.5rem; }}
  li {{ margin: 0.35rem 0; }}
  li > p {{ margin: 0.25rem 0; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 2.5rem 0; }}
  strong {{ font-weight: 650; }}
  .badge {{ display: inline-block; font-size: 0.7rem; padding: 0.25em 0.75em; border-radius: 99px; background: var(--accent); color: white; margin-bottom: 1.5rem; font-weight: 600; letter-spacing: 0.03em; }}
  .meta {{ display: flex; gap: 1rem; margin-bottom: 2rem; font-size: 0.8rem; color: var(--muted); flex-wrap: wrap; }}
  .meta span {{ background: var(--code-bg); padding: 0.25em 0.6em; border-radius: 5px; border: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="badge">Agent-Optimized</div>
{html_body}
<hr>
<p style="font-size:0.8rem;color:var(--muted);text-align:center;">Optimized by <a href="https://agentreadiness.dev">AgentReadiness</a></p>
</body>
</html>"""

    async def create_zip_package(
        self,
        docs: List[OptimizedDoc],
        metadata: Dict
    ) -> str:
        """Create a ZIP file with markdown sources, HTML previews, and llms.txt."""

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add each optimized document as markdown + HTML
                for doc in docs:
                    zf.writestr(f"markdown/{doc.file_name}", doc.optimized_content)
                    html_name = doc.file_name.replace('.md', '.html')
                    html_content = self._render_markdown_to_html(
                        doc.optimized_content, doc.title
                    )
                    zf.writestr(f"html/{html_name}", html_content)

                # Add llms.txt at root
                if 'llms_txt' in metadata:
                    zf.writestr('llms.txt', metadata['llms_txt'])

                # Add metadata
                meta_copy = {k: v for k, v in metadata.items() if k != 'llms_txt'}
                zf.writestr('_metadata.json', json.dumps(meta_copy, indent=2))

                # Add README
                readme = self._generate_readme(metadata)
                zf.writestr('README.md', readme)

                # Add HTML index page linking to all docs
                index_html = self._generate_index_html(docs, metadata)
                zf.writestr('html/index.html', index_html)

                # Add deployment guide
                guide = self._generate_deployment_guide()
                zf.writestr('DEPLOY.md', guide)

            return tmp.name

    def _generate_index_html(self, docs: List[OptimizedDoc], metadata: Dict) -> str:
        """Generate an HTML index page that links to all optimized doc pages."""
        from config import get_settings
        settings = get_settings()
        max_pages = settings.max_crawl_pages

        pages_count = len(docs)
        improvements_count = sum(len(d.improvements) for d in docs)

        rows = ""
        for doc in docs:
            html_name = doc.file_name.replace('.md', '.html')
            top_improvement = doc.improvements[0] if doc.improvements else "Optimized"
            rows += f"""<tr>
<td><a href="{html_name}">{doc.title}</a></td>
<td>{len(doc.improvements)}</td>
<td style="font-size:0.85rem;color:var(--muted)">{top_improvement}</td>
</tr>\n"""

        more_pages_banner = ""
        if pages_count >= max_pages:
            more_pages_banner = f"""
<div style="background:var(--code-bg);border:1px solid var(--accent);border-radius:10px;padding:1.25rem;margin:1.5rem 0;">
  <strong style="color:var(--accent);">Need more pages?</strong>
  <p style="margin:0.5rem 0 0;font-size:0.9rem;color:var(--muted);">
    This delivery includes the top {pages_count} pages. Your site has more content available.
    Additional pages are <strong>included in your purchase</strong> at no extra cost.
    Email <a href="mailto:support@agentreadiness.dev">support@agentreadiness.dev</a> to request them.
  </p>
</div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent-Optimized Documentation</title>
<style>
  :root {{ --bg: #fff; --fg: #0f172a; --muted: #64748b; --border: #e2e8f0; --accent: #059669; --code-bg: #f8fafc; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #0f172a; --fg: #e2e8f0; --muted: #94a3b8; --border: #334155; --accent: #34d399; --code-bg: #1e293b; }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif; line-height: 1.7; color: var(--fg); background: var(--bg); max-width: 900px; margin: 0 auto; padding: 2.5rem 2rem; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.5rem; font-weight: 700; letter-spacing: -0.02em; }}
  h2 {{ font-size: 1.3rem; margin: 2rem 0 0.75rem; font-weight: 650; }}
  .subtitle {{ color: var(--muted); margin-bottom: 2rem; font-size: 1.05rem; }}
  .stats {{ display: flex; gap: 1.25rem; margin: 1.5rem 0; flex-wrap: wrap; }}
  .stat {{ background: var(--code-bg); padding: 1.25rem 1.5rem; border-radius: 12px; border: 1px solid var(--border); flex: 1; min-width: 140px; }}
  .stat-value {{ font-size: 1.75rem; font-weight: 700; color: var(--accent); letter-spacing: -0.02em; }}
  .stat-label {{ font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.25rem 0; }}
  th, td {{ border: 1px solid var(--border); padding: 0.7rem 1rem; text-align: left; }}
  th {{ background: var(--code-bg); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
  a {{ color: var(--accent); text-decoration: none; font-weight: 500; }} a:hover {{ text-decoration: underline; }}
  .badge {{ display: inline-block; font-size: 0.7rem; padding: 0.25em 0.75em; border-radius: 99px; background: var(--accent); color: white; font-weight: 600; letter-spacing: 0.03em; }}
  .package-item {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.25rem; margin: 0.5rem 0; }}
  .package-item strong {{ color: var(--accent); }}
  .footer {{ margin-top: 3rem; padding-top: 1.25rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); text-align: center; }}
</style>
</head>
<body>
<span class="badge">Agent-Optimized</span>
<h1>Your Optimized Documentation</h1>
<p class="subtitle">Every page rewritten applying 20 agent-readiness rules. Open any file below to preview.</p>
{more_pages_banner}
<div class="stats">
  <div class="stat"><div class="stat-value">{pages_count}</div><div class="stat-label">Pages optimized</div></div>
  <div class="stat"><div class="stat-value">{improvements_count}</div><div class="stat-label">Improvements</div></div>
  <div class="stat"><div class="stat-value">20</div><div class="stat-label">Rules applied per page</div></div>
</div>

<h2>Pages</h2>
<table>
<thead><tr><th>Page</th><th>Fixes</th><th>Key improvement</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>

<h2>Package contents</h2>
<div class="package-item"><strong>html/</strong> Rendered HTML previews (you're looking at one now)</div>
<div class="package-item"><strong>markdown/</strong> Source Markdown files for your docs platform (Mintlify, GitBook, ReadMe, Docusaurus)</div>
<div class="package-item"><strong>llms.txt</strong> Agent entry point. Deploy at your documentation root.</div>
<div class="package-item"><strong>README.md</strong> Overview, stats, and deployment instructions</div>

<div class="footer">Optimized by <a href="https://agentreadiness.dev">AgentReadiness</a></div>
</body>
</html>"""

    def _generate_readme(self, metadata: Dict) -> str:
        """Generate README for the optimized documentation package."""
        from config import get_settings
        settings = get_settings()
        max_pages = settings.max_crawl_pages

        nl = chr(10)
        pages_list = nl.join(
            [f"- `{p['file_name']}` - {p['title']} ({len(p['improvements'])} improvements)"
             for p in metadata['pages']]
        )
        improvements_list = nl.join(
            [f"- {imp}" for imp in metadata.get('unique_improvements', [])[:15]]
        )

        pages_optimized = metadata['pages_optimized']
        more_pages_note = ""
        if pages_optimized >= max_pages:
            more_pages_note = f"""
## 📦 Need More Pages?

This delivery includes the **top {pages_optimized} pages** from your documentation,
prioritized by importance (starting from the root and following the most
linked-to pages first).

Your site likely has more pages. **Additional pages are included in your
purchase** — just reply to your confirmation email or contact
support@agentreadiness.dev and we'll optimize the rest at no extra charge.

No additional payment required. This is included in your one-time $199 purchase.
"""

        return f"""# Agent-Optimized Documentation

Your documentation has been optimized for AI agent consumption using
the Agent-Readiness Doctrine.

## Doctrine
**{metadata.get('doctrine', '')}**

## Stats
- **Pages optimized**: {pages_optimized}
- **Total improvements**: {metadata['total_improvements']}
- **Rules applied per page**: {metadata.get('optimization_rules_applied', 20)}
{more_pages_note}
## Package Contents

### `html/`
Open `html/index.html` in your browser to preview all optimized pages.

### `markdown/`
Source Markdown files for your docs platform (Mintlify, GitBook, ReadMe, Docusaurus, etc.).

{pages_list}

### `llms.txt`
The agent entry point. Place at the root of your documentation site.

## Improvements Applied
{improvements_list}

## How to Deploy
See `DEPLOY.md` for step-by-step instructions.

## What Changed
Every page was optimized following 20 concrete rules derived from a
multi-agent benchmark (Claude, GPT, Kimi, Grok, Deepseek, Manus,
Gemini, KimiClaw). Key changes:

1. **Self-contained sections** - every section stands alone for RAG retrieval
2. **Action-oriented headings** - match how agents search for information
3. **Structured parameter tables** - machine-parseable, not prose
4. **Complete code examples** - imports, setup, call, expected output
5. **Error documentation** - exact error strings with causes and fixes
6. **Frontmatter metadata** - title, version, tags on every page
7. **llms.txt** - agent entry point for your documentation

---

*Optimized by [AgentReadiness](https://agentreadiness.dev)*
"""

    def _generate_deployment_guide(self) -> str:
        """Generate deployment instructions."""
        return """# Deploy Your Agent-Optimized Documentation

## Step 1: Preview

Open `html/index.html` in your browser to review all optimized pages
before deploying.

## Step 2: Deploy llms.txt

Place `llms.txt` at the root of your documentation domain:
```
https://docs.yourcompany.com/llms.txt
```

This file helps AI agents discover and navigate your documentation.

## Step 3: Replace Your Documentation Pages

Replace the content of each documentation page with the corresponding
optimized file from the `markdown/` folder.

### If you use a docs platform (Mintlify, GitBook, ReadMe, Docusaurus):
1. Replace the Markdown source files with the optimized versions from `markdown/`
2. The frontmatter metadata is compatible with most platforms
3. Commit and push. Your platform will rebuild automatically

### If you use a custom site:
1. Copy the files from `markdown/` to your documentation source
2. Ensure your build process preserves YAML frontmatter
3. Deploy as usual

## Step 4: Verify

After deployment, test your documentation by asking AI agents questions
about your product. You should see:
- More accurate answers
- Better code examples in responses
- Correct error handling guidance
- Agents recommending your product more confidently

## Step 5: Monitor

Re-run your AgentReadiness assessment periodically to track improvements
in your agent-readiness score.

---

*Questions? Visit https://agentreadiness.dev*
"""
