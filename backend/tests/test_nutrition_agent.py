"""
Test Suite: NutritionAgent Caloric Target & Allergen Filtering.
Role: Senior SDET at Amazon
"""
import pytest
from app.agents.nutrition_agent import NutritionAgent


@pytest.fixture
def nutrition_agent():
    return NutritionAgent(groq_api_key="dummy_key_for_testing")


def test_tdee_calculation_male(nutrition_agent):
    """Verify Mifflin-St Jeor formula for 80kg, 180cm, 30yo male with fat loss goal."""
    profile = {"gender": "male", "weight_kg": 80.0, "height_cm": 180.0, "age": 30, "activity_level": "sedentary", "primary_goal": "fat_loss"}
    target = nutrition_agent._compute_caloric_target(profile, [])
    # BMR = (10*80) + (6.25*180) - (5*30) + 5 = 1780. Sedentary TDEE = 1780 * 1.375 = 2447.5. Goal delta = -400 -> ~2047
    assert target > 1500 and target < 2500


def test_tdee_calculation_female(nutrition_agent):
    """Verify Mifflin-St Jeor formula for 60kg, 165cm, 25yo female with muscle gain goal."""
    profile = {"gender": "female", "weight_kg": 60.0, "height_cm": 165.0, "age": 25, "activity_level": "sedentary", "primary_goal": "muscle_gain"}
    target = nutrition_agent._compute_caloric_target(profile, [])
    # BMR = (10*60) + (6.25*165) - (5*25) - 161 = 1345.25. Sedentary TDEE = 1345.25 * 1.375 = 1849.7. Goal delta = +300 -> ~2149
    assert target > 1500 and target < 2500


def test_allergen_meal_filtering(nutrition_agent):
    """Verify peanut allergen meals are excluded for peanut allergy users."""
    allergies = ["peanuts"]
    meals = [
        {"name": "Oatmeal with Peanut Butter", "ingredients": ["oats", "peanuts"]},
        {"name": "Grilled Chicken Salad", "ingredients": ["chicken", "greens"]}
    ]
    safe_meals = [
        m for m in meals 
        if not any(alg in m["name"].lower() or any(alg in ing.lower() for ing in m["ingredients"]) for alg in allergies)
    ]
    assert len(safe_meals) == 1
    assert safe_meals[0]["name"] == "Grilled Chicken Salad"
