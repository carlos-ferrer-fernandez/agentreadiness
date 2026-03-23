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

SYSTEM_PROMPT = """\
You are a source-faithful documentation rewriter and optimizer.

Your job is to transform a crawled documentation page into production-ready Markdown optimized for AI retrieval and RAG systems, while preserving the full technical substance of the source.

INSTRUCTION PRIORITY
1. Follow the user-supplied metadata exactly.
2. Preserve the source content's meaning, scope, and technical detail.
3. Improve structure, clarity, retrieval quality, and formatting.
4. Never invent unsupported facts.

CORE BEHAVIOR
- This is a REWRITE, not a summary.
- Preserve all unique technical content from the source.
- Do not remove, collapse, or gloss over technical detail in order to make the page shorter or more "scannable".
- If the source is long and detailed, the output must remain long and detailed.
- Short paragraphs are allowed, but only by splitting content into clearer units. Never use brevity as a reason to condense content.
- Preserve all substantive items that appear in the source, including:
  - technical explanations
  - steps and workflows
  - links and link intent
  - warnings, notes, and limitations
  - parameter names and descriptions
  - code blocks
  - error messages and troubleshooting content
  - constraints, defaults, requirements, and edge cases
  - version statements
  - literal strings that matter for retrieval

PAGE-TYPE BEHAVIOR
- PAGE_TYPE is authoritative.
- If PAGE_TYPE = content:
  - Treat the page as a normal documentation page.
  - Preserve full technical depth and detail.
- If PAGE_TYPE = hub:
  - Treat the page as a landing page / index / navigation hub.
  - Your job is to clean structure, preserve categories, preserve link text, preserve one-line descriptions, and improve heading hierarchy and formatting.
  - Do NOT turn a hub page into a tutorial, conceptual deep-dive, API reference, troubleshooting page, or code-heavy page unless the source already contains that content.
  - Do NOT add technical depth, examples, errors, workflows, prerequisites, or explanatory sections that are not explicitly present.
  - For hub pages, realistic improvements are structural and formatting improvements, not invented substance.

ZERO FABRICATION
- Never add facts that are not supported by the source or explicit user metadata.
- Never invent API endpoints, SDK calls, parameters, defaults, limits, versions, dates, error codes, outputs, responses, prerequisites, or migration steps.
- Never "complete" partial code by guessing missing lines.
- Never add error sections unless the source contains error-related content.
- Never add expected outputs unless they are present in the source.
- Never add a Prerequisites section unless prerequisites are explicitly stated in the source.
- If a formatting rule would require invented content, skip that formatting rule rather than fabricate.

LINK FIDELITY RULES
- Preserve link targets exactly when they are explicitly provided in the source or user metadata.
- If the user provides an EXTRACTED_LINKS block, treat it as authoritative for link destinations.
- If a link target cannot be determined from the source, NEVER guess or fabricate a URL.
- NEVER default unresolved links to PAGE_URL.
- NEVER assign multiple distinct links to the same URL unless the source explicitly shows that they share the same target.
- If a target is unresolved:
  - prefer a same-document anchor if the link clearly points to a section present in the output
  - otherwise use a safe local fragment based on the descriptive text, such as [Link Text](#link-text)
  - if even that would be misleading, keep the label as plain text rather than inventing a URL
- Preserve link intent even when the exact external target is unavailable.

MISSING / THIN CONTENT RULES
- If the source briefly mentions a topic but does not provide details, include only a brief faithful mention or a link/reference if available.
- Do NOT expand thin mentions into explanatory paragraphs.
- Do NOT write meta-commentary about what the source contains.
- Never refer to:
  - "the source page"
  - "the source"
  - "this page indicates"
  - "the documentation states"
  - or similar framing
- The output IS the documentation, not commentary about the documentation.

TRUNCATION RULES
- If the source appears truncated or ends abruptly mid-section, do NOT attempt to complete, summarize, infer, or describe the missing remainder.
- End the document cleanly at the last complete section supported by the source.
- Do NOT add placeholder paragraphs for missing material.
- Do NOT write sentences that merely announce that a topic exists without source-backed content.

ALLOWED IMPROVEMENTS
You MAY:
- reorganize sections
- rewrite headings to be more action-oriented
- convert existing parameter/config/reference prose into tables
- add YAML frontmatter
- add callout formatting
- restate existing facts to make sections self-contained
- improve terminology consistency
- rewrite for clarity and retrieval quality
- translate faithfully when the user explicitly provides a TARGET_LANGUAGE

LANGUAGE RULES
- If the user provides TARGET_LANGUAGE, output the entire document in TARGET_LANGUAGE.
- If TARGET_LANGUAGE differs from the crawled page language, treat TARGET_LANGUAGE as authoritative and translate faithfully without adding or removing meaning.
- If TARGET_LANGUAGE is not provided, preserve the source language.
- Do not mix languages, except:
  - frontmatter field names remain in English
  - code syntax remains as-is
- In non-English output, frontmatter field values must be in the output language.

FRONTMATTER RULES
- Output must start with YAML frontmatter.
- Use these field names when supported:
  - title
  - description
  - version
  - last_updated
  - tags
  - prerequisites
- Set last_updated to the exact value of TODAY_UTC provided by the user.
- If TODAY_UTC is not provided, omit last_updated.
- Never guess, infer, or hallucinate a date.
- Include version only if it is explicitly stated in the source. Otherwise omit it.
- tags must be derived from concepts explicitly present in the source.
- prerequisites must contain only prerequisites explicitly present in the source; otherwise use an empty list.
- An empty prerequisites list is correct metadata, not a substantive section that needs elaboration.

CONTENT-PRESERVATION RULES
- Preserve coverage, depth, and specificity.
- Do not reduce a detailed section to bullets if the source contains explanatory prose.
- Do not replace detailed examples with summaries.
- Do not merge multiple distinct concepts into one generic section.
- If you convert prose to a table, keep any important nuance in prose below the table.
- If the source contains a landing page or link hub, preserve it as a landing page or link hub. Do not turn it into a tutorial.
- Padding with restatements is worse than being concise. Never restate the same information in multiple section structures just to increase output length.
- If you have already covered a fact, do not repeat it in a "navigation map", "page scope", "link intent", or summary-of-sections block.
- MIN_OUTPUT_WORD_COUNT is a completeness guard, not a license to pad, repeat, or invent content.

STRUCTURE AND STYLE
- Use clear H1 → H2 → H3 hierarchy.
- Use action-oriented headings where faithful to the source.
- Make each section self-contained for retrieval.
- Lead sections with a one-sentence summary when helpful, but do not add fluff.
- Use numbered lists for procedures and bullet lists for non-sequential items.
- Use callouts only when supported by source content.
- No marketing language.
- No "simply", "just", or vague filler.
- No conclusion or summary section.
- Code blocks must be top-level, not nested inside list items.
- Never wrap the whole output in ```markdown fences.

CONFLICT RESOLUTION
If any optimization rule conflicts with source-faithfulness, source-faithfulness wins.

FINAL OUTPUT RULES
- Output ONLY the final Markdown document.
- No commentary, no explanations, no separator lines, no "improvements made" list.
- Start directly with YAML frontmatter.

SILENT SELF-CHECK BEFORE FINALIZING
Verify all of the following:
- Output language matches TARGET_LANGUAGE if provided, otherwise source language.
- last_updated exactly matches TODAY_UTC if provided.
- version is omitted unless explicitly present in source.
- No invented technical content was added.
- No substantive source content was removed.
- Output is not shorter in substance than the source.
- If PAGE_TYPE = hub, the output remains a hub/index page and does not invent depth.
- No meta-commentary about "the source" appears anywhere.
- No distinct unresolved links were collapsed onto PAGE_URL or the same fabricated URL.
- If the source is truncated, the document ends cleanly at the last supported complete section.
- Output starts with frontmatter and contains only Markdown.
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

    # Use a real browser user-agent so SSR sites (Next.js, Nuxt, etc.)
    # return full server-rendered HTML instead of empty JS shells.
    BROWSER_UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": self.BROWSER_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
        )
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

        # Step 1: Crawl documentation (progress 0.05 → 0.25)
        await self._notify_progress(progress_callback, "crawling", 0.05)

        try:
            pages = await self._crawl_documentation(start_url, progress_callback)
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

    async def _crawl_documentation(self, start_url: str, progress_callback=None) -> List[DocPage]:
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
                logger.info(f"Crawling page {len(pages)+1}/{max_pages}: {url}")
                page = await self._fetch_page(url)
                visited.add(url)  # Always mark visited, even on failure

                if page:
                    # Only add pages with meaningful content (not just nav/landing)
                    if page.content and len(page.content.strip()) > 50:
                        pages.append(page)
                        # Report crawl progress (0.05 → 0.25 range)
                        crawl_progress = 0.05 + (0.20 * len(pages) / max_pages)
                        await self._notify_progress(
                            progress_callback,
                            f"crawling ({len(pages)}/{max_pages} pages)",
                            crawl_progress,
                        )

                    # Discover new links (both absolute and relative)
                    for link in page.links:
                        href = link['href'] if isinstance(link, dict) else link
                        normalized = urldefrag(href)[0].rstrip('/')
                        if normalized and normalized not in visited:
                            parsed_link = urlparse(normalized)
                            if parsed_link.netloc == base_domain:
                                # Stay within the docs scope
                                if not base_path or parsed_link.path.startswith(base_path):
                                    to_visit.append(normalized)

                # Brief delay to be polite to the target server
                import asyncio
                await asyncio.sleep(settings.crawl_delay_seconds)

            except Exception as e:
                visited.add(url)  # Mark visited on error too
                logger.warning(f"Failed to fetch {url}: {e}")

        logger.info(f"Crawled {len(pages)} content pages from {len(visited)} URLs visited")
        return pages

    async def _fetch_page(self, url: str) -> Optional[DocPage]:
        """Fetch and parse a single page.

        Uses httpx with a browser user-agent (works for most SSR sites like
        Next.js, Nuxt, etc.). Only falls back to Playwright for truly
        client-side-only SPAs where httpx returns < 200 chars of content.
        Playwright is memory-heavy (~300MB) so we avoid it when possible.
        """
        from urllib.parse import urljoin

        try:
            # If we already know this site is JS-rendered, go straight to Playwright
            if self._needs_js_rendering and HAS_PLAYWRIGHT:
                return await self._fetch_page_with_playwright(url)

            # --- Fast path: plain HTTP with browser user-agent ---
            response = await self.client.get(url)
            if response.status_code != 200:
                return None

            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type and 'text/plain' not in content_type:
                return None

            page = self._parse_html_to_page(response.text, url)

            # --- Fallback: JS rendering via Playwright (last resort) ---
            # Most SSR sites (Next.js, Nuxt) serve full HTML to browser UAs.
            # Only fall back to Playwright for truly client-only SPAs.
            if page and len(page.content.strip()) < 200 and HAS_PLAYWRIGHT:
                logger.info(f"Thin content ({len(page.content.strip())} chars) from {url} — trying Playwright")
                rendered_page = await self._fetch_page_with_playwright(url)
                if rendered_page and len(rendered_page.content.strip()) > len(page.content.strip()):
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
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",   # Critical for Docker — /dev/shm is only 64MB
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--single-process",           # Saves ~100MB RAM
                ],
            )
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
                user_agent="GrounDocsBot/1.0 (Documentation Analysis)"
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
        """Parse raw HTML string into a DocPage with content, headings, links.

        IMPORTANT: We extract the main content container FIRST, then clean up
        noise inside it. The previous approach of removing nav/sidebar/etc by
        class name BEFORE finding content was destroying the content itself
        (e.g. Stripe wraps everything in a div with class 'Sidebar--expanded').
        """
        from urllib.parse import urljoin

        soup = BeautifulSoup(html, 'html.parser')

        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else "Untitled"

        # Step 1: Find the main content container FIRST (before any cleanup)
        main = (soup.find('article') or
                soup.find('main') or
                soup.find('div', role='main') or
                soup.find('div', class_=re.compile(
                    r'(docs-content|documentation|page-content|markdown-body|'
                    r'article-content|post-content|entry-content|Content-article)',
                    re.IGNORECASE
                )) or
                soup.find('div', class_='content'))

        if not main:
            # Last resort: use body, but clean up noise first
            main = soup.find('body')
            if main:
                # Only remove noise tags when using body as container
                for tag in main.find_all(['nav', 'footer', 'aside', 'header', 'script', 'style', 'noscript']):
                    tag.decompose()
                for tag in main.find_all(class_=re.compile(
                    r'^(nav|footer|cookie|banner)$',  # Strict match, not partial
                    re.IGNORECASE
                )):
                    tag.decompose()
        else:
            # Clean up noise INSIDE the content container (not parents)
            for tag in main.find_all(['nav', 'footer', 'script', 'style', 'noscript']):
                tag.decompose()

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

        # Collect ALL links from the page with text + URL for link fidelity
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
            text = a.get_text(strip=True)
            if absolute.startswith('http') and text:
                links.append({'text': text, 'href': absolute})

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

        # Fallback chain: configured model -> gpt-5.4-mini -> gpt-4o
        models_to_try = [model]
        fallbacks = ["gpt-5.4-mini", "gpt-4o"]
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
                                "content": SYSTEM_PROMPT,
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.2,
                        max_completion_tokens=8192,
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

        # Post-processing: validate no fabrication
        optimized_content = self._validate_no_fabrication(
            optimized_content, page.content, page.code_blocks
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

    @staticmethod
    def _detect_content_language(text: str) -> str:
        """Detect the natural language of content using common word heuristics.

        Returns an ISO 639-1 code (e.g. 'en', 'fr', 'es', 'de').
        Falls back to 'en' if uncertain.
        """
        sample = text[:2000].lower()

        lang_markers = {
            'fr': [' les ', ' des ', ' une ', ' pour ', ' avec ', ' dans ', ' votre ', ' sont ', ' cette '],
            'es': [' los ', ' las ', ' una ', ' para ', ' con ', ' esta ', ' como ', ' más ', ' tiene '],
            'de': [' die ', ' das ', ' und ', ' für ', ' mit ', ' eine ', ' wird ', ' sich ', ' auch '],
            'pt': [' para ', ' uma ', ' com ', ' dos ', ' são ', ' como ', ' mais ', ' esta ', ' você '],
            'it': [' per ', ' una ', ' con ', ' del ', ' sono ', ' come ', ' dalla ', ' nella ', ' questo '],
        }

        scores = {}
        for lang, markers in lang_markers.items():
            scores[lang] = sum(1 for m in markers if m in sample)

        best_lang = max(scores, key=scores.get) if scores else 'en'
        if scores.get(best_lang, 0) >= 3:
            return best_lang
        return 'en'

    @staticmethod
    def _detect_page_type(page: 'DocPage', analysis: 'PageAnalysis') -> str:
        """Classify page as 'hub' (navigation/index) or 'content' (documentation).

        Uses a scoring heuristic: hub pages have many links, little prose,
        no code blocks, and titles that look like category names.
        Content pages override if they have code, tables, or detailed steps.
        """
        content = page.content
        link_count = len(page.links) if page.links else 0
        code_block_count = len(page.code_blocks) if page.code_blocks else 0
        word_count = analysis.word_count
        heading_count = analysis.heading_count

        # Count long paragraphs (80+ words) — proxy for explanatory prose
        paragraphs = content.split('\n\n')
        long_paragraph_count = sum(
            1 for p in paragraphs
            if len(p.split()) >= 80 and not p.strip().startswith(('|', '-', '*', '#', '```'))
        )

        # Count ordered list items (proxy for step-by-step procedures)
        import re
        ordered_steps = len(re.findall(r'^\d+\.', content, re.MULTILINE))

        # Check title/headings for hub-like signals
        title = (page.title or '').lower()
        headings_text = ' '.join(page.headings or []).lower()
        combined = title + ' ' + headings_text
        hub_title_terms = [
            'overview', 'get started', 'getting started', 'docs', 'guides',
            'products', 'topics', 'use cases', 'resources', 'documentation',
        ]
        title_hub_signal = any(term in combined for term in hub_title_terms)

        hub_score = 0
        content_score = 0

        # Hub signals
        if link_count >= 8:
            hub_score += 2
        if word_count > 0 and (word_count / max(link_count, 1)) <= 40:
            hub_score += 2
        if code_block_count == 0:
            hub_score += 1
        if not analysis.has_parameter_tables:
            hub_score += 1
        if ordered_steps <= 3:
            hub_score += 1
        if long_paragraph_count <= 2:
            hub_score += 1
        if title_hub_signal:
            hub_score += 1

        # Content signals (strong overrides)
        if code_block_count >= 1:
            content_score += 3
        if analysis.has_parameter_tables:
            content_score += 2
        if ordered_steps >= 4:
            content_score += 2
        if long_paragraph_count >= 3:
            content_score += 2
        if analysis.has_error_docs:
            content_score += 2

        # Content overrides hub
        if content_score >= 4:
            return 'content'
        if hub_score >= 5 and content_score <= 2:
            return 'hub'
        # Conservative default
        return 'content'

    @staticmethod
    def _extract_links(page: 'DocPage') -> str:
        """Build an EXTRACTED_LINKS block from the page's link data.

        Returns a formatted string listing visible text -> URL or UNRESOLVED.
        """
        if not page.links:
            return 'None found'

        lines = []
        seen = set()
        for link in page.links[:50]:  # Cap at 50 links
            if isinstance(link, dict):
                text = link.get('text', '').strip()
                href = link.get('href', '').strip()
            elif isinstance(link, str):
                text = link
                href = ''
            else:
                continue

            if not text or text in seen:
                continue
            seen.add(text)

            if href and href != '#' and not href.startswith('javascript:'):
                lines.append(f'- {text} -> {href}')
            else:
                lines.append(f'- {text} -> UNRESOLVED')

        return '\n'.join(lines) if lines else 'None found'

    @staticmethod
    def _detect_truncation(content: str, max_chars: int) -> str:
        """Detect if content was likely truncated at the character limit."""
        if len(content) >= max_chars - 100:
            return 'possibly_truncated'
        return 'complete'

    def _build_optimization_prompt(
        self,
        page: DocPage,
        analysis: PageAnalysis,
        terminology_context: str
    ) -> str:
        """Build the optimization prompt using the GPT-5.4-designed template."""
        from datetime import date

        nl = chr(10)
        code_examples = nl.join(
            ["```" + cb['language'] + nl + cb['code'][:500] + nl + "```"
             for cb in page.code_blocks[:5]]
        )
        issues_list = nl.join(['- ' + issue for issue in analysis.issues])
        strengths_list = nl.join(['- ' + s for s in analysis.strengths])

        today_utc = date.today().isoformat()
        detected_lang = self._detect_content_language(page.content)
        # Target language is English unless the site is genuinely non-English
        # (the crawler sends Accept-Language: en, so English sites return English)
        target_language = detected_lang

        headings_str = ', '.join(page.headings[:20]) if page.headings else 'None'
        page_type = self._detect_page_type(page, analysis)
        content_limit = 12000
        source_content_status = self._detect_truncation(page.content, content_limit)
        extracted_links = self._extract_links(page)
        link_count = len(page.links) if page.links else 0
        code_block_count = len(page.code_blocks) if page.code_blocks else 0

        return f"""## JOB METADATA

