from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.workout_service import generate_7_day_plan, get_today_workout, get_all_workouts
from app.models.progress import ProgressMetric
from datetime import date
import random

router = APIRouter(prefix="/workout", tags=["Workout"])


def _get_user_profile(user: User, db: Session) -> dict:
    """Build user profile dict from HealthProfile (AroMi 2.0 schema)."""
    from app.models.health_profile import HealthProfile
    profile = db.query(HealthProfile).filter(
        HealthProfile.user_id == user.id
    ).first()
    if profile:
        return profile.to_agent_context()
    # Fallback for users without a profile
    return {
        "age": None, "gender": None, "weight_kg": 70, "height_cm": 170,
        "fitness_level": "beginner", "primary_goal": "general_fitness",
        "workout_location": "home", "preferred_workout_time": "morning",
        "health_conditions": None, "injuries": None,
        # legacy keys
        "fitness_goal": "general_fitness", "workout_preference": "home",
        "workout_time": "morning",
    }


@router.post("/generate")
async def generate_workout_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered 7-day workout plan (legacy single-agent endpoint)."""
    user_profile = _get_user_profile(current_user, db)
    try:
        plan = await generate_7_day_plan(user_profile, db, current_user.id)
        return {"status": "success", "plan": plan, "message": "Your 7-day workout plan is ready!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan")
def get_workout_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get this week's workout sessions."""
    plans = get_all_workouts(db, current_user.id)
    return {"plan": plans}


@router.get("/today")
def get_todays_workout(
    day: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's workout."""
    workout = get_today_workout(db, current_user.id, day)
    if not workout:
        return {"workout": None, "message": "No workout plan found. Generate a plan first!"}
    return {"workout": workout}


@router.post("/complete")
async def complete_workout(
    calories_burned: float,
    sets_completed: int,
    duration_minutes: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a completed workout and update progress metrics."""
    # Log as a ProgressMetric entry (new schema)
    metric = ProgressMetric(
        user_id=current_user.id,
        notes=f"Workout completed: {sets_completed} sets, {duration_minutes} min, {calories_burned} kcal burned"
    )
    db.add(metric)
    db.commit()

    messages = [
        "Shabash! You crushed it today! 💪",
        "Wah! Amazing work! Keep going! 🔥",
        "Fantastic effort! AROMI is proud of you! 🌟",
        "You're unstoppable! Great workout! 🏆"
    ]
    return {
        "status": "success",
        "message": random.choice(messages),
        "calories_burned": calories_burned,
        "sets_completed": sets_completed
    }
