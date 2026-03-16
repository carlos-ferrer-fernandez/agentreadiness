"""Tests for the FriendlinessScorer."""

import pytest
from services.evaluator.scorer import FriendlinessScorer, QueryResult


def _make_result(**overrides) -> QueryResult:
    defaults = {
        "query": "test query",
        "passed": True,
        "confidence": 0.9,
        "accuracy_score": 0.85,
        "retrieval_precision": 0.8,
        "latency_ms": 500,
        "citation_accuracy": 0.9,
        "code_valid": True,
    }
    defaults.update(overrides)
    return QueryResult(**defaults)


class TestFriendlinessScorer:
    def test_empty_results_returns_zero(self):
        scorer = FriendlinessScorer()
        score = scorer.calculate_score([])
        assert score.overall == 0
        assert score.grade == "F"
        assert score.query_count == 0

    def test_perfect_results(self):
        scorer = FriendlinessScorer()
        results = [_make_result(
            accuracy_score=1.0,
            retrieval_precision=1.0,
            latency_ms=500,
            citation_accuracy=1.0,
            code_valid=True,
        )] * 10

        score = scorer.calculate_score(results)
        assert score.overall >= 95
        assert score.grade in ("A+", "A")
        assert score.query_count == 10
        assert score.pass_rate == 1.0

    def test_low_accuracy_lowers_score(self):
        scorer = FriendlinessScorer()
        results = [_make_result(accuracy_score=0.3)] * 10
        score = scorer.calculate_score(results)
        assert score.overall < 80

    def test_grade_boundaries(self):
        scorer = FriendlinessScorer()
        assert scorer._score_to_grade(97) == "A+"
        assert scorer._score_to_grade(93) == "A"
        assert scorer._score_to_grade(83) == "B"
        assert scorer._score_to_grade(70) == "C-"
        assert scorer._score_to_grade(60) == "D"
        assert scorer._score_to_grade(0) == "F"

    def test_latency_scoring(self):
        scorer = FriendlinessScorer()
        fast = [_make_result(latency_ms=500)] * 5
        slow = [_make_result(latency_ms=6000)] * 5

        fast_score = scorer.calculate_score(fast)
        slow_score = scorer.calculate_score(slow)
        assert fast_score.overall > slow_score.overall

    def test_interpretation(self):
        scorer = FriendlinessScorer()
        assert "Exceptional" in scorer.get_interpretation("A+")
        assert "Failing" in scorer.get_interpretation("F")
        assert scorer.get_interpretation("Z") == "Unknown"

    def test_pass_rate_calculation(self):
        scorer = FriendlinessScorer()
        results = [
            _make_result(passed=True),
            _make_result(passed=True),
            _make_result(passed=False),
        ]
        score = scorer.calculate_score(results)
        assert abs(score.pass_rate - 2 / 3) < 0.01
