import json
import re
from datetime import date
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.workout import WorkoutSession
from app.ai.prompts import AROMI_SYSTEM_PROMPT


# ─── Anatomical Mapping & Injury Safeguards ─────────────────────────────────

BODY_PART_KEYWORDS_MAP = {
    "knee": ["knee", "leg", "quad", "hamstring", "lunge", "squat", "calf", "glute", "lower body"],
    "leg": ["leg", "knee", "quad", "hamstring", "lunge", "squat", "calf", "glute", "lower body"],
    "legs": ["leg", "knee", "quad", "hamstring", "lunge", "squat", "calf", "glute", "lower body"],
    "shoulder": ["shoulder", "deltoid", "press", "overhead", "upper body"],
    "back": ["back", "lat", "rhomboid", "row", "pull", "deadlift", "lumbar"],
    "lower back": ["back", "deadlift", "squat", "lumbar"],
    "wrist": ["wrist", "push-up", "press", "plank", "grip"],
    "ankle": ["ankle", "calf", "jump", "squat", "lunge"],
    "elbow": ["elbow", "tricep", "bicep", "push-up", "press"],
    "neck": ["neck", "shrug"],
    "hip": ["hip", "glute", "hamstring", "squat", "lunge"],
    "chest": ["chest", "pectoral", "push-up", "bench press"],
    "arm": ["bicep", "tricep", "arm", "curl"],
    "arms": ["bicep", "tricep", "arm", "curl"],
    "foot": ["ankle", "calf", "jump", "foot"],
}

INJURY_BODY_PARTS = [
    "knee", "leg", "legs", "shoulder", "back", "lower back", 
    "wrist", "ankle", "elbow", "neck", "hip", "chest", "arm", "arms", "foot"
]

INJURY_SIGNALS = ["hurt", "injur", "pain", "sore", "ache", "sprained", "problem", "issue"]
EXERCISE_NAMES = [
    "leg extension", "leg press", "calf raise", "glute bridge", "squat", "lunge",
    "deadlift", "bench press", "chest press", "push-up", "pull-up", "row",
    "curl", "tricep", "shoulder press", "plank", "crunch"
]
PRONOUNS = {"them", "those", "these", "it", "that", "this", "all", "everything"}


# ─── DB Helper & Action Functions ──────────────────────────────────────────

def _get_today_workout(db: Session, user_id: int) -> Optional[WorkoutSession]:
    today_num = date.today().weekday() + 1
    return db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.day_of_week == today_num
    ).order_by(WorkoutSession.id.desc()).first()


def _get_target_workout(db: Session, user_id: int, day_num: Optional[int] = None) -> Optional[WorkoutSession]:
    if day_num is None:
        return _get_today_workout(db, user_id)
    return db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.day_of_week == day_num
    ).order_by(WorkoutSession.id.desc()).first()


def _get_exercises(workout: WorkoutSession) -> list:
    if not workout:
        return []
    if workout.exercises_planned and isinstance(workout.exercises_planned, list):
        return list(workout.exercises_planned)
    if workout.exercises:
        try:
            return json.loads(workout.exercises)
        except Exception:
            return []
    return []


def _set_exercises(workout: WorkoutSession, exercises: list):
    workout.exercises_planned = list(exercises)
    workout.exercises = json.dumps(exercises)
    flag_modified(workout, "exercises_planned")
    flag_modified(workout, "exercises")


