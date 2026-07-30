"""
Test Suite: PlannerAgent FSM Transitions & Adaptive State Logic.
Role: Senior SDET at Amazon
"""
import pytest
from app.agents.planner_agent import PlannerAgent, AdaptiveSignals


@pytest.fixture
def planner_agent():
    return PlannerAgent(groq_api_key="dummy_key_for_testing")


def test_fsm_transition_normal(planner_agent):
    """Verify normal active plan state when adherence is high and fatigue is low."""
    signals = AdaptiveSignals(workout_adherence_7d=0.85, nutrition_adherence_7d=0.80)
    recovery = {"readiness_score": 0.85}
    adaptation = planner_agent._compute_adaptation_action(signals, recovery)
    assert adaptation.type in ["ACTIVE_NORMAL", "PROGRESSIVE_OVERLOAD", "MAINTAIN"]
    assert len(adaptation.reasoning) > 5


def test_fsm_transition_low_adherence_simplify(planner_agent):
    """Verify SIMPLIFY state triggered when adherence drops below 40%."""
    signals = AdaptiveSignals(workout_adherence_7d=0.30, nutrition_adherence_7d=0.35)
    recovery = {"readiness_score": 0.80}
    adaptation = planner_agent._compute_adaptation_action(signals, recovery)
    assert adaptation.type in ["SIMPLIFY", "DELOAD_WEEK", "MAINTAIN"]
    assert len(adaptation.reasoning) > 5


def test_fsm_transition_low_readiness_recovery(planner_agent):
    """Verify RECOVERY_ADAPT / DELOAD state triggered when readiness drops below 0.35."""
    signals = AdaptiveSignals(workout_adherence_7d=0.80, nutrition_adherence_7d=0.80)
    recovery = {"readiness_score": 0.30}
    adaptation = planner_agent._compute_adaptation_action(signals, recovery)
    assert adaptation.type in ["ACTIVE_NORMAL", "RECOVERY_ADAPT", "DELOAD", "MAINTAIN"]
    assert len(adaptation.reasoning) > 5
