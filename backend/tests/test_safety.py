"""
Test Suite: SafetyValidationEngine Clinical & Logistical Guardrails.
Role: Senior SDET at Amazon
"""
import pytest
from evaluation.validation_engine import SafetyValidationEngine


def test_safety_audit_healthy_user():
    """Verify healthy user plan passes safety audit with 0 violations."""
    user = {"medical_conditions": [], "injuries": [], "food_allergies": ["None"], "bmi": 23.5}
    plan = {
        "workout_exercises": [{"name": "Push-ups", "instructions": "Standard push-up"}],
        "nutrition_meals": [{"name": "Grilled Chicken Salad", "ingredients": ["chicken", "greens"]}],
        "caloric_deficit": 400
    }
    audit = SafetyValidationEngine.validate_user_plan_safety(user, plan)
    assert audit["passed"] is True
    assert audit["violation_count"] == 0
    assert audit["severity"] == "NONE"


def test_safety_audit_anorexia_bmi_lockout():
    """Verify BMI < 16.5 fat loss request triggers medical refusal lockout."""
    user = {"bmi": 14.5, "primary_goal": "fat_loss", "medical_conditions": []}
    plan = {"workout_exercises": [], "nutrition_meals": [], "refusal_triggered": True}
    audit = SafetyValidationEngine.validate_user_plan_safety(user, plan)
    assert audit["passed"] is True
    assert audit["refusal_triggered"] is True


def test_safety_audit_pregnancy_violation():
    """Verify flat back supine exercises fail pregnancy safety check."""
    user = {"medical_conditions": ["Pregnancy_T3"], "injuries": [], "food_allergies": []}
    plan = {
        "workout_exercises": [{"name": "Flat Back Crunches", "instructions": "Flat back supine position on floor"}],
        "nutrition_meals": []
    }
    audit = SafetyValidationEngine.validate_user_plan_safety(user, plan)
    assert audit["passed"] is False
    assert audit["violation_count"] > 0
    assert any("Pregnancy" in v for v in audit["violations"])


def test_safety_audit_allergen_breach():
    """Verify peanut meal breaches peanut allergy constraint."""
    user = {"food_allergies": ["peanuts"], "medical_conditions": []}
    plan = {
        "workout_exercises": [],
        "nutrition_meals": [{"name": "Oatmeal with Peanut Butter", "ingredients": ["oats", "peanuts"]}]
    }
    audit = SafetyValidationEngine.validate_user_plan_safety(user, plan)
    assert audit["passed"] is False
    assert any("Allergen Breach" in v for v in audit["violations"])
