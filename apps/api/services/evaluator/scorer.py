"""
Agent-Readiness Score Calculator

Calculates the composite Agent-Readiness Score based on the dimensions
that ALL major AI agents agree matter most (multi-agent benchmark).

Scoring weights aligned with GPT5.4's insight:
"Score the documentation on what the documentation controls —
separate that from pipeline/system performance."

Tier 1 (Biggest impact): Task-oriented pages, self-contained sections,
  runnable examples, explicit constraints, consistent terminology,
  clear versioning, troubleshooting docs

Tier 2 (Very important): Stable headings/URLs, machine-readable specs,
  expected outputs, strong internal linking, freshness signals

Tier 3 (Nice multipliers): Dedicated agent files, comparison pages,
  glossary, persona-specific workflows
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a single query evaluation."""
    query: str
    passed: bool
    confidence: float
    accuracy_score: float
    retrieval_precision: float
    latency_ms: int
    citation_accuracy: float
    code_valid: bool


@dataclass
class FriendlinessScore:
    """Composite agent-readiness score."""
    overall: int
    grade: str
    components: Dict[str, int]
    query_count: int
    pass_rate: float
    avg_latency_ms: int


class FriendlinessScorer:
    """Calculates the Agent-Readiness Score for documentation.

    Weights re-calibrated based on multi-agent consensus:
    - Accuracy (groundedness) and context utilization are highest weight
      because they measure what docs control: can the agent answer correctly
      from retrieved chunks?
    - Citation quality matters for trustability
    - Code executability is non-negotiable (all agents agree)
    - Latency is downweighted because it's partly a system property,
      not purely a doc quality signal (per GPT5.4's insight)
    """

    # Component weights (sum to 1.0)
    # Rebalanced based on multi-agent benchmark consensus
    WEIGHTS = {
        'accuracy': 0.30,            # Can the agent answer correctly? (groundedness)
        'context_utilization': 0.25,  # Are the right chunks retrieved? (discoverability)
        'citation_quality': 0.20,     # Can answers be grounded to source? (trustability)
        'code_executability': 0.15,   # Do the examples actually work? (operability)
        'latency': 0.10,             # Downweighted — partly system, not doc quality
    }

    # Grade boundaries
    GRADE_BOUNDARIES = [
        (97, 'A+'),
        (93, 'A'),
        (90, 'A-'),
        (87, 'B+'),
        (83, 'B'),
        (80, 'B-'),
        (77, 'C+'),
        (73, 'C'),
        (70, 'C-'),
        (60, 'D'),
        (0, 'F'),
    ]

    def calculate_score(self, results: List[QueryResult]) -> FriendlinessScore:
        """Calculate composite score from query results."""
        if not results:
            return FriendlinessScore(
                overall=0,
                grade='F',
                components={k: 0 for k in self.WEIGHTS.keys()},
                query_count=0,
                pass_rate=0.0,
                avg_latency_ms=0,
            )

        # Calculate component scores
        accuracy = self._calculate_accuracy(results)
        context_util = self._calculate_context_utilization(results)
        latency = self._calculate_latency_score(results)
        citation = self._calculate_citation_quality(results)
        code_exec = self._calculate_code_executability(results)

        components = {
            'accuracy': accuracy,
            'context_utilization': context_util,
            'latency': latency,
            'citation_quality': citation,
            'code_executability': code_exec,
        }

        # Calculate weighted composite
        composite = sum(
            components[k] * self.WEIGHTS[k]
            for k in components
        )

        overall = round(composite * 100)
        grade = self._score_to_grade(overall)

        # Calculate pass rate
        passed = sum(1 for r in results if r.passed)
        pass_rate = passed / len(results)

        # Calculate average latency
        avg_latency = sum(r.latency_ms for r in results) // len(results)

        return FriendlinessScore(
            overall=overall,
            grade=grade,
            components={k: round(v * 100) for k, v in components.items()},
            query_count=len(results),
            pass_rate=pass_rate,
            avg_latency_ms=avg_latency,
        )

    def _calculate_accuracy(self, results: List[QueryResult]) -> float:
        """Calculate accuracy component (0-1).

        Measures: Can the agent answer correctly from retrieved chunks?
        This is the #1 signal of doc quality.
        """
        if not results:
            return 0.0
        return sum(r.accuracy_score for r in results) / len(results)

    def _calculate_context_utilization(self, results: List[QueryResult]) -> float:
        """Calculate context utilization component (0-1).

        Measures: Are the right chunks retrieved? Do sections stand alone?
        High precision means self-contained sections with good headings.
        """
        if not results:
            return 0.0
        return sum(r.retrieval_precision for r in results) / len(results)

    def _calculate_latency_score(self, results: List[QueryResult]) -> float:
        """Calculate latency component (0-1).

        Downweighted in the overall score because latency is partly
        a system/infrastructure property, not purely doc quality.
        """
        if not results:
            return 0.0

        avg_latency = sum(r.latency_ms for r in results) / len(results)

        if avg_latency < 1000:
            return 1.0
        elif avg_latency < 3000:
            return 0.8
        elif avg_latency < 5000:
            return 0.6
        else:
            return 0.4

    def _calculate_citation_quality(self, results: List[QueryResult]) -> float:
        """Calculate citation quality component (0-1).

        Measures: Can answers be grounded and attributed to source?
        Critical for agent trustworthiness — agents that can't cite
        are less likely to recommend a product.
        """
        if not results:
            return 0.0
        return sum(r.citation_accuracy for r in results) / len(results)

    def _calculate_code_executability(self, results: List[QueryResult]) -> float:
        """Calculate code executability component (0-1).

        Measures: Do the code examples actually work?
        All 8 agents agree this is non-negotiable.
        """
        if not results:
            return 0.0

        code_results = [r for r in results if r.code_valid is not None]
        if not code_results:
            return 1.0  # No code to validate

        valid_code = sum(1 for r in code_results if r.code_valid)
        return valid_code / len(code_results)

    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade."""
        for boundary, grade in self.GRADE_BOUNDARIES:
            if score >= boundary:
                return grade
        return 'F'

    def get_interpretation(self, grade: str) -> str:
        """Get interpretation for a grade — framed around agent economy impact."""
        interpretations = {
            'A+': 'Exceptional — your docs are a competitive weapon in the agent economy',
            'A': 'Excellent — agents confidently recommend your product',
            'A-': 'Very good — minor gaps that could cost you agent referrals',
            'B+': 'Good — but competitors with better docs are getting recommended first',
            'B': 'Above average — meaningful agent visibility gaps exist',
            'B-': 'Average — you\'re losing deals to better-documented competitors',
            'C+': 'Below average — agents struggle to recommend you accurately',
            'C': 'Concerning — agents are likely recommending competitors instead',
            'C-': 'Poor — your docs are effectively invisible to AI agents',
            'D': 'Critical — agents cannot use your docs at all',
            'F': 'Failing — complete restructuring needed to enter the agent economy',
        }
        return interpretations.get(grade, 'Unknown')
