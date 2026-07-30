import json
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models.workout import WorkoutSession, WeeklyPlan, WorkoutPlan
from app.services.ai_service import generate_plan_with_groq
from app.services.youtube_service import enrich_exercise
from app.ai.prompts import get_workout_prompt

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


async def generate_7_day_plan(user_profile: dict, db: Session, user_id: int) -> list:
    """Generate a 7-day workout plan using Groq AI + YouTube videos."""
    import asyncio

    prompt = get_workout_prompt(user_profile)
    plan_data = await generate_plan_with_groq(prompt)

    days_data = plan_data.get("plan", [])
    if not days_data:
        raise Exception("AI returned empty plan data")

    all_exercises = []
    for day_data in days_data:
        all_exercises.extend(day_data.get("exercises", []))

    await asyncio.gather(*[enrich_exercise(ex) for ex in all_exercises])

    try:
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        existing_plan = db.query(WeeklyPlan).filter(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start_date == monday,
            WeeklyPlan.plan_status == "active"
        ).first()
        if existing_plan:
            existing_plan.plan_status = "superseded"
            db.query(WorkoutSession).filter(
                WorkoutSession.weekly_plan_id == existing_plan.id
            ).delete()

        plan = WeeklyPlan(
            user_id=user_id,
            week_start_date=monday,
            generated_by="legacy_workout_service",
        )
        db.add(plan)
        db.flush()

        saved_plans = []
        for day_data in days_data:
            day_num = day_data.get("day", 1)
            exercises = day_data.get("exercises", [])
            session_date = monday + timedelta(days=day_num - 1)

            ws = WorkoutSession(
                user_id=user_id,
                weekly_plan_id=plan.id,
                session_date=session_date,
                day_of_week=day_num,
                day_name=day_data.get("day_name", DAYS[day_num - 1]),
                focus_area=day_data.get("focus", ""),
                planned_duration_min=day_data.get("duration_minutes", 45),
                exercises_planned=exercises,
                warmup=day_data.get("warmup", ""),
                cooldown=day_data.get("cooldown", ""),
                tips=json.dumps(day_data.get("tips", "")),
                calories_burned_estimate=day_data.get("calories_estimate", 250),
                day=day_num,
                exercises=json.dumps(exercises),
            )
            db.add(ws)

            saved_plans.append({
                "id": None,
                "day": day_num,
                "day_name": ws.day_name,
                "exercises": exercises,
                "warmup": ws.warmup,
                "cooldown": ws.cooldown,
                "tips": day_data.get("tips", ""),
                "duration_minutes": ws.planned_duration_min,
                "focus": day_data.get("focus", ""),
                "calories_estimate": day_data.get("calories_estimate", 250),
            })

        db.commit()
        return saved_plans

    except Exception as e:
        db.rollback()
        print(f"Database error in workout generation: {e}")
        raise Exception(f"Failed to save workout plan: {str(e)}")


def get_today_workout(db: Session, user_id: int, day: int = None) -> dict:
    """Get today's workout from the current week's WorkoutSessions."""
    if day is None:
        day = date.today().weekday() + 1

    session = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.day_of_week == day
    ).order_by(WorkoutSession.session_date.desc(), WorkoutSession.id.desc()).first()

    if not session:
        return None

    exercises = []
    if session.exercises:
        try:
            exercises = json.loads(session.exercises)
        except Exception:
            pass
    if not exercises and session.exercises_planned:
        if isinstance(session.exercises_planned, list):
            exercises = session.exercises_planned

    tips = session.tips or ""
    if isinstance(tips, str):
        try:
            tips = json.loads(tips)
        except Exception:
            pass

    return {
        "id": session.id,
        "day": session.day_of_week or day,
        "day_name": session.day_name or DAYS[day - 1],
        "exercises": exercises,
        "warmup": session.warmup or "",
        "cooldown": session.cooldown or "",
        "tips": tips,
        "duration_minutes": session.planned_duration_min or 45,
        "focus": session.focus_area or "",
        "status": session.status,
        "reasoning": session.reasoning or "",
    }


def get_all_workouts(db: Session, user_id: int) -> list:
    """Get the current week's workout sessions in the shape the frontend expects."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.session_date >= monday,
        WorkoutSession.session_date <= sunday,
    ).order_by(WorkoutSession.day_of_week, WorkoutSession.id.desc()).all()

    if not sessions:
        sessions = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
        ).order_by(
            WorkoutSession.session_date.desc(),
            WorkoutSession.day_of_week
        ).limit(7).all()
        sessions = sorted(sessions, key=lambda s: s.day_of_week or 0)

    # Deduplicate sessions by day_of_week (take the latest id for each day)
    unique_sessions = {}
    for s in sessions:
        d = s.day_of_week or 1
        if d not in unique_sessions:
            unique_sessions[d] = s

    result = []
    for day_num in range(1, 8):
        s = unique_sessions.get(day_num)
        if not s:
            continue

        exercises = []
        if s.exercises:
            try:
                exercises = json.loads(s.exercises)
            except Exception:
                pass
        if not exercises and s.exercises_planned:
            if isinstance(s.exercises_planned, list):
                exercises = s.exercises_planned

        tips = s.tips or ""
        if isinstance(tips, str):
            try:
                tips = json.loads(tips)
            except Exception:
                pass

        result.append({
            "id": s.id,
            "day": s.day_of_week,
            "day_name": s.day_name or (DAYS[s.day_of_week - 1] if s.day_of_week else ""),
            "exercises": exercises,
            "warmup": s.warmup or "",
            "cooldown": s.cooldown or "",
            "tips": tips,
            "duration_minutes": s.planned_duration_min or 45,
            "focus": s.focus_area or "",
            "status": s.status,
            "reasoning": s.reasoning or "",
            "calories_estimate": s.calories_burned_estimate,
        })
    return result