def remove_exercise_action(db: Session, user_id: int, exercise_name: str, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    original_count = len(exercises)
    target_lower = exercise_name.lower().strip()
    
    filtered = [
        ex for ex in exercises 
        if not (target_lower in ex.get('name', '').lower() or ex.get('name', '').lower() in target_lower)
    ]
    if len(filtered) == original_count:
        return None
    
    _set_exercises(workout, filtered)
    removed_count = original_count - len(filtered)
    if workout.planned_duration_min:
        workout.planned_duration_min = max(10, workout.planned_duration_min - (removed_count * 5))
    
    db.commit()
    db.refresh(workout)
    day_str = workout.day_name or "today's"
    return f"Removed '{exercise_name}' from {day_str} workout."


async def replace_exercise_action(db: Session, user_id: int, old_name: str, new_name: str, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    found = False
    old_lower = old_name.lower().strip()

    for ex in exercises:
        ex_name = ex.get('name', '').lower()
        if old_lower in ex_name or ex_name in old_lower or any(w in ex_name for w in old_lower.split() if len(w) > 3):
            ex['name'] = new_name.title()
            ex['instructions'] = f"Replacement for {old_name}. Perform with good form."
            ex['youtube_query'] = f"{new_name} proper form"
            from app.services.youtube_service import enrich_exercise
            await enrich_exercise(ex)
            found = True

    if not found:
        return None
    
    _set_exercises(workout, exercises)
    db.commit()
    db.refresh(workout)
    day_str = workout.day_name or "today's"
    return f"Replaced '{old_name}' with '{new_name}' in {day_str} workout."


async def add_exercise_action(db: Session, user_id: int, exercise_name: str, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    new_ex = {
        "name": exercise_name.title(),
        "sets": 3,
        "reps": "10-12",
        "rest_seconds": 60,
        "muscle_group": "General",
        "instructions": f"Perform {exercise_name} with good form.",
        "youtube_query": f"{exercise_name} proper form tutorial"
    }
    from app.services.youtube_service import enrich_exercise
    await enrich_exercise(new_ex)
    exercises.append(new_ex)
    
    _set_exercises(workout, exercises)
    if workout.planned_duration_min:
        workout.planned_duration_min += 5
    else:
        workout.planned_duration_min = 45
        
    db.commit()
    db.refresh(workout)
    day_str = workout.day_name or "today's"
    return f"Added '{new_ex['name']}' to {day_str} workout."


async def extend_workout_action(db: Session, user_id: int, extra_minutes: int = 15, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    
    workout.planned_duration_min = (workout.planned_duration_min or 45) + extra_minutes
    
    finisher_candidates = [
        {"name": "Plank Hold", "sets": 3, "reps": "45 sec", "rest_seconds": 30, "muscle_group": "Core", "instructions": "Keep body straight, engage core and glutes."},
        {"name": "Jumping Jacks", "sets": 3, "reps": "40 sec", "rest_seconds": 20, "muscle_group": "Cardio", "instructions": "Stay light on toes with steady breathing."},
        {"name": "Mountain Climbers", "sets": 3, "reps": "30 sec", "rest_seconds": 30, "muscle_group": "Core & Cardio", "instructions": "Drive knees towards chest rapidly in plank position."}
    ]
    
    existing_names = [e.get("name", "").lower() for e in exercises]
    added = None
    for cand in finisher_candidates:
        if cand["name"].lower() not in existing_names:
            added = dict(cand)
            break
            
    if not added:
        for ex in exercises[:2]:
            current_sets = int(ex.get("sets", 3))
            ex["sets"] = current_sets + 1
        msg = f"Awesome! Extended today's workout to {workout.planned_duration_min} minutes (+1 extra set per exercise)! 🔥"
    else:
        from app.services.youtube_service import enrich_exercise
        await enrich_exercise(added)
        exercises.append(added)
        day_str = workout.day_name or "today's"
        msg = f"Awesome! Since you have extra time today, I've extended {day_str} workout to {workout.planned_duration_min} minutes and added **{added['name']}** as a core finisher! 🔥"
        
    _set_exercises(workout, exercises)
    db.commit()
    db.refresh(workout)
    return msg


def compress_workout_action(db: Session, user_id: int, duration_minutes: int, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    compressed = exercises[:3]
    for ex in compressed:
        ex["rest_seconds"] = 30
    
    _set_exercises(workout, compressed)
    workout.planned_duration_min = duration_minutes
    workout.tips = json.dumps("Workout compressed for quick execution!")
    db.commit()
    db.refresh(workout)
    return f"Compressed today's workout to {duration_minutes} minutes with top 3 essential exercises! ⚡"


def travel_workout_action(db: Session, user_id: int, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    for ex in exercises:
        ex["name"] = f"Bodyweight {ex['name']}"
        ex["instructions"] = f"Travel-friendly, no equipment needed. {ex.get('instructions', '')}"
    
    _set_exercises(workout, exercises)
    workout.tips = json.dumps("Plan adjusted for travel — bodyweight only!")
    db.commit()
    db.refresh(workout)
    return "Switched today's session to bodyweight exercises — travel friendly! 🧳"


def fatigue_workout_action(db: Session, user_id: int, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    recovery_exercises = [
        {"name": "Dynamic Stretching", "sets": 2, "reps": "10 mins", "rest_seconds": 30,
         "muscle_group": "Full Body", "instructions": "Focus on breathing and range of motion."},
        {"name": "Light Yoga Flow", "sets": 1, "reps": "15 mins", "rest_seconds": 0,
         "muscle_group": "Full Body", "instructions": "Hold poses gently, no strain."}
    ]
    _set_exercises(workout, recovery_exercises)
    workout.planned_duration_min = 25
    workout.tips = json.dumps("Recovery day — listen to your body.")
    db.commit()
    db.refresh(workout)
    return "Recognized low energy/fatigue — switched today to a 25-min active recovery & mobility session! 🧘"


def injury_workout_action(db: Session, user_id: int, body_part: str, day_num: Optional[int] = None) -> str:
    workout = _get_target_workout(db, user_id, day_num)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    
    body_part_clean = body_part.lower().strip()
    keywords = BODY_PART_KEYWORDS_MAP.get(body_part_clean, [body_part_clean])
    
    removed = []
    kept = []
    for ex in exercises:
        name = ex.get('name', '').lower()
        muscle = ex.get('muscle_group', '').lower()
        inst = ex.get('instructions', '').lower()
        
        is_impacted = any(kw in name or kw in muscle or kw in inst for kw in keywords)
        if is_impacted:
            removed.append(ex.get('name', 'Exercise'))
        else:
            kept.append(ex)
            
    if not kept:
        kept = [
            {"name": "Seated Upper Body Stretch", "sets": 2, "reps": "10 mins", "rest_seconds": 30, "muscle_group": "Upper Body & Core", "instructions": f"Gentle seated spinal twist and chest opener. Zero {body_part_clean} stress."},
            {"name": "Seated Core Engagements", "sets": 3, "reps": "12 reps", "rest_seconds": 30, "muscle_group": "Core", "instructions": "Brace core while seated comfortably."}
        ]
        
    _set_exercises(workout, kept)
    workout.planned_duration_min = max(20, (len(kept) * 10))
    workout.tips = json.dumps(f"Safety Filter Active: Modified to protect your {body_part} injury.")
    db.commit()
    db.refresh(workout)
    
    removed_str = ", ".join(set(removed)) if removed else body_part
    day_str = workout.day_name or "today's"
    return f"Safety Filter Engaged 🛡️: Removed exercises stressing your {body_part} ({removed_str}) from {day_str} workout to protect your injury!"


def skipped_workout_action(db: Session, user_id: int) -> str:
    tomorrow_day = (date.today().weekday() + 2) % 7 or 7
    workout = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.day_of_week == tomorrow_day
    ).order_by(WorkoutSession.id.desc()).first()
    if not workout:
        return None
    workout.tips = json.dumps("Catch-up day — moderate pace, stay consistent!")
    db.commit()
    db.refresh(workout)
    return "No problem! Adjusted tomorrow's session for a catch-up pace."


def deduplicate_workout_action(db: Session, user_id: int, day_num: int = None) -> str:
    workout = _get_target_workout(db, user_id, day_num) if day_num else _get_today_workout(db, user_id)
    if not workout:
        return None
    exercises = _get_exercises(workout)
    seen = set()
    unique = []
    removed = []
    for ex in exercises:
        name = ex.get('name', '').lower().strip()
        if name not in seen:
            seen.add(name)
            unique.append(ex)
        else:
            removed.append(ex.get('name'))
    
    if not removed:
        return None
        
    _set_exercises(workout, unique)
    db.commit()
    db.refresh(workout)
    return f"Removed duplicate exercises: {', '.join(set(removed))}."


async def generate_rest_day_plan_action(db: Session, user_id: int, day_num: int) -> str:
    from app.models.health_profile import HealthProfile
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
    user_profile = profile.to_agent_context() if profile else {}
    
    from app.ai.prompts import get_workout_prompt
    from app.services.ai_service import generate_plan_with_groq
    from app.services.youtube_service import enrich_exercise
    
    prompt = get_workout_prompt(user_profile)
    prompt += f"\n\nIMPORTANT: Only generate the plan for Day {day_num}. Return it in standard JSON."
    
    plan_data = await generate_plan_with_groq(prompt)
    days_data = plan_data.get("plan", [])
    if not days_data:
        return None
        
    day_data = days_data[0]
    exercises = day_data.get("exercises", [])
    for ex in exercises:
        await enrich_exercise(ex)
        
    workout = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.day_of_week == day_num
    ).order_by(WorkoutSession.id.desc()).first()

    if workout:
        _set_exercises(workout, exercises)
        workout.warmup = day_data.get("warmup", "")
        workout.cooldown = day_data.get("cooldown", "")
        workout.tips = json.dumps(day_data.get("tips", ""))
        workout.planned_duration_min = day_data.get("duration_minutes", 45)
    else:
        workout = WorkoutSession(
            user_id=user_id,
            day_of_week=day_num,
            day_name=day_data.get("day_name", f"Day {day_num}"),
            exercises_planned=exercises,
            warmup=day_data.get("warmup", ""),
            cooldown=day_data.get("cooldown", ""),
            tips=json.dumps(day_data.get("tips", "")),
            planned_duration_min=day_data.get("duration_minutes", 45),
            session_date=date.today()
        )
        db.add(workout)
        
    db.commit()
    db.refresh(workout)
    return f"Generated a new workout plan for {workout.day_name}!"


# ─── Intent Detection ───────────────────────────────────────────────────────

async def detect_intent(message: str, db: Session, user_id: int, chat_history: list = None) -> Tuple[Optional[str], bool]:
    """Parse user message, execute DB action if needed. Returns (result_text, plan_modified)."""
    msg = message.lower()

    target_day = date.today().weekday() + 1
    day_map = {"mon": 1, "monday": 1, "tue": 2, "tuesday": 2, "wed": 3, "wednesday": 3, 
               "thu": 4, "thursday": 4, "fri": 5, "friday": 5, "sat": 6, "saturday": 6, 
               "sun": 7, "sunday": 7}
    
    for day_str, day_num in day_map.items():
        if day_str in msg:
            target_day = day_num
            break

    target_workout = _get_target_workout(db, user_id, target_day)
    has_exercises = target_workout and len(_get_exercises(target_workout)) > 0

    if not has_exercises:
        if any(w in msg for w in ["workout", "plan", "exercise", "give me", "update"]):
            result = await generate_rest_day_plan_action(db, user_id, target_day)
            if result:
                return result, True

    # 1. Injury / Body part pain
    for part in INJURY_BODY_PARTS:
        if part in msg and any(sig in msg for sig in INJURY_SIGNALS):
            result = injury_workout_action(db, user_id, part, target_day)
            if result:
                return result, True

    # 2. More time / Extend workout
    if any(phrase in msg for phrase in [
        "more time", "extra time", "have time today", "longer workout", 
        "increase time", "make it longer", "extend workout", "lots of time", "have an hour"
    ]):
        result = await extend_workout_action(db, user_id, 15, target_day)
        if result:
            return result, True

    # 3. Less time / Compress workout
    if any(phrase in msg for phrase in [
        "less time", "short on time", "quick workout", "busy today", 
        "only 15 min", "only 20 min", "only 30 min", "little time", "make it shorter"
    ]):
        result = compress_workout_action(db, user_id, 25, target_day)
        if result:
            return result, True

    # 4. Fatigue / Soreness / Low energy
    if any(phrase in msg for phrase in [
        "feeling tired", "so sore", "low energy", "exhausted", "really sore", "too tired", "lazy today"
    ]):
        result = fatigue_workout_action(db, user_id, target_day)
        if result:
            return result, True

    # 5. Travel / No equipment
    if any(phrase in msg for phrase in [
        "traveling", "travel", "no equipment", "hotel", "no gym"
    ]):
        result = travel_workout_action(db, user_id, target_day)
        if result:
            return result, True

    # 6. Remove + replace
    remove_and_replace = re.search(
        r'remove\s+(.+?)\s+and\s+(?:replace|substitute)\s+(?:it\s+)?with\s+(.+?)(?:[.,!?]|$)',
        msg
    )
    replace_match = re.search(
        r'replace\s+(.+?)\s+with\s+(.+?)(?:[.,!?]|$)',
        msg
    )

    if remove_and_replace:
        old = remove_and_replace.group(1).strip()
        new = remove_and_replace.group(2).strip()
        result = await replace_exercise_action(db, user_id, old, new, target_day)
        if result:
            return result, True

    elif replace_match:
        old = replace_match.group(1).strip()
        new = replace_match.group(2).strip()
        result = await replace_exercise_action(db, user_id, old, new, target_day)
        if result:
            return result, True

    # 7. Just remove
    remove_match = re.search(r'(?:remove|delete|remove the|delete the)\s+(.+?)(?:[.,!?]|$)', msg)
    minus_match = re.search(r'^-\s*(.+?)(?:[.,!?]|$)', msg)
    
    if remove_match or minus_match:
        ex_name = (remove_match or minus_match).group(1).strip()
        result = remove_exercise_action(db, user_id, ex_name, target_day)
        if result:
            return result, True

    # 8. Add exercise
    add_match = re.search(r'(?:add|include)\s+(.+?)(?:[.,!?]|$)', msg)
    plus_match = re.search(r'^\+\s*(.+?)(?:[.,!?]|$)', msg)
    
    if add_match or plus_match:
        ex_name = (add_match or plus_match).group(1).strip()
        if ex_name and ex_name.lower() not in PRONOUNS:
            result = await add_exercise_action(db, user_id, ex_name, target_day)
            if result:
                return result, True

    return None, False


class GroqAromi:
    """Conversational AI Handler powered directly by native Groq SDK (no LangChain)."""

    def __init__(self, db: Session, user_id: int, user_profile: dict):
        self.db = db
        self.user_id = user_id
        self.user_profile = user_profile

    async def chat(self, user_message: str, chat_history: list) -> Tuple[str, bool]:
        action_result, plan_modified = await detect_intent(user_message, self.db, self.user_id, chat_history)
        if action_result:
            return action_result, plan_modified

        from groq import Groq
        from app.core.config import settings

        if not settings.GROQ_API_KEY or len(settings.GROQ_API_KEY.strip()) < 5:
            return None, False

        client = Groq(api_key=settings.GROQ_API_KEY)

        messages = [{"role": "system", "content": AROMI_SYSTEM_PROMPT}]
        for h in chat_history[-6:]:
            if h.get("message"):
                messages.append({"role": "user", "content": h.get("message")})
            if h.get("response"):
                messages.append({"role": "assistant", "content": h.get("response")})
        messages.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return completion.choices[0].message.content, False