TARGET_LANGUAGE: {target_language}
DETECTED_PAGE_LANGUAGE: {detected_lang}
TODAY_UTC: {today_utc}
PAGE_TITLE: {page.title}
PAGE_URL: {page.url}
PAGE_TYPE: {page_type}
SOURCE_CONTENT_STATUS: {source_content_status}
ORIGINAL_WORD_COUNT: {analysis.word_count}
MIN_OUTPUT_WORD_COUNT: {analysis.word_count}
HEADINGS_FOUND: {headings_str}
LINK_COUNT: {link_count}
CODE_BLOCK_COUNT: {code_block_count}

## TASK

Rewrite the page into production-ready Markdown optimized for AI agent consumption and RAG retrieval.

Follow these page-specific rules:
- Treat PAGE_TYPE as authoritative.
- If PAGE_TYPE = hub:
  - Preserve the page as a hub / index / navigation page.
  - Focus on clean heading hierarchy, faithful link formatting, concise descriptions, and structural cleanup.
  - Do NOT add technical depth, tutorials, workflows, code examples, troubleshooting, prerequisites, or error documentation unless explicitly present in the source.
- If PAGE_TYPE = content:
  - Preserve all technical depth, detail, examples, warnings, and retrieval-relevant literals.
- MIN_OUTPUT_WORD_COUNT is a completeness guard against omission, not a target to hit by padding.
- If SOURCE_CONTENT_STATUS = possibly_truncated, or if the content ends abruptly mid-section, stop cleanly at the last complete section.
- Do NOT complete missing sections.
- Do NOT write placeholder paragraphs.
- Do NOT refer to "the source", "the source page", or similar meta-language.
- If a topic is only mentioned briefly, keep it brief unless the source provides more detail.

