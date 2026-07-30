"""
AI Prompt Templates for ArogyaMitra
"""


AROMI_SYSTEM_PROMPT = """You are AROMI, a professional, intelligent, and highly capable fitness coach and wellness companion on the ArogyaMitra platform.

Your personality:
- Professional, efficient, and results-oriented.
- English only — do not use Hindi or other regional languages.
- Give short, precise, and actionable tactical advice.
- Be medically cautious — always recommend consulting a doctor for serious conditions.
- Focus on data-driven holistic wellness: physical fitness, nutrition, and recovery.

Your capabilities:
- Dynamic plan auto-regeneration based on performance analytics.
- Context-aware adjustments (travel, time constraints, injuries).
- Data-driven progressive overload strategies.
- Motivation through clarity and direct feedback.

Guidelines:
- Keep responses concise and direct.
- Avoid unnecessary fluff or over-explaining.
- Directly modify plans when user context requires it.
- Ensure all changes are reflected immediately in the user's dashboard.
"""


def get_workout_prompt(user_profile: dict) -> str:
    performance_context = user_profile.get('performance_context', '')
    adaptive_instructions = ""
    if performance_context:
        adaptive_instructions = f"\nADAPTIVE FEEDBACK: {performance_context}\nIMPORTANT: You must directly modify the previous plan's intensity. If performance was high, increase reps by 10-15%, reduce rest by 5-10s, or add 1 set to compound exercises. If performance was low, simplify movements or increase rest."

    return f"""You are an expert fitness coach. Generate a 7-day personalized workout plan.
{adaptive_instructions}

User Profile:
- Age: {user_profile.get('age', 25)} years
- Gender: {user_profile.get('gender', 'not specified')}
- Weight: {user_profile.get('weight', 70)} kg
- Height: {user_profile.get('height', 170)} cm
- Fitness Level: {user_profile.get('fitness_level', 'beginner')}
- Primary Goal: {user_profile.get('fitness_goal', 'general fitness')}
- Workout Location: {user_profile.get('workout_preference', 'home')}
- Preferred Time: {user_profile.get('workout_time', 'morning')}
- Medical Conditions: {user_profile.get('health_conditions', 'none')}
- Injuries: {user_profile.get('injuries', 'none')}
- Last Week Performance: {user_profile.get('total_workouts_last_week', 0)} workouts completed.

Generate a JSON response with this exact structure:
{{{{
  "plan": [
    {{{{
      "day": 1,
      "day_name": "Monday",
      "focus": "Upper Body",
      "duration_minutes": 45,
      "warmup": "5-minute brisk walk and arm circles",
      "exercises": [
        {{{{
          "name": "Push-ups",
          "sets": 3,
          "reps": "10-12",
          "rest_seconds": 60,
          "muscle_group": "Chest",
          "youtube_query": "push-ups proper form for beginners",
          "instructions": "Keep your core tight and lower chest to ground"
        }}}}
      ],
      "cooldown": "5-minute stretching",
      "tips": "Stay hydrated and rest if you feel pain",
      "calories_estimate": 250
    }}}}
  ]
}}}}

Requirements:
- Day 7 should be active rest (yoga, stretching, walk)
- Adjust intensity for {user_profile.get('fitness_level', 'beginner')} level
- For home workouts, use bodyweight exercises only
- For gym, include equipment-based exercises
- Include realistic sets/reps
- Return ONLY the JSON, no extra text"""


def get_nutrition_prompt(user_profile: dict) -> str:
    calorie_target = _calculate_calories(user_profile)
    return f"""You are an expert nutritionist. Generate a 7-day Indian meal plan.

User Profile:
- Age: {user_profile.get('age', 25)}
- Weight: {user_profile.get('weight', 70)} kg
- Height: {user_profile.get('height', 170)} cm
- Goal: {user_profile.get('fitness_goal', 'general fitness')}
- Diet: {user_profile.get('diet_preference', 'vegetarian')}
- Allergies: {user_profile.get('allergies', 'none')}
- Calorie Target: ~{calorie_target} kcal/day

Generate a JSON response with this exact structure:
{{{{
  "plan": [
    {{{{
      "day": 1,
      "day_name": "Monday",
      "calories": {calorie_target},
      "protein": 80,
      "carbs": 200,
      "fat": 50,
      "meals": {{{{
        "breakfast": {{{{
          "name": "Oats Upma with Vegetables",
          "ingredients": ["oats", "vegetables", "spices"],
          "calories": 350,
          "prep_time": "15 mins",
          "recipe_hint": "Cook oats with sauteed vegetables"
        }}}},
        "mid_morning_snack": {{{{
          "name": "Banana and Almonds",
          "calories": 150
        }}}},
        "lunch": {{{{
          "name": "Dal Rice with Salad",
          "ingredients": ["dal", "rice", "cucumber", "tomato"],
          "calories": 500,
          "prep_time": "30 mins"
        }}}},
        "evening_snack": {{{{
          "name": "Green Tea with Roasted Chana",
          "calories": 100
        }}}},
        "dinner": {{{{
          "name": "Roti with Sabzi and Curd",
          "ingredients": ["wheat roti", "mixed vegetables", "curd"],
          "calories": 400,
          "prep_time": "25 mins"
        }}}}
      }}}},
      "hydration": "Drink 8-10 glasses of water",
      "grocery_list": [
        {{"name": "oats", "quantity": "500g"}},
        {{"name": "dal", "quantity": "1kg"}},
        {{"name": "rice", "quantity": "2kg"}},
        {{"name": "vegetables", "quantity": "2kg"}},
        {{"name": "almonds", "quantity": "100g"}},
        {{"name": "banana", "quantity": "1 dozen"}}
      ]
    }}}}
  ]
}}}}

Requirements:
- Use Indian foods primarily (dal, roti, sabzi, rice, idli, dosa, etc.)
- Respect {user_profile.get('diet_preference', 'vegetarian')} preference
- Avoid allergens: {user_profile.get('allergies', 'none')}
- Calorie target: ~{calorie_target} kcal/day
- Return ONLY the JSON, no extra text"""


def get_chat_prompt(user_profile: dict, chat_history: list) -> str:
    history_text = ""
    for msg in chat_history[-6:]:  # last 6 messages for context
        history_text += f"User: {msg['message']}\nAROMI: {msg['response']}\n"
    
    return f"""User Profile: Age {user_profile.get('age', 'unknown')}, 
Goal: {user_profile.get('fitness_goal', 'general fitness')}, 
Level: {user_profile.get('fitness_level', 'beginner')},
Diet: {user_profile.get('diet_preference', 'vegetarian')}

Recent conversation:
{history_text}"""


def _calculate_calories(profile: dict) -> int:
    try:
        weight = float(profile.get('weight', 70))
        height = float(profile.get('height', 170))
        age = float(profile.get('age', 25))
        gender = profile.get('gender', 'male').lower()
        goal = profile.get('fitness_goal', '').lower()

        if 'female' in gender:
            bmr = 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)
        else:
            bmr = 66 + (13.7 * weight) + (5 * height) - (6.8 * age)

        tdee = bmr * 1.375  # moderate activity

        if 'loss' in goal or 'slim' in goal:
            return int(tdee - 500)
        elif 'muscle' in goal or 'gain' in goal or 'bulk' in goal:
            return int(tdee + 300)
        else:
            return int(tdee)
    except Exception:
        return 2000
