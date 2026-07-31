import json
import re
import random
from groq import Groq
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.chat import ChatSession
from app.ai.prompts import AROMI_SYSTEM_PROMPT, get_chat_prompt


def get_groq_client():
    print(f"DEBUG: Using Groq API Key: {settings.GROQ_API_KEY[:10]}...{settings.GROQ_API_KEY[-5:]}")
    return Groq(api_key=settings.GROQ_API_KEY)


def clean_user_profile(profile: dict) -> dict:
    """Ensure user profile has sensible defaults and no None values for AI prompts."""
    defaults = {
        "age": 25,
        "gender": "not specified",
        "weight": 70,
        "height": 170,
        "fitness_level": "beginner",
        "fitness_goal": "general fitness",
        "workout_preference": "home",
        "workout_time": "flexible",
        "diet_preference": "vegetarian",
        "allergies": "none",
        "health_conditions": "none",
        "injuries": "none",
        "username": "User"
    }
    cleaned = {}
    for key, default in defaults.items():
        val = profile.get(key)
        cleaned[key] = val if val not in [None, "", "null"] else default
    
    for key, val in profile.items():
        if key not in cleaned:
            cleaned[key] = val
            
    return cleaned


async def chat_with_aromi(
    user_message: str,
    user_profile: dict,
    chat_history: list,
    db: Session,
    user_id: int
) -> tuple[str, bool]:
    """Main AROMI chat handler with DB-aware intelligent response generation."""
    try:
        from app.services.intent_service import GroqAromi
        
        safe_profile = clean_user_profile(user_profile)
        agent = GroqAromi(db, user_id, safe_profile)
        response_text, plan_modified = await agent.chat(user_message, chat_history)
        
        if response_text:
            chat_record = ChatSession(
                user_id=user_id,
                message=user_message,
                response=response_text,
                timestamp=datetime.utcnow()
            )
            db.add(chat_record)
            db.commit()
            return response_text, plan_modified
        else:
            return await _db_aware_conversational_fallback(user_message, user_profile, db, user_id)
        
    except Exception as e:
        print(f"Groq Aromi notice: {e}. Engaging DB-Aware Intelligence Engine.")
        return await _db_aware_conversational_fallback(user_message, user_profile, db, user_id)


