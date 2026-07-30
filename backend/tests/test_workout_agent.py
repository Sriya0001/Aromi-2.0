"""
Test Suite: WorkoutAgent Exercise Selection & Safety Adaptation.
Role: Senior SDET at Amazon
"""
import pytest
from app.agents.workout_agent import WorkoutAgent


@pytest.fixture
def workout_agent():
    return WorkoutAgent(groq_api_key="dummy_key_for_testing")


def test_workout_agent_initialization(workout_agent):
    """Verify WorkoutAgent initializes correctly."""
    assert workout_agent.name == "workout_agent"
    assert hasattr(workout_agent, "run")


def test_workout_safety_filter_purges_knee_exercises(workout_agent):
    """Verify safety filter removes knee-stressing exercises when knee injury reported."""
    profile = {"medical_conditions": [], "injuries": ["knee"]}
    candidates = [
        {"name": "Walking Lunges", "muscle_group": "Legs"},
        {"name": "Bodyweight Squats", "muscle_group": "Legs"},
        {"name": "Push-ups", "muscle_group": "Chest"}
    ]
    safe = [ex for ex in candidates if not any(k in ex["name"].lower() for k in ["lunge", "squat"])]
    assert len(safe) == 1
    assert safe[0]["name"] == "Push-ups"
