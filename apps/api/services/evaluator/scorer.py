"""
Friendliness Score Calculator

Calculates the composite Friendliness Score based on multiple dimensions.
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
    """Composite friendliness score."""
    overall: int
    grade: str
    components: Dict[str, int]
    query_count: int
    pass_rate: float
    avg_latency_ms: int


class FriendlinessScorer:
    """Calculates the Friendliness Score for documentation."""
    
    # Component weights (must sum to 1.0)
    WEIGHTS = {
        'accuracy': 0.30,
        'context_utilization': 0.25,
        'latency': 0.20,
        'citation_quality': 0.15,
        'code_executability': 0.10,
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
            components={k: round(v * 100) for k, v in components.items()},  # 0-100
            query_count=len(results),
            pass_rate=pass_rate,
            avg_latency_ms=avg_latency,
        )
    
    def _calculate_accuracy(self, results: List[QueryResult]) -> float:
        """Calculate accuracy component (0-1)."""
        if not results:
            return 0.0
        
        total_accuracy = sum(r.accuracy_score for r in results)
        return total_accuracy / len(results)
    
    def _calculate_context_utilization(self, results: List[QueryResult]) -> float:
        """Calculate context utilization component (0-1)."""
        if not results:
            return 0.0
        
        total_precision = sum(r.retrieval_precision for r in results)
        return total_precision / len(results)
    
    def _calculate_latency_score(self, results: List[QueryResult]) -> float:
        """Calculate latency component (0-1).
        
        Score based on response time:
        - < 1s: 1.0
        - 1-3s: 0.8
        - 3-5s: 0.6
        - > 5s: 0.4
        """
        if not results:
            return 0.0
        
        latencies = [r.latency_ms for r in results]
        avg_latency = sum(latencies) / len(latencies)
        
        if avg_latency < 1000:
            return 1.0
        elif avg_latency < 3000:
            return 0.8
        elif avg_latency < 5000:
            return 0.6
        else:
            return 0.4
    
    def _calculate_citation_quality(self, results: List[QueryResult]) -> float:
        """Calculate citation quality component (0-1)."""
        if not results:
            return 0.0
        
        total_citation = sum(r.citation_accuracy for r in results)
        return total_citation / len(results)
    
    def _calculate_code_executability(self, results: List[QueryResult]) -> float:
        """Calculate code executability component (0-1)."""
        if not results:
            return 0.0
        
        # Count results with code blocks that are valid
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
        """Get interpretation for a grade."""
        interpretations = {
            'A+': 'Exceptional: best-in-class agent experience',
            'A': 'Excellent: strong competitive position',
            'A-': 'Very good: minor optimization opportunities',
            'B+': 'Good: some gaps relative to leaders',
            'B': 'Above average: meaningful improvement potential',
            'B-': 'Average: significant optimization needed',
            'C+': 'Below average: competitive disadvantage risk',
            'C': 'Concerning: likely losing agent recommendations',
            'C-': 'Poor: urgent improvement required',
            'D': 'Critical: effectively invisible to agents',
            'F': 'Failing: complete restructuring needed',
        }
        return interpretations.get(grade, 'Unknown')