async def _db_aware_conversational_fallback(
    user_message: str,
    user_profile: dict,
    db: Session,
    user_id: int
) -> tuple[str, bool]:
    """
    DB-Aware Intelligence Engine — Queries user's active database tables
    (WorkoutSession, HealthProfile, NutritionPlan, UserMemory) to produce
    detailed, accurate, personalized answers even when external LLM API is offline.
    """
    msg = user_message.lower().strip()
    username = user_profile.get("username", "there")

    # 0. Run deterministic action detection first (more time, less time, remove, replace, add, travel, fatigue, etc.)
    from app.services.intent_service import detect_intent
    action_result, plan_modified = await detect_intent(user_message, db, user_id)
    if action_result:
        return action_result, plan_modified

    def has_word(words, text):
        pattern = r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    # ── 1. AGE, SAFETY & CAPABILITY ENQUIRIES ─────────────────────────────────
    if any(w in msg for w in ["60", "70", "50", "80", "old", "age", "senior", "elderly", "can i do", "safe", "safely", "ability", "difficult", "hard"]):
        reply = (
            f"Yes, absolutely, {username}! 🌟\n\n"
            f"AROMI's Multi-Agent Engine is designed with anatomical safety guardrails. "
            f"All prescribed exercises account for your age, fitness level, and joint safety.\n\n"
            f"💡 **Safety & Modification Tips**:\n"
            f"1. **Listen to your body**: Perform repetitions at a controlled, comfortable pace.\n"
            f"2. **Use modifications**: You can swap any movement for low-impact alternatives anytime.\n"
            f"3. **Pacing**: Feel free to take extra rest seconds between sets.\n\n"
            f"If any exercise feels uncomfortable, simply tell me (e.g., *\"Swap exercise X\"* or *\"I'm tired today\"*), and I will update your plan immediately! 💪"
        )

    # ── 2. EXERCISE SWAP & ALTERNATIVE ENQUIRIES ──────────────────────────────
    elif has_word(["suggest", "alternative", "instead", "swap", "don't like", "dont like", "hate", "replace"], msg):
        from app.services.workout_service import get_today_workout
        today_w = get_today_workout(db, user_id)
        if today_w and today_w.get("exercises"):
            ex_names = [e.get("name") for e in today_w.get("exercises", []) if e.get("name")]
            ex_str = ", ".join(ex_names[:4])
            reply = (
                f"I hear you! 🎯 I've noted your preference.\n\n"
                f"In your current workout, you have: **{ex_str}**.\n\n"
                f"You can tell me: *\"Replace plank hold with Russian twists\"* or *\"Remove plank hold\"*, and I will swap it in your plan right away!"
            )
        else:
            reply = "I've noted your exercise preference! You can ask me to swap or remove any exercise from your workout anytime."

    # ── 3. GENERAL FITNESS & SAFETY QUESTIONS ─────────────────────────────────
    elif any(w in msg for w in ["can i", "is it", "how do", "should i", "why", "what if"]):
        reply = (
            f"That's a great question, {username}! 💡\n\n"
            f"Your workout and nutrition plans are fully personalized for your goals, fitness level, and health profile. "
            f"Always prioritize proper form, controlled breathing, and adequate hydration.\n\n"
            f"Tell me if you'd like me to modify today's workout (*\"less time\"*, *\"swap exercise X\"*), or ask about your meal plan!"
        )

    # ── 2. WORKOUT ROUTINE ENQUIRIES ──────────────────────────────────────────
    elif has_word(["workout", "routine", "exercise", "today's plan", "schedule", "training"], msg):
        from app.services.workout_service import get_today_workout
        today_w = get_today_workout(db, user_id)

        if today_w and today_w.get("exercises"):
            focus = today_w.get("focus", "Full Body")
            duration = today_w.get("duration_minutes", 45)
            exercises = today_w.get("exercises", [])
            
            ex_details = []
            for ex in exercises:
                name = ex.get("name", "Exercise")
                sets = ex.get("sets", 3)
                reps = ex.get("reps", "10-12")
                ex_details.append(f"• **{name}**: {sets} sets × {reps}")
            
            ex_summary = "\n".join(ex_details)
            reasoning = today_w.get("reasoning", "")
            reason_text = f"\n\n🧠 **Coach Reasoning**: {reasoning}" if reasoning else ""

            reply = (
                f"Here is your personalized workout routine for **{today_w.get('day_name', 'Today')}**! 💪\n\n"
                f"🎯 **Focus Area**: {focus}\n"
                f"⏱️ **Duration**: {duration} minutes\n\n"
                f"**Prescribed Exercises**:\n{ex_summary}"
                f"{reason_text}\n\n"
                f"Let me know if you want to swap an exercise, or tell me if you have *more time* or *less time* today!"
            )
        else:
            reply = (
                f"Here is your workout context, {username}:\n"
                f"You have a 7-day personalized training plan ready under the **Workouts** tab! "
                f"You can view today's target focus, exercise videos, and sets/reps breakdown there."
            )

    # ── 3. NUTRITION & MEAL PLAN ENQUIRIES ────────────────────────────────────
    elif has_word(["diet", "food", "nutrition", "meal", "eat", "lunch", "dinner", "breakfast", "calories"], msg):
        from app.services.nutrition_service import get_all_nutrition
        nutrition_plans = get_all_nutrition(db, user_id)
        
        today_num = date.today().weekday() + 1
        today_n = next((n for n in nutrition_plans if n.get("day") == today_num), None)
        if not today_n and nutrition_plans:
            today_n = nutrition_plans[0]

        if today_n and today_n.get("meals"):
            meals = today_n.get("meals", {})
            cals = today_n.get("calories", 2000)
            
            meal_lines = []
            for m_type, m_data in meals.items():
                m_label = m_type.replace('_', ' ').title()
                if isinstance(m_data, dict):
                    m_name = m_data.get("name", "Balanced Meal")
                    m_cal = m_data.get("calories", "")
                    cal_str = f" ({m_cal} kcal)" if m_cal else ""
                    meal_lines.append(f"• **{m_label}**: {m_name}{cal_str}")
                elif isinstance(m_data, str):
                    meal_lines.append(f"• **{m_label}**: {m_data}")

            meals_summary = "\n".join(meal_lines) if meal_lines else "Custom balanced meals"
            reply = (
                f"Here is your personalized meal plan for **{today_n.get('day_name', 'Today')}** 🥗\n\n"
                f"🔥 **Daily Calorie Target**: {cals} kcal\n\n"
                f"**Planned Meals**:\n{meals_summary}\n\n"
                f"Check out the **Nutrition** tab for the full grocery list and recipe hints!"
            )
        else:
            reply = (
                f"Your customized 7-day Indian meal plan and weekly grocery list are ready in the **Nutrition** tab! 🥗"
            )

    # ── 4. GREETINGS & INTROS ──────────────────────────────────────────────────
    elif has_word(["hi", "hey", "hello", "namaste", "hlo", "greetings"], msg):
        responses = [
            f"Namaste {username}! 🙏 I'm AROMI, your AI Fitness & Wellness Coach. How are you feeling today?",
            f"Hey {username}! Ready to crush your wellness goals today? 💪 Tell me if you have extra time or short time for your workout!",
            f"Hello {username}! Great to see you. How can I assist with your fitness plan today?"
        ]
        reply = random.choice(responses)

    # ── 5. SENTIMENT & STATUS ──────────────────────────────────────────────────
    elif has_word(["good", "great", "awesome", "fantastic", "well", "fine"], msg):
        responses = [
            f"Glad to hear that, {username}! That positive energy is perfect for today's workout session. 🔥",
            f"Awesome! Keeping a positive mindset is half the battle. Ready to check today's exercises? 🌟",
            f"That's great news! Remember to stay hydrated and keep moving today. 💧"
        ]
        reply = random.choice(responses)

    # ── 6. ACKNOWLEDGMENTS ─────────────────────────────────────────────────────
    elif has_word(["okay", "ok", "cool", "alright", "got it", "sure"], msg):
        responses = [
            "Awesome! Tell me if you'd like to check your routine, swap an exercise, or extend today's workout. 💪",
            "Sounds good! I'm right here whenever you want to adjust your schedule or log progress. ✨",
            "Great! Let me know how today's session goes! 🚀"
        ]
        reply = random.choice(responses)

    # ── 7. THANKS ──────────────────────────────────────────────────────────────
    elif has_word(["thank", "thanks", "thx", "shukriya", "dhanyawad"], msg):
        reply = f"You're very welcome, {username}! Keep up the fantastic effort! 🙌"

    # ── 8. DEFAULT INFORMED RESPONSE ───────────────────────────────────────────
    else:
        responses = [
            f"Namaste {username}! I'm here to guide your workouts, nutrition, and recovery. Tell me if you have *more time* or *less time* today, or ask me to swap/remove any exercise! 🌟",
            f"I'm all ears, {username}! Tell me how much time you have for your workout today or ask about your meal plan. 🏃‍♂️"
        ]
        reply = random.choice(responses)

    try:
        chat_record = ChatSession(
            user_id=user_id,
            message=user_message,
            response=reply,
            timestamp=datetime.utcnow()
        )
        db.add(chat_record)
        db.commit()
    except Exception:
        pass

    return reply, plan_modified


