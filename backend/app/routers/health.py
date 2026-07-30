"""
Health data router — sleep, hydration, progress metric logging, and feedback.
These endpoints feed the Recovery Agent and Evaluation Framework.

WHY separate router (not merged into users/):
- Health data is high-frequency (daily logs) vs. profile (rare updates)
- Separate prefix (/health-data) makes API semantics clear
- Enables independent rate-limiting if needed in production
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.progress import SleepLog, HydrationLog, ProgressMetric
from app.models.evaluation import FeedbackEvent
from app.models.workout import WorkoutSession
from pydantic import BaseModel, Field

router = APIRouter(prefix="/health-data", tags=["Health Data"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class SleepLogCreate(BaseModel):
    sleep_date: date
    duration_hours: float = Field(ge=0, le=24)
    quality_score: int = Field(ge=1, le=10)
    hrv_ms: Optional[float] = None
    notes: Optional[str] = None


class HydrationLogCreate(BaseModel):
    log_date: date
    water_ml: int = Field(ge=0)
    target_ml: Optional[int] = None


class ProgressMetricCreate(BaseModel):
    weight_kg: Optional[float] = Field(default=None, ge=1, le=500)
    body_fat_pct: Optional[float] = Field(default=None, ge=0, le=100)
    waist_cm: Optional[float] = None
    notes: Optional[str] = None


class WorkoutFeedbackSubmit(BaseModel):
    session_id: int
    status: Optional[str] = None          # completed/skipped/partial
    completion_pct: Optional[float] = Field(default=None, ge=0, le=1)
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)
    difficulty_felt: Optional[str] = None  # too_easy/right/too_hard
    user_feedback: Optional[str] = None
    skipped_reason: Optional[str] = None
    actual_duration_min: Optional[int] = None


class FeedbackCreate(BaseModel):
    entity_type: str                       # workout_session/meal/recommendation
    entity_id: Optional[int] = None
    feedback_type: str                     # thumbs_up/thumbs_down/rating/text
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    text_feedback: Optional[str] = None


# ─── Sleep Endpoints ─────────────────────────────────────────────────────────

@router.post("/sleep")
async def log_sleep(
    log_data: SleepLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a sleep entry. Feeds the Recovery Agent's readiness computation.
    Sleep < 6h → Recovery Agent reduces workout volume next day.
    """
    log = SleepLog(
        user_id=current_user.id,
        sleep_date=log_data.sleep_date,
        duration_hours=log_data.duration_hours,
        quality_score=log_data.quality_score,
        hrv_ms=log_data.hrv_ms,
        notes=log_data.notes
    )
    db.add(log)
    db.commit()
    return {"message": "Sleep logged successfully", "id": log.id}


@router.get("/sleep")
async def get_sleep_logs(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sleep logs for the last N days."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days)
    logs = db.query(SleepLog).filter(
        SleepLog.user_id == current_user.id,
        SleepLog.sleep_date >= cutoff
    ).order_by(SleepLog.sleep_date.desc()).all()
    return {
        "logs": [{"date": str(l.sleep_date), "hours": l.duration_hours,
                  "quality": l.quality_score, "hrv_ms": l.hrv_ms} for l in logs],
        "avg_quality": round(
            sum(l.quality_score or 0 for l in logs) / len(logs), 1
        ) if logs else 0,
        "avg_hours": round(
            sum(l.duration_hours or 0 for l in logs) / len(logs), 1
        ) if logs else 0,
    }


# ─── Hydration Endpoints ──────────────────────────────────────────────────────

@router.post("/hydration")
async def log_hydration(
    log_data: HydrationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log daily hydration. Nutrition Agent uses this to adjust electrolyte
    recommendations during high-volume training weeks.
    """
    log = HydrationLog(
        user_id=current_user.id,
        log_date=log_data.log_date,
        water_ml=log_data.water_ml,
        target_ml=log_data.target_ml or 2500
    )
    db.add(log)
    db.commit()
    return {"message": "Hydration logged", "id": log.id}


@router.get("/hydration")
async def get_hydration_logs(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=days)
    logs = db.query(HydrationLog).filter(
        HydrationLog.user_id == current_user.id,
        HydrationLog.log_date >= cutoff
    ).order_by(HydrationLog.log_date.desc()).all()
    return {"logs": [{"date": str(l.log_date), "water_ml": l.water_ml,
                      "target_ml": l.target_ml} for l in logs]}


# ─── Progress Endpoints ───────────────────────────────────────────────────────

@router.post("/progress")
async def log_progress(
    data: ProgressMetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log body composition metrics. Used by Planner Agent for weight trend analysis
    (plateau detection and goal completion evaluation).
    """
    metric = ProgressMetric(
        user_id=current_user.id,
        weight_kg=data.weight_kg,
        body_fat_pct=data.body_fat_pct,
        waist_cm=data.waist_cm,
        notes=data.notes
    )
    db.add(metric)
    db.commit()
    return {"message": "Progress logged", "id": metric.id}


@router.get("/progress")
async def get_progress_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    metrics = db.query(ProgressMetric).filter(
        ProgressMetric.user_id == current_user.id
    ).order_by(ProgressMetric.recorded_at.desc()).limit(limit).all()
    return {"history": [{
        "date": m.recorded_at.date().isoformat(),
        "weight_kg": m.weight_kg,
        "body_fat_pct": m.body_fat_pct,
        "notes": m.notes
    } for m in metrics]}


# ─── Workout Feedback Endpoints ───────────────────────────────────────────────

@router.post("/workout-feedback")
async def submit_workout_feedback(
    feedback: WorkoutFeedbackSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit post-workout feedback. This is a primary learning signal:
    - difficulty_felt feeds the Recovery Agent calibration
    - user_rating feeds CSAT metric
    - Completion triggers behavioral memory extraction
    """
    session = db.query(WorkoutSession).filter(
        WorkoutSession.id == feedback.session_id,
        WorkoutSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Apply feedback to session
    if feedback.status:
        session.status = feedback.status
    if feedback.completion_pct is not None:
        session.completion_pct = feedback.completion_pct
    if feedback.user_rating is not None:
        session.user_rating = feedback.user_rating
    if feedback.difficulty_felt:
        session.difficulty_felt = feedback.difficulty_felt
    if feedback.user_feedback:
        session.user_feedback = feedback.user_feedback
    if feedback.skipped_reason:
        session.skipped_reason = feedback.skipped_reason
    if feedback.actual_duration_min:
        session.actual_duration_min = feedback.actual_duration_min

    db.commit()

    # Trigger behavioral memory extraction on completion
    if feedback.status in ("completed", "partial"):
        try:
            from app.services.memory_service import MemoryService
            MemoryService.extract_memories_from_behavior(db, current_user.id)
        except Exception as e:
            print(f"Memory extraction error (non-fatal): {e}")

    # Log evaluation metrics
    try:
        from app.services.evaluation_service import EvaluationService
        if feedback.difficulty_felt:
            EvaluationService.log_metric(
                db, current_user.id,
                "difficulty_felt_right",
                1.0 if feedback.difficulty_felt == "right" else 0.0
            )
    except Exception:
        pass

    return {"message": "Feedback saved", "session_id": feedback.session_id}


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generic feedback endpoint. Every thumbs up/down and rating is a labeled
    training example for evaluation and potential future fine-tuning.
    """
    event = FeedbackEvent(
        user_id=current_user.id,
        entity_type=feedback.entity_type,
        entity_id=feedback.entity_id,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        text_feedback=feedback.text_feedback
    )
    db.add(event)
    db.commit()
    return {"message": "Feedback recorded", "id": event.id}
