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

logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')


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

        pages = await self._crawl_documentation(start_url)
        logger.info(f"Crawled {len(pages)} pages")

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
        """Crawl documentation site and extract pages."""
        pages = []
        visited = set()
        to_visit = [start_url]
        max_pages = 100

        while to_visit and len(pages) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue

            try:
                page = await self._fetch_page(url)
                if page:
                    pages.append(page)
                    visited.add(url)

                    for link in page.links:
                        if link not in visited and self._is_same_domain(link, start_url):
                            to_visit.append(link)

            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")

        return pages

    async def _fetch_page(self, url: str) -> Optional[DocPage]:
        """Fetch and parse a single page."""
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else "Untitled"

            main = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if not main:
                main = soup.find('body')

            content = main.get_text(separator='\n', strip=True) if main else ""

            code_blocks = []
            for pre in soup.find_all('pre'):
                code = pre.find('code')
                if code:
                    language = self._detect_language(code.get('class', []))
                    code_blocks.append({
                        'language': language,
                        'code': code.get_text(strip=True)
                    })

            headings = []
            for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                headings.append(h.get_text(strip=True))

            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http'):
                    links.append(href)

            return DocPage(
                url=url,
                title=title_text,
                content=content,
                code_blocks=code_blocks,
                headings=headings,
                links=links
            )

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

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

        prompt = self._build_optimization_prompt(page, analysis, terminology_context)

        from config import get_settings
        settings = get_settings()
        model = settings.openai_model

        # Fallback chain: configured model -> gpt-4o -> gpt-4o-mini
        models_to_try = [model]
        if model != "gpt-4o":
            models_to_try.append("gpt-4o")
        if "gpt-4o-mini" not in models_to_try:
            models_to_try.append("gpt-4o-mini")

        max_retries = 3
        last_error = None
        optimized_content = None

        for current_model in models_to_try:
            if optimized_content is not None:
                break

            for attempt in range(max_retries):
                try:
                    client = openai.AsyncOpenAI(timeout=120.0)
                    response = await client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert documentation optimizer. Your SOLE purpose is to "
                                    "rewrite documentation so it is maximally useful for AI agents "
                                    "(Claude, GPT, Gemini, etc.) that consume it via RAG pipelines.\n\n"
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
                        max_tokens=4096,
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
{page.content[:6000]}

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

Rewrite this page applying ALL 20 rules above. The output must be:

1. **Production-ready Markdown** — deployable as-is, not a draft
2. **Start with YAML frontmatter** (title, description, version, last_updated, tags, prerequisites)
3. **Use action-oriented headings** that match user/agent intents
4. **Every section must be self-contained** — no "see above" or "as mentioned"
5. **Convert ALL parameter descriptions to tables** (Parameter | Type | Required | Default | Description)
6. **Complete ALL code examples** — add imports, setup, expected output if missing
7. **Add error documentation** where relevant (error code | cause | fix)
8. **Add prerequisites section** at the top
9. **Strip ALL marketing language** — only technical, precise content
10. **Replace vague pronouns** — always restate the explicit subject
11. **Add expected outputs** for every API call or code example
12. **Use callouts** for warnings, tips, and important notes
13. **State intent before mechanics** — explain WHY then HOW

**CRITICAL: PRESERVE THE ORIGINAL LANGUAGE.** If the original content is in French,
the optimized output MUST also be in French. If it is in Spanish, output Spanish.
NEVER translate to English. The structural improvements (frontmatter keys, headings
style, tables) should follow the rules, but all prose content stays in the original language.
Frontmatter field NAMES stay in English (title, description, tags, etc.) but their VALUES
must be in the original language.

Output ONLY the optimized Markdown. No explanations. No "here's the optimized version".
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
        """Determine what improvements were made based on analysis."""
        improvements = []

        # Based on issues that were found (and should now be fixed)
        if analysis.has_vague_references:
            improvements.append("Made sections self-contained — removed vague cross-references")
        if not analysis.has_action_headings:
            improvements.append("Converted headings to action-oriented, task-shaped format")
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
            improvements.append("Stripped marketing language — technical precision only")
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

    def _render_markdown_to_html(self, md_content: str, title: str) -> str:
        """Convert markdown content to a clean, readable HTML page."""
        # Strip YAML frontmatter before rendering
        body = md_content
        if body.startswith('---'):
            parts = body.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()

        html_body = markdown.markdown(
            body,
            extensions=['tables', 'fenced_code', 'toc', 'attr_list'],
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{ --bg: #fff; --fg: #1a1a1a; --muted: #666; --border: #e5e5e5; --accent: #2563eb; --code-bg: #f5f5f5; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #111; --fg: #e5e5e5; --muted: #999; --border: #333; --accent: #60a5fa; --code-bg: #1e1e1e; }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.7; color: var(--fg); background: var(--bg); max-width: 800px; margin: 0 auto; padding: 2rem 1.5rem; }}
  h1 {{ font-size: 2rem; margin: 2rem 0 1rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; }}
  h2 {{ font-size: 1.5rem; margin: 1.8rem 0 0.8rem; color: var(--fg); }}
  h3 {{ font-size: 1.2rem; margin: 1.5rem 0 0.6rem; }}
  h4 {{ font-size: 1rem; margin: 1.2rem 0 0.4rem; color: var(--muted); }}
  p {{ margin: 0.8rem 0; }}
  a {{ color: var(--accent); text-decoration: none; }} a:hover {{ text-decoration: underline; }}
  code {{ font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.9em; background: var(--code-bg); padding: 0.15em 0.4em; border-radius: 4px; }}
  pre {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; overflow-x: auto; margin: 1rem 0; }}
  pre code {{ background: none; padding: 0; font-size: 0.85em; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }}
  th, td {{ border: 1px solid var(--border); padding: 0.6rem 0.8rem; text-align: left; }}
  th {{ background: var(--code-bg); font-weight: 600; }}
  blockquote {{ border-left: 4px solid var(--accent); padding: 0.5rem 1rem; margin: 1rem 0; background: var(--code-bg); border-radius: 0 6px 6px 0; }}
  ul, ol {{ margin: 0.8rem 0; padding-left: 1.5rem; }}
  li {{ margin: 0.3rem 0; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 2rem 0; }}
  .badge {{ display: inline-block; font-size: 0.75rem; padding: 0.2em 0.6em; border-radius: 12px; background: var(--accent); color: white; margin-bottom: 1rem; }}
</style>
</head>
<body>
<div class="badge">Agent-Optimized</div>
{html_body}
<hr>
<p style="font-size:0.8rem;color:var(--muted);">Optimized by AgentReadiness. 20 rules applied.</p>
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

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent-Optimized Documentation</title>
<style>
  :root {{ --bg: #fff; --fg: #1a1a1a; --muted: #666; --border: #e5e5e5; --accent: #2563eb; --code-bg: #f5f5f5; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #111; --fg: #e5e5e5; --muted: #999; --border: #333; --accent: #60a5fa; --code-bg: #1e1e1e; }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.7; color: var(--fg); background: var(--bg); max-width: 900px; margin: 0 auto; padding: 2rem 1.5rem; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
  .subtitle {{ color: var(--muted); margin-bottom: 2rem; }}
  .stats {{ display: flex; gap: 2rem; margin: 1.5rem 0; }}
  .stat {{ background: var(--code-bg); padding: 1rem 1.5rem; border-radius: 8px; border: 1px solid var(--border); }}
  .stat-value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
  .stat-label {{ font-size: 0.8rem; color: var(--muted); }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
  th, td {{ border: 1px solid var(--border); padding: 0.7rem 1rem; text-align: left; }}
  th {{ background: var(--code-bg); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
  a {{ color: var(--accent); text-decoration: none; font-weight: 500; }} a:hover {{ text-decoration: underline; }}
  .badge {{ display: inline-block; font-size: 0.75rem; padding: 0.2em 0.6em; border-radius: 12px; background: var(--accent); color: white; }}
  .footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); }}
</style>
</head>
<body>
<span class="badge">Agent-Optimized</span>
<h1>Your Optimized Documentation</h1>
<p class="subtitle">Every page rewritten applying 20 agent-readiness rules. Open any file below to see the result.</p>

<div class="stats">
  <div class="stat"><div class="stat-value">{pages_count}</div><div class="stat-label">Pages optimized</div></div>
  <div class="stat"><div class="stat-value">{improvements_count}</div><div class="stat-label">Improvements applied</div></div>
  <div class="stat"><div class="stat-value">20</div><div class="stat-label">Rules per page</div></div>
</div>

<h2>Pages</h2>
<table>
<thead><tr><th>Page</th><th>Fixes</th><th>Key improvement</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>

<h2>What's in this package</h2>
<ul>
  <li><strong>html/</strong> &mdash; rendered HTML pages (you're looking at one now)</li>
  <li><strong>markdown/</strong> &mdash; source Markdown files for your docs platform</li>
  <li><strong>llms.txt</strong> &mdash; agent entry point (deploy at your docs root)</li>
  <li><strong>README.md</strong> &mdash; overview and deployment instructions</li>
</ul>

<div class="footer">Optimized by AgentReadiness. 20 rules applied per page.</div>
</body>
</html>"""

    def _generate_readme(self, metadata: Dict) -> str:
        """Generate README for the optimized documentation package."""
        nl = chr(10)
        pages_list = nl.join(
            [f"- `{p['file_name']}` - {p['title']} ({len(p['improvements'])} improvements)"
             for p in metadata['pages']]
        )
        improvements_list = nl.join(
            [f"- {imp}" for imp in metadata.get('unique_improvements', [])[:15]]
        )

        return f"""# Agent-Optimized Documentation

Your documentation has been optimized for AI agent consumption using
the Agent-Readiness Doctrine.

## Doctrine
**{metadata.get('doctrine', '')}**

## Stats
- **Pages optimized**: {metadata['pages_optimized']}
- **Total improvements**: {metadata['total_improvements']}
- **Rules applied per page**: {metadata.get('optimization_rules_applied', 20)}

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
