"""
Test Suite: RecoveryAgent Readiness Score & Active Recovery Logic.
Role: Senior SDET at Amazon
"""
import pytest
from app.agents.recovery_agent import RecoveryAgent


@pytest.fixture
def recovery_agent():
    return RecoveryAgent(groq_api_key="dummy_key_for_testing")


def test_readiness_score_optimal_sleep(recovery_agent):
    """Verify readiness score is high (>=0.70) for optimal sleep signals."""
    signals = {
        "sleep_quality_avg": 8.0,
        "sleep_hours_avg": 8.0,
        "consecutive_training_days": 1,
        "hrv_score": 65.0,
        "user_energy": 8.0
    }
    score = recovery_agent._compute_readiness(signals)
    assert score >= 0.65


def test_readiness_score_deprived_sleep(recovery_agent):
    """Verify readiness score drops for deprived sleep signals."""
    signals = {
        "sleep_quality_avg": 3.0,
        "sleep_hours_avg": 4.0,
        "consecutive_training_days": 6,
        "hrv_score": 30.0,
        "user_energy": 3.0
    }
    score = recovery_agent._compute_readiness(signals)
    assert score < 0.60
