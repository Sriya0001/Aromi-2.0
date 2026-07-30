"""
Test Suite: PlanGenerationService End-to-End Orchestration.
Role: Senior SDET at Amazon
"""
import pytest
import asyncio
from unittest.mock import MagicMock
from app.services.plan_generation_service import PlanGenerationService, GeneratedPlanResponse


def test_plan_generation_anorexia_refusal():
    """Verify PlanGenerationService returns medical refusal response when BMI < 16.5."""
    db_mock = MagicMock()
    service = PlanGenerationService(db_mock)

    synthetic_user = {
        "user_id": 999,
        "bmi": 14.2,
        "primary_goal": "fat_loss",
        "medical_conditions": [],
        "injuries": []
    }

    res = asyncio.run(service.generate_complete_plan(user_id=999, user_profile_override=synthetic_user))
    assert isinstance(res, GeneratedPlanResponse)
    assert res.refusal_triggered is True
    assert res.planner_state == "MEDICAL_REFUSAL_LOCKOUT"
    assert res.confidence_score == 1.0


def test_plan_generation_standard_flow():
    """Verify PlanGenerationService completes standard generation flow."""
    db_mock = MagicMock()
    service = PlanGenerationService(db_mock)

    synthetic_user = {
        "user_id": 100,
        "bmi": 23.5,
        "primary_goal": "muscle_gain",
        "medical_conditions": [],
        "injuries": []
    }

    res = asyncio.run(service.generate_complete_plan(user_id=100, user_profile_override=synthetic_user))
    assert isinstance(res, GeneratedPlanResponse)
    assert res.user_id == 100
    assert res.planner_state in ["ACTIVE_NORMAL", "PROGRESSIVE_OVERLOAD"]
    assert res.confidence_score > 0.5