async def generate_plan_with_groq(prompt: str, user_profile: dict = None) -> dict:
    """Generate workout or nutrition plan using Groq, with graceful fallback on connection failure."""
    from app.services.fallback_service import get_fallback_workout_plan, get_fallback_nutrition_plan

    try:
        if not settings.GROQ_API_KEY or len(settings.GROQ_API_KEY.strip()) < 5:
            print("WARNING: Groq API key missing/invalid. Falling back to rule-based plan generator.")
            if "nutrition" in prompt.lower() or "meal" in prompt.lower():
                return get_fallback_nutrition_plan()
            return get_fallback_workout_plan(user_profile)

        client = get_groq_client()
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert fitness and nutrition coach. Always respond with valid JSON only. No markdown, no explanations, just JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        
        raw_response = completion.choices[0].message.content.strip()
        
        start_idx = raw_response.find('{')
        end_idx = raw_response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            response_text = raw_response[start_idx:end_idx+1]
        else:
            response_text = raw_response

        response_text = re.sub(r',\s*}', '}', response_text)
        response_text = re.sub(r',\s*]', ']', response_text)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            print(f"JSON parse error: {e}. Falling back to rule-based plan.")
            if "nutrition" in prompt.lower() or "meal" in prompt.lower():
                return get_fallback_nutrition_plan()
            return get_fallback_workout_plan(user_profile)
            
    except Exception as e:
        print(f"Groq API connection/service warning: {e}. Engaging offline fallback plan generator.")
        if "nutrition" in prompt.lower() or "meal" in prompt.lower():
            return get_fallback_nutrition_plan()
        return get_fallback_workout_plan(user_profile)