Link handling rules:
- Use explicit link targets exactly as provided.
- If EXTRACTED_LINKS includes a resolved URL, use it.
- If a link target is unresolved or missing, NEVER guess and NEVER default to PAGE_URL.
- For unresolved targets, use a same-page anchor when justified, or a safe local fragment based on the visible link text.
- Never map multiple distinct links to the same URL unless that target is explicitly present in the source.

When applying optimization rules, use this priority:
1. Source fidelity and completeness
2. Correct output language
3. Correct frontmatter date
4. Structural and retrieval improvements

## OPTIMIZATION RULES

Apply these rules ONLY when they can be satisfied from the source content itself:

1. Self-contained sections
- Each section should make sense on its own.
- Replace context-dependent phrasing with explicit restatements of existing facts.

2. Action-oriented headings
- Use headings that match user intent where faithful to the source.
- Keep a strict H1 → H2 → H3 hierarchy.

3. Structured reference content
- Convert parameters, options, fields, config, and return values into tables when those details exist in the source.
- Do not drop nuance when converting prose to tables.

4. Code examples
- Preserve every existing code example.
- You may reformat or label existing examples for clarity.
- Do NOT invent missing imports, setup, calls, or outputs.
- If a source example is partial, keep it partial rather than guessing.

5. Explicit statements
- Surface defaults, limits, requirements, and constraints when explicitly present in the source.
- Do not infer unstated defaults or limits.

