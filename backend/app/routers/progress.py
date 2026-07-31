from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.progress import ProgressMetric  # new schema (ProgressRecord alias also works)

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.post("/log")
def log_progress(
    calories_burned: float = 0,
    workouts_completed: int = 0,
    weight: float = None,
    sets_completed: int = 0,
    workout_duration: int = 0,
    healthy_meals: int = 0,
    notes: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log daily progress into ProgressMetric (new schema)."""
    from app.models.workout import WorkoutSession
    
    note_parts = []
    if calories_burned:
        note_parts.append(f"{calories_burned} kcal burned")
    if workouts_completed:
        note_parts.append(f"{workouts_completed} workouts")
    if sets_completed:
        note_parts.append(f"{sets_completed} sets")
    if workout_duration:
        note_parts.append(f"{workout_duration} min")
    if healthy_meals:
        note_parts.append(f"{healthy_meals} healthy meals")
    if notes:
        note_parts.append(notes)

    if workouts_completed > 0:
        today = date.today()
        session = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.session_date == today
        ).first()
        if session:
            session.status = "completed"
            session.completion_pct = 1.0
            if calories_burned:
                session.calories_burned_estimate = int(calories_burned)
        else:
            session = WorkoutSession(
                user_id=current_user.id,
                session_date=today,
                day_name=today.strftime("%A"),
                focus_area="Full Body Workout",
                status="completed",
                completion_pct=1.0,
                calories_burned_estimate=int(calories_burned) if calories_burned else 200
            )
            db.add(session)

    metric = ProgressMetric(
        user_id=current_user.id,
        weight_kg=weight,
        notes=", ".join(note_parts) if note_parts else None,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)

    return {
        "id": metric.id,
        "user_id": metric.user_id,
        "date": metric.recorded_at.date().isoformat(),
        "weight_kg": metric.weight_kg,
        "notes": metric.notes,
        "calories_burned": calories_burned,
        "workouts_completed": workouts_completed,
        "sets_completed": sets_completed,
        "workout_duration": workout_duration,
        "healthy_meals": healthy_meals,
    }


@router.get("/history")
def get_progress_history(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get last N progress records."""
    records = db.query(ProgressMetric).filter(
        ProgressMetric.user_id == current_user.id
    ).order_by(ProgressMetric.recorded_at.desc()).limit(limit).all()

    return [{
        "id": r.id,
        "user_id": r.user_id,
        "date": r.recorded_at.date().isoformat(),
        "weight_kg": r.weight_kg,
        "body_fat_pct": r.body_fat_pct,
        "notes": r.notes,
    } for r in records]


@router.get("/stats")
def get_progress_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggregated stats for the dashboard."""
    from app.models.workout import WorkoutSession

    # Reconcile any ProgressMetric entries logged for workouts that don't have WorkoutSession marked completed
    metrics_with_workouts = db.query(ProgressMetric).filter(
        ProgressMetric.user_id == current_user.id,
        ProgressMetric.notes.like("%Workout%")
    ).all()

    for m in metrics_with_workouts:
        m_date = m.recorded_at.date()
        existing = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.session_date == m_date,
            WorkoutSession.status == "completed"
        ).first()
        if not existing:
            ws = db.query(WorkoutSession).filter(
                WorkoutSession.user_id == current_user.id,
                WorkoutSession.session_date == m_date
            ).first()
            if ws:
                ws.status = "completed"
                ws.completion_pct = 1.0
                if not ws.calories_burned_estimate:
                    ws.calories_burned_estimate = 200
            else:
                ws = WorkoutSession(
                    user_id=current_user.id,
                    session_date=m_date,
                    day_name=m_date.strftime("%A"),
                    focus_area="Full Body Workout",
                    status="completed",
                    completion_pct=1.0,
                    calories_burned_estimate=200
                )
                db.add(ws)
            db.commit()

    # Workout stats from WorkoutSession
    completed_sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.status == "completed"
    ).all()

    total_workouts = len(completed_sessions)
    total_calories = sum(
        s.calories_burned_estimate or 0 for s in completed_sessions
    )

    # Progress records for weight trend
    metrics = db.query(ProgressMetric).filter(
        ProgressMetric.user_id == current_user.id
    ).order_by(ProgressMetric.recorded_at.desc()).limit(30).all()

    streak = _compute_streak(current_user.id, db)

    # Charity impact: ₹2 per workout
    charity_amount = total_workouts * 2

    return {
        "total_calories_burned": round(total_calories, 1),
        "total_workouts": total_workouts,
        "total_healthy_meals": 0,   # Tracked separately via /health-data endpoints
        "streak_days": streak,
        "charity_amount_inr": charity_amount,
        "people_impacted": total_workouts // 3,
        "records": len(metrics),
        "latest_weight_kg": metrics[0].weight_kg if metrics else None,
    }


def _compute_streak(user_id: int, db: Session) -> int:
    """Compute current consecutive training days streak."""
    from app.models.workout import WorkoutSession
    from datetime import timedelta

    today = date.today()
    streak = 0
    check_date = today
    for _ in range(60):  # look back up to 60 days
        session = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date == check_date,
            WorkoutSession.status == "completed"
        ).first()
        if session:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak
