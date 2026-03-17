"""
Agent-Readiness Rule Analyzer

Evaluates documentation pages against the 20 concrete rules derived from
the multi-agent benchmark (Claude, GPT, Kimi, Grok, Deepseek, Manus, Gemini, KimiClaw).

This is the CORE evaluation engine used by both:
- Free assessment (diagnose: which rules pass/fail?)
- Paid optimizer (fix: apply all 20 rules to rewrite docs)
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RuleResult:
    """Result of evaluating a single rule across all pages."""
    rule_id: int
    name: str
    short_name: str
    category: str  # Maps to one of the 5 scoring components
    score: int  # 0-100
    status: str  # 'pass', 'warning', 'fail'
    finding: str  # Human-readable finding
    pages_checked: int = 0
    pages_passing: int = 0

    def to_dict(self) -> dict:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'short_name': self.short_name,
            'category': self.category,
            'score': self.score,
            'status': self.status,
            'finding': self.finding,
            'pages_checked': self.pages_checked,
            'pages_passing': self.pages_passing,
        }


@dataclass
class RuleAnalysisResult:
    """Complete result of analyzing documentation against all 20 rules."""
    rule_results: List[RuleResult]
    overall_score: int
    grade: str
    components: Dict[str, int]  # 5-component scores for backward compat
    top_issues: List[dict]

    def to_dict(self) -> dict:
        return {
            'rule_results': [r.to_dict() for r in self.rule_results],
            'overall_score': self.overall_score,
            'grade': self.grade,
            'components': self.components,
            'top_issues': self.top_issues,
        }


# Rule-to-component mapping
RULE_COMPONENTS = {
    # accuracy: Can agents answer correctly from retrieved chunks?
    'accuracy': [1, 5, 7, 12, 13, 18],
    # context_utilization: Are the right chunks retrieved?
    'context_utilization': [2, 8, 11, 17],
    # citation_quality: Can answers be grounded to source?
    'citation_quality': [9, 10, 14, 19],
    # code_executability: Do examples work?
    'code_executability': [4, 6],
    # structure: Is the doc well-structured for agents?
    'structure': [3, 15, 16, 20],
}

# Component weights for overall score
COMPONENT_WEIGHTS = {
    'accuracy': 0.30,
    'context_utilization': 0.25,
    'citation_quality': 0.20,
    'code_executability': 0.15,
    'structure': 0.10,
}

GRADE_BOUNDARIES = [
    (97, 'A+'), (93, 'A'), (90, 'A-'),
    (87, 'B+'), (83, 'B'), (80, 'B-'),
    (77, 'C+'), (73, 'C'), (70, 'C-'),
    (60, 'D'), (0, 'F'),
]


class AgentReadinessAnalyzer:
    """Evaluates documentation against the 20 agent-readiness rules.

    Each rule is evaluated across all crawled pages. The result is:
    - A score per rule (0-100)
    - A pass/warning/fail status per rule
    - A human-readable finding per rule
    - Component scores (aggregated from rules)
    - An overall score and grade
    """

    def analyze(self, pages: list) -> RuleAnalysisResult:
        """Analyze pages against all 20 rules.

        Args:
            pages: List of crawled Page objects (from crawler.py)

        Returns:
            RuleAnalysisResult with per-rule scores, components, and grade
        """
        if not pages:
            return self._empty_result()

        # Pre-compute cross-page data
        all_content = ' '.join(p.content or '' for p in pages)
        all_content_lower = all_content.lower()

        # Evaluate each rule
        rule_results = [
            self._rule_01_self_contained(pages),
            self._rule_02_action_headings(pages),
            self._rule_03_parameter_tables(pages),
            self._rule_04_complete_code(pages),
            self._rule_05_explicit_language(pages),
            self._rule_06_error_docs(pages),
            self._rule_07_consistent_terminology(pages, all_content_lower),
            self._rule_08_frontmatter(pages),
            self._rule_09_prerequisites(pages),
            self._rule_10_expected_outputs(pages),
            self._rule_11_cross_references(pages),
            self._rule_12_content_separation(pages),
            self._rule_13_version_clarity(pages),
            self._rule_14_decision_docs(pages, all_content_lower),
            self._rule_15_safety_boundaries(pages, all_content_lower),
            self._rule_16_no_anti_patterns(pages),
            self._rule_17_retrieval_chunks(pages),
            self._rule_18_intent_before_mechanics(pages),
            self._rule_19_state_transitions(pages, all_content_lower),
            self._rule_20_callouts(pages),
        ]

        # Calculate component scores
        components = {}
        for comp_name, rule_ids in RULE_COMPONENTS.items():
            comp_scores = [r.score for r in rule_results if r.rule_id in rule_ids]
            components[comp_name] = round(sum(comp_scores) / len(comp_scores)) if comp_scores else 0

        # Calculate overall score
        overall = round(sum(
            components[c] * COMPONENT_WEIGHTS[c]
            for c in components
        ))

        # Determine grade
        grade = 'F'
        for boundary, g in GRADE_BOUNDARIES:
            if overall >= boundary:
                grade = g
                break

        # Generate top issues from failing rules
        top_issues = self._generate_top_issues(rule_results)

        return RuleAnalysisResult(
            rule_results=rule_results,
            overall_score=overall,
            grade=grade,
            components=components,
            top_issues=top_issues,
        )

    # =========================================================================
    # RULE EVALUATORS
    # =========================================================================

    def _rule_01_self_contained(self, pages: list) -> RuleResult:
        """Rule 1: Self-contained sections — no 'see above' or 'as mentioned'."""
        vague_patterns = [
            r'\bsee\s+(above|previous|earlier)\b',
            r'\bas\s+(mentioned|described|noted|shown|discussed)\s+(above|earlier|previously)\b',
            r'\brefer\s+to\s+(the\s+)?(above|previous)\b',
            r'\bthe\s+previous\s+(section|example|step)\b',
        ]
        combined = re.compile('|'.join(vague_patterns), re.IGNORECASE)

        passing = 0
        for page in pages:
            content = page.content or ''
            if not combined.search(content):
                passing += 1

        score = round(passing / len(pages) * 100) if pages else 0
        return RuleResult(
            rule_id=1,
            name='Self-Contained Sections',
            short_name='self_contained',
            category='accuracy',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(pages)} pages are self-contained (no vague cross-references)',
            pages_checked=len(pages),
            pages_passing=passing,
        )

    def _rule_02_action_headings(self, pages: list) -> RuleResult:
        """Rule 2: Action-oriented, task-shaped headings."""
        action_patterns = re.compile(
            r'\b(how\s+to|create|send|configure|set\s*up|install|authenticate|deploy|'
            r'handle|verify|migrate|troubleshoot|debug|retry|list|get|update|delete|'
            r'build|connect|test|monitor|manage|enable|disable|upgrade)\b',
            re.IGNORECASE
        )

        total_headings = 0
        action_headings = 0
        for page in pages:
            if page.heading_hierarchy:
                for h in page.heading_hierarchy:
                    total_headings += 1
                    if action_patterns.search(h.get('text', '')):
                        action_headings += 1

        if total_headings == 0:
            score = 0
            finding = 'No headings found — documentation has no structure'
        else:
            ratio = action_headings / total_headings
            score = min(100, round(ratio * 100 * 1.5))  # Boost because 50%+ is good
            finding = f'{action_headings}/{total_headings} headings are action-oriented'

        return RuleResult(
            rule_id=2,
            name='Action-Oriented Headings',
            short_name='action_headings',
            category='context_utilization',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=action_headings,
        )

    def _rule_03_parameter_tables(self, pages: list) -> RuleResult:
        """Rule 3: Structured parameter tables (not prose)."""
        pages_with_params = 0
        pages_with_tables = 0

        param_keywords = re.compile(
            r'\b(parameter|argument|option|field|property|attribute)\b', re.IGNORECASE
        )
        table_pattern = re.compile(r'\|.*\|.*\|')  # Markdown table rows

        for page in pages:
            content = page.content or ''
            if param_keywords.search(content):
                pages_with_params += 1
                if table_pattern.search(content):
                    pages_with_tables += 1

        if pages_with_params == 0:
            score = 70  # Neutral — no params to document
            finding = 'No parameter documentation detected'
        else:
            ratio = pages_with_tables / pages_with_params
            score = round(ratio * 100)
            finding = f'{pages_with_tables}/{pages_with_params} pages with parameters use structured tables'

        return RuleResult(
            rule_id=3,
            name='Structured Parameter Tables',
            short_name='param_tables',
            category='structure',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=pages_with_params,
            pages_passing=pages_with_tables,
        )

    def _rule_04_complete_code(self, pages: list) -> RuleResult:
        """Rule 4: Complete, runnable code examples with imports."""
        pages_with_code = 0
        pages_with_complete_code = 0

        import_patterns = re.compile(
            r'\b(import|require|from|include|using|use)\b'
        )

        for page in pages:
            if page.code_blocks and len(page.code_blocks) > 0:
                pages_with_code += 1
                # Check if any code block has imports
                has_imports = any(
                    import_patterns.search(cb.get('code', ''))
                    for cb in page.code_blocks
                )
                # Check if code blocks have language tags
                has_lang = any(
                    cb.get('language') and cb['language'] != 'text'
                    for cb in page.code_blocks
                )
                if has_imports and has_lang:
                    pages_with_complete_code += 1

        if pages_with_code == 0:
            score = 20  # Bad — no code at all
            finding = 'No code examples found in any page'
        else:
            ratio = pages_with_complete_code / pages_with_code
            score = round(ratio * 100)
            finding = f'{pages_with_complete_code}/{pages_with_code} pages have complete code examples (with imports & language tags)'

        return RuleResult(
            rule_id=4,
            name='Complete, Runnable Code Examples',
            short_name='complete_code',
            category='code_executability',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=pages_with_code,
            pages_passing=pages_with_complete_code,
        )

    def _rule_05_explicit_language(self, pages: list) -> RuleResult:
        """Rule 5: Explicit over implicit — no vague language."""
        vague_patterns = re.compile(
            r'\b(typically|usually|simply|obviously|you\s+may\s+want\s+to|'
            r'it\s+works\s+like|as\s+you\s+might\s+expect|you\s+just\s+need\s+to|'
            r'it\'s\s+easy\s+to)\b',
            re.IGNORECASE
        )

        passing = 0
        for page in pages:
            content = page.content or ''
            matches = vague_patterns.findall(content)
            # Allow up to 2 instances per page
            if len(matches) <= 2:
                passing += 1

        score = round(passing / len(pages) * 100) if pages else 0
        return RuleResult(
            rule_id=5,
            name='Explicit Over Implicit',
            short_name='explicit_language',
            category='accuracy',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(pages)} pages use precise, explicit language',
            pages_checked=len(pages),
            pages_passing=passing,
        )

    def _rule_06_error_docs(self, pages: list) -> RuleResult:
        """Rule 6: First-class error documentation."""
        error_patterns = re.compile(
            r'\b(error\s+code|status\s+code|error\s+message|troubleshoot|'
            r'common\s+errors|error\s+handling|exception|4[0-9]{2}|5[0-9]{2})\b',
            re.IGNORECASE
        )
        fix_patterns = re.compile(
            r'\b(fix|solution|resolve|how\s+to\s+fix|workaround|remedy|'
            r'recovery|retry|fallback)\b',
            re.IGNORECASE
        )

        has_error_docs = False
        has_fixes = False
        for page in pages:
            content = page.content or ''
            if error_patterns.search(content):
                has_error_docs = True
                if fix_patterns.search(content):
                    has_fixes = True
                    break

        if has_error_docs and has_fixes:
            score = 85
            finding = 'Error documentation found with resolution steps'
        elif has_error_docs:
            score = 45
            finding = 'Error codes mentioned but no structured fix/resolution docs'
        else:
            score = 15
            finding = 'No error documentation found — agents can\'t help users debug'

        return RuleResult(
            rule_id=6,
            name='First-Class Error Documentation',
            short_name='error_docs',
            category='code_executability',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=1 if has_fixes else 0,
        )

    def _rule_07_consistent_terminology(self, pages: list, all_content_lower: str) -> RuleResult:
        """Rule 7: Consistent terminology across all pages."""
        term_groups = [
            (['user', 'account', 'customer', 'client', 'member'], 'user entity'),
            (['workspace', 'organization', 'org', 'team', 'project'], 'workspace entity'),
            (['token', 'api key', 'secret', 'credential'], 'authentication credential'),
            (['endpoint', 'route', 'path'], 'API endpoint'),
        ]

        conflicts = 0
        total_groups = 0
        for terms, label in term_groups:
            found = [t for t in terms if re.search(r'\b' + re.escape(t) + r'\b', all_content_lower)]
            if len(found) >= 2:
                total_groups += 1
                conflicts += 1
            elif len(found) == 1:
                total_groups += 1

        if total_groups == 0:
            score = 80  # Neutral
            finding = 'Limited terminology to evaluate'
        else:
            consistency_ratio = (total_groups - conflicts) / total_groups
            score = round(consistency_ratio * 100)
            if conflicts > 0:
                finding = f'{conflicts} terminology conflict(s) detected — inconsistent terms for the same concepts'
            else:
                finding = 'Terminology is consistent across all pages'

        return RuleResult(
            rule_id=7,
            name='Consistent Terminology',
            short_name='terminology',
            category='accuracy',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=len(pages) - conflicts,
        )

    def _rule_08_frontmatter(self, pages: list) -> RuleResult:
        """Rule 8: Frontmatter metadata on every page."""
        passing = 0
        for page in pages:
            content = (page.content or '').strip()
            # Check for YAML frontmatter or meta description
            has_frontmatter = content.startswith('---')
            has_meta_desc = page.description and len(page.description) > 10
            has_title = page.title and len(page.title) > 3
            if has_frontmatter or (has_meta_desc and has_title):
                passing += 1

        score = round(passing / len(pages) * 100) if pages else 0
        return RuleResult(
            rule_id=8,
            name='Page Metadata (Frontmatter)',
            short_name='frontmatter',
            category='context_utilization',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(pages)} pages have adequate metadata (title + description or frontmatter)',
            pages_checked=len(pages),
            pages_passing=passing,
        )

    def _rule_09_prerequisites(self, pages: list) -> RuleResult:
        """Rule 9: Prerequisites stated up front."""
        prereq_patterns = re.compile(
            r'\b(prerequisite|before\s+you\s+begin|requirements?|what\s+you\s+need|'
            r'before\s+starting|you\'ll\s+need|make\s+sure\s+you\s+have)\b',
            re.IGNORECASE
        )

        # Only check how-to / guide / tutorial pages
        how_to_pages = [p for p in pages if any(
            kw in (p.title or '').lower()
            for kw in ['how', 'guide', 'tutorial', 'start', 'setup', 'install', 'quick']
        )]

        if not how_to_pages:
            how_to_pages = pages  # Check all if no obvious how-to pages

        passing = sum(
            1 for p in how_to_pages
            if prereq_patterns.search(p.content or '')
        )

        score = round(passing / len(how_to_pages) * 100) if how_to_pages else 0
        return RuleResult(
            rule_id=9,
            name='Prerequisites Stated Up Front',
            short_name='prerequisites',
            category='citation_quality',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(how_to_pages)} how-to/guide pages state prerequisites explicitly',
            pages_checked=len(how_to_pages),
            pages_passing=passing,
        )

    def _rule_10_expected_outputs(self, pages: list) -> RuleResult:
        """Rule 10: Expected outputs shown (not just inputs)."""
        output_patterns = re.compile(
            r'\b(response|output|returns?|result|expected\s+output|'
            r'example\s+response|sample\s+response|will\s+return)\b',
            re.IGNORECASE
        )

        pages_with_code = [p for p in pages if p.code_blocks and len(p.code_blocks) > 0]
        if not pages_with_code:
            score = 50
            finding = 'No code examples to check for expected outputs'
        else:
            passing = sum(
                1 for p in pages_with_code
                if output_patterns.search(p.content or '')
            )
            score = round(passing / len(pages_with_code) * 100)
            finding = f'{passing}/{len(pages_with_code)} pages with code also show expected outputs'

        return RuleResult(
            rule_id=10,
            name='Expected Outputs Documented',
            short_name='expected_outputs',
            category='citation_quality',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages_with_code) if pages_with_code else 0,
            pages_passing=passing if pages_with_code else 0,
        )

    def _rule_11_cross_references(self, pages: list) -> RuleResult:
        """Rule 11: Cross-references with full context (not 'click here')."""
        bad_link_patterns = re.compile(
            r'\b(click\s+here|see\s+here|learn\s+more|read\s+more|more\s+info)\b',
            re.IGNORECASE
        )

        pages_with_links = [p for p in pages if p.links and len(p.links) > 0]
        passing = 0
        for page in pages_with_links:
            content = page.content or ''
            if not bad_link_patterns.search(content):
                passing += 1

        if not pages_with_links:
            score = 60
            finding = 'No internal links found — pages may be isolated'
        else:
            score = round(passing / len(pages_with_links) * 100)
            finding = f'{passing}/{len(pages_with_links)} pages use descriptive link text (no "click here")'

        return RuleResult(
            rule_id=11,
            name='Cross-References with Context',
            short_name='cross_refs',
            category='context_utilization',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages_with_links),
            pages_passing=passing,
        )

    def _rule_12_content_separation(self, pages: list) -> RuleResult:
        """Rule 12: Separate conceptual / how-to / reference content."""
        concept_markers = re.compile(r'\b(overview|concept|what\s+is|introduction|about)\b', re.IGNORECASE)
        howto_markers = re.compile(r'\b(how\s+to|guide|tutorial|step[\s-]+by[\s-]+step|walkthrough)\b', re.IGNORECASE)
        ref_markers = re.compile(r'\b(reference|api\s+ref|endpoint|schema|specification)\b', re.IGNORECASE)

        types_found = set()
        for page in pages:
            title = (page.title or '') + ' ' + (page.content or '')[:200]
            if concept_markers.search(title):
                types_found.add('conceptual')
            if howto_markers.search(title):
                types_found.add('how-to')
            if ref_markers.search(title):
                types_found.add('reference')

        score = min(100, len(types_found) * 35)
        finding = f"Content types detected: {', '.join(types_found) if types_found else 'unclear'}"

        return RuleResult(
            rule_id=12,
            name='Content Type Separation',
            short_name='content_types',
            category='accuracy',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=len(types_found),
        )

    def _rule_13_version_clarity(self, pages: list) -> RuleResult:
        """Rule 13: Version clarity — API/SDK version stated clearly."""
        version_patterns = re.compile(
            r'\b(v\d+\.?\d*|version\s+\d|api\s+v\d|sdk\s+v\d|'
            r'deprecated|sunset|migration|breaking\s+change)\b',
            re.IGNORECASE
        )

        passing = sum(
            1 for p in pages
            if version_patterns.search(p.content or '')
        )

        score = round(passing / len(pages) * 100) if pages else 0
        # Cap at 90 because we can't verify correctness
        score = min(score, 90)
        return RuleResult(
            rule_id=13,
            name='Version Clarity',
            short_name='versioning',
            category='accuracy',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(pages)} pages include version information',
            pages_checked=len(pages),
            pages_passing=passing,
        )

    def _rule_14_decision_docs(self, pages: list, all_content_lower: str) -> RuleResult:
        """Rule 14: Decision documentation ('when to use X vs Y')."""
        decision_patterns = re.compile(
            r'\b(when\s+to\s+use|vs\.?|versus|compared?\s+to|comparison|'
            r'trade[\s-]?offs?|which\s+should|differences?\s+between)\b',
            re.IGNORECASE
        )

        has_decision_docs = bool(decision_patterns.search(all_content_lower))
        score = 75 if has_decision_docs else 30
        finding = ('Decision/comparison documentation found'
                   if has_decision_docs
                   else 'No decision documentation found (e.g., "when to use X vs Y")')

        return RuleResult(
            rule_id=14,
            name='Decision Documentation',
            short_name='decision_docs',
            category='citation_quality',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=1 if has_decision_docs else 0,
        )

    def _rule_15_safety_boundaries(self, pages: list, all_content_lower: str) -> RuleResult:
        """Rule 15: Safety boundaries documented."""
        safety_patterns = re.compile(
            r'\b(warning|caution|danger|irreversible|destructive|'
            r'cannot\s+be\s+undone|permanent|rate\s+limit|quota|'
            r'billing|side\s+effect|dry[\s-]?run)\b',
            re.IGNORECASE
        )

        passing = sum(
            1 for p in pages
            if safety_patterns.search(p.content or '')
        )

        # Many pages won't need safety docs, so score generously
        has_any = passing > 0
        score = 80 if has_any else 40
        finding = (f'{passing} page(s) document safety boundaries (warnings, limits, irreversible actions)'
                   if has_any
                   else 'No safety boundaries documented (rate limits, destructive actions, etc.)')

        return RuleResult(
            rule_id=15,
            name='Safety Boundaries',
            short_name='safety',
            category='structure',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=passing,
        )

    def _rule_16_no_anti_patterns(self, pages: list) -> RuleResult:
        """Rule 16: No anti-patterns (marketing language, 'contact support')."""
        antipattern_re = re.compile(
            r'\b(seamlessly|world[\s-]?class|next[\s-]?generation|cutting[\s-]?edge|'
            r'unlock|leverage|synergy|revolutionary|best[\s-]?in[\s-]?class|'
            r'game[\s-]?changing|disruptive|supercharge|contact\s+support)\b',
            re.IGNORECASE
        )

        passing = 0
        for page in pages:
            content = page.content or ''
            matches = antipattern_re.findall(content)
            if len(matches) == 0:
                passing += 1

        score = round(passing / len(pages) * 100) if pages else 0
        return RuleResult(
            rule_id=16,
            name='No Anti-Patterns',
            short_name='no_antipatterns',
            category='structure',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(pages)} pages are free of marketing language and anti-patterns',
            pages_checked=len(pages),
            pages_passing=passing,
        )

    def _rule_17_retrieval_chunks(self, pages: list) -> RuleResult:
        """Rule 17: Optimized for retrieval chunks (good heading density, reasonable section size)."""
        good_pages = 0
        for page in pages:
            content = page.content or ''
            word_count = len(content.split())
            heading_count = len(page.heading_hierarchy or [])

            # Good: reasonable length with enough headings
            if word_count < 100:
                continue  # Too short
            heading_density = heading_count / (word_count / 500)  # Headings per 500 words
            if heading_density >= 0.8 and word_count <= 5000:
                good_pages += 1
            elif heading_density >= 0.5:
                good_pages += 0.5  # Partial credit

        score = round(good_pages / len(pages) * 100) if pages else 0
        return RuleResult(
            rule_id=17,
            name='Retrieval-Chunk Optimized',
            short_name='chunking',
            category='context_utilization',
            score=score,
            status=self._score_to_status(score),
            finding=f'{int(good_pages)}/{len(pages)} pages have good heading density for RAG chunking',
            pages_checked=len(pages),
            pages_passing=int(good_pages),
        )

    def _rule_18_intent_before_mechanics(self, pages: list) -> RuleResult:
        """Rule 18: State intent before mechanics (explain WHY then HOW)."""
        # Check if pages start with purpose/context before diving into code
        good_pages = 0
        for page in pages:
            content = (page.content or '')[:500].lower()
            # Good sign: starts with purpose/context language
            intent_first = any(kw in content for kw in [
                'this guide', 'this page', 'in this', 'learn how',
                'you can use', 'allows you to', 'enables you to',
                'to receive', 'to send', 'to create', 'to configure',
                'purpose', 'overview', 'what you\'ll',
            ])
            if intent_first:
                good_pages += 1

        score = round(good_pages / len(pages) * 100) if pages else 0
        return RuleResult(
            rule_id=18,
            name='Intent Before Mechanics',
            short_name='intent_first',
            category='accuracy',
            score=score,
            status=self._score_to_status(score),
            finding=f'{good_pages}/{len(pages)} pages explain intent/purpose before diving into mechanics',
            pages_checked=len(pages),
            pages_passing=good_pages,
        )

    def _rule_19_state_transitions(self, pages: list, all_content_lower: str) -> RuleResult:
        """Rule 19: Document state transitions & lifecycle."""
        state_patterns = re.compile(
            r'\b(state|lifecycle|status|transition|pending|active|'
            r'completed|failed|draft|published|archived|workflow)\b',
            re.IGNORECASE
        )
        arrow_patterns = re.compile(r'(→|->|=>)')

        has_states = bool(state_patterns.search(all_content_lower))
        has_transitions = bool(arrow_patterns.search(all_content_lower))

        if has_states and has_transitions:
            score = 85
            finding = 'State transitions and lifecycle documentation found'
        elif has_states:
            score = 55
            finding = 'State/status concepts mentioned but no clear transition documentation'
        else:
            score = 40  # Not all docs need this
            finding = 'No state transition or lifecycle documentation found'

        return RuleResult(
            rule_id=19,
            name='State Transitions & Lifecycle',
            short_name='state_transitions',
            category='citation_quality',
            score=score,
            status=self._score_to_status(score),
            finding=finding,
            pages_checked=len(pages),
            pages_passing=1 if has_states and has_transitions else 0,
        )

    def _rule_20_callouts(self, pages: list) -> RuleResult:
        """Rule 20: Callouts & admonitions (warnings, tips, notes)."""
        callout_patterns = re.compile(
            r'(⚠️|❌|💡|ℹ️|warning|caution|note|tip|important|info|'
            r':::warning|:::note|:::tip|:::info|'
            r'>\s*\*\*(warning|note|tip|important))',
            re.IGNORECASE
        )

        passing = sum(
            1 for p in pages
            if callout_patterns.search(p.content or '')
        )

        score = round(passing / len(pages) * 100) if pages else 0
        # Boost score since not every page needs callouts
        score = min(100, score + 20)
        return RuleResult(
            rule_id=20,
            name='Callouts & Admonitions',
            short_name='callouts',
            category='structure',
            score=score,
            status=self._score_to_status(score),
            finding=f'{passing}/{len(pages)} pages use callouts/admonitions (warnings, tips, notes)',
            pages_checked=len(pages),
            pages_passing=passing,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _score_to_status(self, score: int) -> str:
        if score >= 70:
            return 'pass'
        elif score >= 40:
            return 'warning'
        return 'fail'

    def _generate_top_issues(self, rules: List[RuleResult]) -> List[dict]:
        """Generate top issues from failing/warning rules, sorted by severity."""
        issues = []
        for r in sorted(rules, key=lambda x: x.score):
            if r.status in ('fail', 'warning'):
                severity = 'high' if r.score < 40 else 'medium' if r.score < 70 else 'low'
                issues.append({
                    'category': r.category,
                    'title': f'Rule {r.rule_id}: {r.name} — {r.finding}',
                    'severity': severity,
                    'rule_id': r.rule_id,
                    'rule_name': r.short_name,
                    'score': r.score,
                })

        if not issues:
            issues.append({
                'category': 'optimization',
                'title': 'All rules passing — minor optimizations available for a perfect score',
                'severity': 'low',
                'rule_id': 0,
                'rule_name': 'all_passing',
                'score': 100,
            })

        return issues[:5]  # Top 5 issues

    def _empty_result(self) -> RuleAnalysisResult:
        return RuleAnalysisResult(
            rule_results=[],
            overall_score=0,
            grade='F',
            components={k: 0 for k in COMPONENT_WEIGHTS},
            top_issues=[{
                'category': 'crawling',
                'title': 'No pages could be analyzed',
                'severity': 'high',
                'rule_id': 0,
                'rule_name': 'no_pages',
                'score': 0,
            }],
        )