6. Error documentation
- If the source includes errors or troubleshooting, structure that material clearly.
- If the source does not include error content, do not add it.

7. Terminology consistency
- Use one consistent term per concept.
- If the source uses multiple terms for the same concept, normalize carefully without changing meaning.

8. Frontmatter
- Add YAML frontmatter at the top.
- last_updated must equal TODAY_UTC exactly.
- version only if explicit in source.
- tags must come from source concepts.
- prerequisites must contain only explicit prerequisites from the source, otherwise use [].

9. Prerequisites
- If prerequisites are explicitly present anywhere in the source, gather them near the top.
- Do not invent prerequisites.

10. Expected outputs
- If expected outputs or results are present in the source, place them near the relevant example.
- Do not invent outputs.

11. Contextual links
- Keep links descriptive and give enough context for retrieval.

12. Separate content types
- Keep conceptual, procedural, and reference content clearly organized.

13. Version clarity
- Preserve explicit version applicability and deprecation notes from the source.
- Do not invent version ranges or migration paths.

14. Decision guidance
- If the source compares options, make that comparison clearer.
- Do not add new comparisons not supported by the source.

15. Safety boundaries
- Preserve and emphasize destructive actions, billing implications, quotas, and irreversible operations when present.

16. Remove anti-patterns
- Strip marketing fluff and vague filler.
- Replace weak phrasing with precise technical prose.
- Do not remove substantive content.

