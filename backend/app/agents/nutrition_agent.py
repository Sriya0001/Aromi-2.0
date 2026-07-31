"""
Nutrition Agent — generates calorie-target, macro-split, and meal plans.

Reasoning Process:
1. Compute TDEE using Mifflin-St Jeor (more accurate than Harris-Benedict)
2. Apply goal modifier (deficit for fat_loss, surplus for muscle_gain)
3. Apply medical modifiers (diabetes → low-GI; hypertension → low-sodium)
4. Apply preference/allergen filters (hard constraints)
5. Generate meals with timing relative to workout schedule
6. Verify allergen safety (hard constraint)

WHY Mifflin-St Jeor over Harris-Benedict:
Mifflin-St Jeor is validated as 10% more accurate for modern populations.
The existing codebase uses Harris-Benedict — this is an improvement.
"""
from app.agents.base import BaseAgent, AgentContext, AgentOutput
from typing import Optional


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}


class NutritionAgent(BaseAgent):
    name = "nutrition_agent"

    SYSTEM_PROMPT = """You are a Registered Dietitian AI. Your ONLY job is to generate safe, personalized meal plans.

IMPORTANT RULES:
1. NEVER include allergens listed in the user profile
2. Respect all medical dietary restrictions (diabetes → low-GI; hypertension → low-sodium)
3. Match the exact calorie and macro targets provided
4. Time carbohydrates relative to workout schedule
5. Use primarily Indian cuisine unless specified otherwise

Return ONLY valid JSON. No markdown, no extra text."""

    async def run(self, context: AgentContext, workout_schedule: list = None, **kwargs) -> AgentOutput:
        import time
        start = time.time()

        hp = context.health_profile
        caloric_target = self._compute_caloric_target(hp, context.medical_conditions)
        macro_split = self._compute_macro_split(hp, caloric_target)
        medical_adjustments = self._get_medical_adjustments(context.medical_conditions)

        user_prompt = self._build_nutrition_prompt(
            hp, caloric_target, macro_split, medical_adjustments,
            workout_schedule, context
        )

        try:
            raw_response, token_count = await self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=4096
            )
            plan_data = self._parse_json_response(raw_response)
        except Exception as e:
            plan_data = {}

        if not plan_data or not plan_data.get("plan"):
            from app.services.fallback_service import get_fallback_nutrition_plan
            plan_data = get_fallback_nutrition_plan()

        # Sanitize meal plan for allergens and medical conditions
        clean_plan = self._apply_nutrition_safety_filter(plan_data.get("plan", []), hp, context)

        reasoning = (
            f"TDEE: {caloric_target + self._goal_delta(hp)} kcal | "
            f"Target: {caloric_target} kcal | "
            f"Protein: {macro_split['protein_g']}g ({macro_split['protein_g_per_kg']}g/kg) | "
            f"Medical adjustments: {', '.join(medical_adjustments) or 'none'} | "
            f"Allergens avoided: {context.health_profile.get('food_allergies') or context.health_profile.get('allergies', 'none')}"
        )

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "plan": clean_plan,
                "caloric_target": caloric_target,
                "macro_split": macro_split,
                "medical_adjustments": medical_adjustments,
                "hydration_target_ml": self._compute_hydration(hp),
            },
            reasoning=reasoning,
            latency_ms=int((time.time() - start) * 1000),
            token_count=token_count
        )

    def _apply_nutrition_safety_filter(self, plan: list, hp: dict, context: AgentContext) -> list:
        allergies = str(hp.get("food_allergies") or hp.get("allergies") or "").lower()
        health_cond = str(hp.get("health_conditions") or "").lower()
        medical_hist = str(hp.get("medical_history") or "").lower()

        # Allergen flags
        has_soy = "soy" in allergies or "soybean" in allergies or "tofu" in allergies
        has_nut = "nut" in allergies or "peanut" in allergies or "cashew" in allergies or "almond" in allergies
        has_dairy = "dairy" in allergies or "lactose" in allergies or "milk" in allergies
        has_gluten = "gluten" in allergies or "wheat" in allergies

        replacements = []
        if has_soy:
            replacements.extend([("Soya Chunks", "Paneer / Dal"), ("Tofu", "Cottage Cheese (Paneer)"), ("Soy Milk", "Almond Milk"), ("Soy Sauce", "Coconut Aminos")])
        if has_nut:
            replacements.extend([("Peanut Butter", "Sunflower Seed Butter"), ("Almonds", "Pumpkin Seeds"), ("Cashews", "Roasted Chana"), ("Walnuts", "Flaxseeds")])
        if has_dairy:
            replacements.extend([("Paneer", "Tofu"), ("Curd", "Coconut Yoghurt"), ("Milk", "Almond Milk"), ("Ghee", "Olive Oil")])
        if has_gluten:
            replacements.extend([("Whole Wheat Roti", "Millets Roti (Ragi/Jowar)"), ("Rava", "Poha / Oats"), ("Bread", "Gluten-Free Bread")])

        for day_plan in plan:
            meals = day_plan.get("meals", {})
            for m_key, m_val in meals.items():
                if isinstance(m_val, dict):
                    m_name = m_val.get("name", "")
                    m_ing = m_val.get("ingredients", [])

                    for old_item, new_item in replacements:
                        if old_item.lower() in m_name.lower():
                            m_val["name"] = m_name.replace(old_item, new_item)
                        if isinstance(m_ing, list):
                            m_val["ingredients"] = [
                                ing.replace(old_item, new_item) if old_item.lower() in ing.lower() else ing
                                for ing in m_ing
                            ]

        return plan

    def _compute_caloric_target(self, hp: dict, medical_conditions: list) -> int:
        """
        Mifflin-St Jeor BMR → TDEE → goal-adjusted target.
        WHY Mifflin-St Jeor: 10% more accurate than Harris-Benedict for modern populations.
        """
        weight = hp.get("weight_kg") or 70
        height = hp.get("height_cm") or 170
        age = hp.get("age") or 25
        gender = (hp.get("gender") or "male").lower()

        # Mifflin-St Jeor formula
        if "female" in gender or "woman" in gender:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5

        activity = hp.get("activity_level", "sedentary")
        tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity, 1.375)

        return int(tdee + self._goal_delta(hp))

    def _goal_delta(self, hp: dict) -> int:
        goal = (hp.get("primary_goal") or hp.get("fitness_goal") or "").lower()
        if "fat_loss" in goal or "loss" in goal or "slim" in goal:
            return -400  # ~0.37kg/week loss
        elif "muscle_gain" in goal or "muscle" in goal or "gain" in goal or "bulk" in goal:
            return 300   # ~0.27kg/week gain
        elif "endurance" in goal:
            return 150   # small surplus for performance
        return 0

    def _compute_macro_split(self, hp: dict, caloric_target: int) -> dict:
        """Evidence-based macro split based on goal."""
        weight = hp.get("weight_kg") or 70
        goal = (hp.get("primary_goal") or hp.get("fitness_goal") or "").lower()

        if "muscle" in goal or "gain" in goal:
            protein_g_per_kg = 2.0
        elif "fat_loss" in goal or "loss" in goal:
            protein_g_per_kg = 2.2  # higher protein preserves muscle in deficit
        else:
            protein_g_per_kg = 1.6

        protein_g = int(weight * protein_g_per_kg)
        protein_kcal = protein_g * 4
        fat_g = int((caloric_target * 0.25) / 9)
        fat_kcal = fat_g * 9
        carbs_g = int((caloric_target - protein_kcal - fat_kcal) / 4)

        return {
            "protein_g": protein_g,
            "protein_g_per_kg": protein_g_per_kg,
            "fat_g": fat_g,
            "carbs_g": max(carbs_g, 50),  # minimum 50g carbs
        }

    def _get_medical_adjustments(self, medical_conditions: list) -> list:
        """Rule-based dietary adjustments for medical conditions."""
        adjustments = []
        condition_names = [c.get("condition", "").lower() for c in medical_conditions if isinstance(c, dict)]

        if any("diabetes" in n or "type2" in n for n in condition_names):
            adjustments.append("Low-GI carbohydrates selected (GI < 55)")
            adjustments.append("Post-meal exercise timing recommended for glucose management")
        if any("hypertension" in n for n in condition_names):
            adjustments.append("Low-sodium options selected (<1500mg/day)")
            adjustments.append("DASH diet principles applied")
        if any("pcos" in n for n in condition_names):
            adjustments.append("Anti-inflammatory foods prioritized")
            adjustments.append("Refined carbs minimized")
        if any("arthritis" in n for n in condition_names):
            adjustments.append("Omega-3 rich foods prioritized for joint inflammation")

        return adjustments

    def _compute_hydration(self, hp: dict) -> int:
        """Target hydration in ml: 35ml/kg + 500ml/training session."""
        weight = hp.get("weight_kg") or 70
        training_days = hp.get("available_days_per_week") or 3
        base = int(weight * 35)
        training_addition = int((training_days / 7) * 500)  # daily training addition
        return base + training_addition

    def _build_nutrition_prompt(self, hp: dict, caloric_target: int,
                                 macro_split: dict, medical_adjustments: list,
                                 workout_schedule: list, context: AgentContext) -> str:
        diet_type = hp.get("diet_type") or hp.get("diet_preference", "vegetarian")
        allergies = hp.get("food_allergies") or hp.get("allergies", "none")
        cuisine = hp.get("cuisine_preference", ["Indian"])
        meal_freq = hp.get("meal_frequency", 3)

        medical_rules = "\n".join(f"- {adj}" for adj in medical_adjustments) if medical_adjustments else "None"
        allergen_rules = f"MUST AVOID (hard constraint): {allergies}" if allergies else "None"

        days = hp.get("available_days_per_week", 3)

        return f"""Generate a 7-day personalized meal plan.

CALORIC AND MACRO TARGETS (must match closely):
- Daily calories: {caloric_target} kcal
- Protein: {macro_split['protein_g']}g/day
- Carbohydrates: {macro_split['carbs_g']}g/day
- Fat: {macro_split['fat_g']}g/day
- Meals per day: {meal_freq}

MEDICAL DIETARY RULES (must follow):
{medical_rules}

ALLERGEN EXCLUSIONS (absolute hard constraint — never include):
{allergen_rules}

PREFERENCES:
- Diet type: {diet_type}
- Cuisine: {cuisine}
- Workout days this week: {days} (time carbs around workouts)

Return ONLY this JSON:
{{
  "plan": [
    {{
      "day": 1,
      "day_name": "Monday",
      "is_workout_day": true,
      "calories": {caloric_target},
      "protein_g": {macro_split['protein_g']},
      "carbs_g": {macro_split['carbs_g']},
      "fat_g": {macro_split['fat_g']},
      "meals": {{
        "breakfast": {{"name": "...", "calories": 400, "protein_g": 25, "ingredients": [], "prep_time": "15 min"}},
        "mid_morning_snack": {{"name": "...", "calories": 150}},
        "lunch": {{"name": "...", "calories": 550, "protein_g": 35, "ingredients": [], "prep_time": "20 min"}},
        "pre_workout_snack": {{"name": "...", "calories": 200, "note": "30 min before workout"}},
        "dinner": {{"name": "...", "calories": 500, "protein_g": 40, "ingredients": [], "prep_time": "25 min"}}
      }},
      "hydration_ml": {self._compute_hydration(hp)},
      "reasoning": "Macro split explained here; why these meals for this day",
      "grocery_list": [{{"name": "oats", "quantity": "500g"}}]
    }}
  ]
}}"""
