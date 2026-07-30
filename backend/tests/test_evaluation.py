"""
Test Suite: EvaluationMetricsCalculator Scientific Metrics.
Role: Senior SDET at Amazon
"""
import pytest
from evaluation.metrics import EvaluationMetricsCalculator


def test_jaccard_distance_identical_sets():
    """Verify Jaccard distance is 0.0 for identical exercise sets."""
    set_a = {"push-ups", "squats"}
    set_b = {"push-ups", "squats"}
    dist = EvaluationMetricsCalculator.compute_jaccard_distance(set_a, set_b)
    assert dist == 0.0


def test_jaccard_distance_disjoint_sets():
    """Verify Jaccard distance is 1.0 for completely disjoint sets."""
    set_a = {"push-ups", "squats"}
    set_b = {"pull-ups", "lunges"}
    dist = EvaluationMetricsCalculator.compute_jaccard_distance(set_a, set_b)
    assert dist == 1.0


def test_summary_statistics_computation():
    """Verify Mean, Median, P95, P99, and 95% CI calculation accuracy."""
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    stats = EvaluationMetricsCalculator.compute_summary_statistics(latencies)
    assert stats["mean"] == 55.0
    assert stats["median"] == 55.0
    assert stats["p95"] > 90.0
    assert stats["ci_95_low"] < 55.0
    assert stats["ci_95_high"] > 55.0