17. Retrieval optimization
- Make sections focused and self-contained.
- Use exact identifiers and concrete nouns from the source.

18. Intent before mechanics
- Explain why a task is done before how, using only source-supported information.

19. Lifecycle/state transitions
- If the source describes states or lifecycles, structure them clearly.

20. Callouts
- Use callouts for warnings, notes, tips, and errors only when supported by source content.

## ISSUES DETECTED (fix when possible without inventing content)

{issues_list if issues_list else 'No major issues detected'}

## STRENGTHS TO PRESERVE

{strengths_list if strengths_list else 'None detected'}

## TERMINOLOGY CONTEXT

{terminology_context}

## EXTRACTED LINKS

{extracted_links}

## ORIGINAL CONTENT

{page.content[:content_limit]}

## EXISTING CODE EXAMPLES

{code_examples if code_examples else 'None found'}

## OUTPUT REQUIREMENTS

Your output must:
- start with YAML frontmatter
- be valid Markdown only
- contain no commentary before or after the document
- contain no separator lines and no "improvements made" section
- preserve the source page's technical depth
- preserve all substantive content from the source
- use TARGET_LANGUAGE
- use TODAY_UTC exactly for last_updated
- omit version if not explicitly present in the source
- avoid any invented facts
- if PAGE_TYPE = hub, remain a hub page with no invented depth
- if SOURCE_CONTENT_STATUS = possibly_truncated, end cleanly at last complete section
- never refer to "the source page" or "the source" — the output IS the documentation"""

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

    def _validate_no_fabrication(
        self, optimized: str, original_content: str, original_code_blocks: List[Dict]
    ) -> str:
        """Post-processing check: remove likely fabricated content.

        Detects code blocks and error/troubleshooting tables that appear
        in the optimized output but have no basis in the original content.
        Also fixes fabricated dates in YAML frontmatter.
        """
        from datetime import date

        # Fix fabricated dates in frontmatter — replace any last_updated
        # that doesn't match today's date with the correct date
        today = date.today().isoformat()
        date_pattern = re.compile(
            r'^(last_updated:\s*["\']?)(\d{4}-\d{2}-\d{2})(["\']?\s*)$',
            re.MULTILINE,
        )
        match = date_pattern.search(optimized)
        if match and match.group(2) != today:
            logger.info(
                f"Fabrication validator: fixed date {match.group(2)} → {today}"
            )
            optimized = date_pattern.sub(
                rf'\g<1>{today}\g<3>', optimized
            )
        original_lower = original_content.lower()
        original_code_strings = {
            cb['code'].strip().lower()[:100] for cb in original_code_blocks
        }
        # Check if the original had ANY code
        has_original_code = bool(original_code_blocks) or '```' in original_content

        lines = optimized.split('\n')
        cleaned_lines = []
        in_suspect_code_block = False
        in_suspect_table = False
        skip_until_fence = False
        fabrication_removed = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect code fences that weren't in original
            if line.strip().startswith('```') and not skip_until_fence:
                if not has_original_code:
                    # Original had NO code at all — this is fabricated
                    skip_until_fence = True
                    fabrication_removed = True
                    i += 1
                    continue
                else:
                    # Original had code — keep it
                    cleaned_lines.append(line)
                    i += 1
                    continue
            elif skip_until_fence:
                if line.strip().startswith('```'):
                    skip_until_fence = False  # End of fabricated block
                i += 1
                continue

            # Detect troubleshooting/error tables on pages without error docs
            if (line.strip().startswith('|') and
                    ('error' in line.lower() or 'troubleshoot' in line.lower() or
                     'cause' in line.lower() and 'fix' in line.lower()) and
                    'error' not in original_lower and
                    'troubleshoot' not in original_lower):
                # Skip this table row and surrounding table
                in_suspect_table = True
                fabrication_removed = True
                i += 1
                continue
            elif in_suspect_table:
                if line.strip().startswith('|'):
                    i += 1
                    continue
                else:
                    in_suspect_table = False

            # Detect fabricated headings like "Troubleshooting" or "Common Errors"
            # on pages that don't mention errors at all
            if (line.strip().startswith('#') and
                    any(kw in line.lower() for kw in ['troubleshoot', 'common error', 'error code']) and
                    'error' not in original_lower and
                    'troubleshoot' not in original_lower):
                fabrication_removed = True
                i += 1
                # Skip content under this heading until next heading
                while i < len(lines) and not lines[i].strip().startswith('#'):
                    i += 1
                continue

            cleaned_lines.append(line)
            i += 1

        if fabrication_removed:
            logger.info("Fabrication validator: removed suspected fabricated content")

        return '\n'.join(cleaned_lines)

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

        # Fallback: static analysis-based improvements
        # Only claim improvements that are verifiable — never claim content was
        # "added" if the source didn't have the raw material for it.
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
        # Only claim error docs improvement if the source HAD error content to restructure
        if not analysis.has_error_docs and analysis.has_code_examples:
            # Check if the optimized output actually contains error content
            if 'error' in content.lower() and ('| error' in content.lower() or '| code' in content.lower()):
                improvements.append("Structured error documentation with codes, causes, and fixes")
        if not analysis.has_frontmatter:
            improvements.append("Added YAML frontmatter metadata (title, version, tags)")
        # Don't claim "added prerequisites" if they're empty — that's just correct metadata
        if not analysis.has_prerequisites and 'prerequisites:' in content and '- ' in content.split('prerequisites:')[1][:100] if 'prerequisites:' in content else False:
            improvements.append("Added explicit prerequisites section")
        # Only claim expected outputs if the output actually contains them
        if not analysis.has_expected_output and analysis.has_code_examples:
            if '```' in content and ('output' in content.lower() or 'response' in content.lower() or 'returns' in content.lower()):
                improvements.append("Added expected outputs for API calls and code examples")
        if analysis.has_marketing_language:
            improvements.append("Stripped marketing language, technical precision only")
        if not analysis.has_version_info and 'version' in content.lower():
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
<p style="font-size:0.8rem;color:var(--muted);text-align:center;">Optimized by <a href="https://groundocs.com">GrounDocs</a></p>
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
    Email <a href="mailto:support@groundocs.com">support@groundocs.com</a> to request them.
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

<div class="footer">Optimized by <a href="https://groundocs.com">GrounDocs</a></div>
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
support@groundocs.com and we'll optimize the rest at no extra charge.

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

*Optimized by [GrounDocs](https://groundocs.com)*
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

Re-run your GrounDocs assessment periodically to track improvements
in your agent-readiness score.

---

*Questions? Visit https://groundocs.com*
"""
