"""
Evaluation router — exposes evaluation metrics, experiment management,
and the internal evaluation dashboard for AroMi 2.0.

WHY this is public-facing:
- Transparency to users (they can see their adherence metrics)
- Internal team dashboard for monitoring recommendation quality
- A/B experiment results for Applied Scientist review
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/report")
async def get_evaluation_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Full evaluation report for the current user.
    Computes all 10 AroMi metrics and auto-logs them to DB.
    Includes interpretation flags (OK/WARNING/CRITICAL/ALERT).
    """
    return EvaluationService.compute_full_evaluation_report(db, current_user.id)


@router.get("/adherence")
async def get_adherence_metrics(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Workout and meal adherence metrics for a given time window.
    Primary metric for plan quality assessment.
    """
    return {
        "workout_adherence": EvaluationService.compute_workout_adherence(
            db, current_user.id, days
        ),
        "meal_adherence": EvaluationService.compute_meal_adherence(
            db, current_user.id, days
        ),
        "period_days": days,
        "targets": {"workout": ">0.70", "meal": ">0.60"}
    }


@router.get("/diversity")
async def get_diversity_score(
    weeks: int = 4,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exercise diversity score over N weeks.
    Target: >0.40 — more than 40% of exercise instances are unique names.
    """
    return {
        "diversity_score": EvaluationService.compute_diversity_score(
            db, current_user.id, weeks
        ),
        "target": ">0.40",
        "period_weeks": weeks,
        "interpretation": "Higher score = more exercise variety in recommendations"
    }


@router.get("/satisfaction")
async def get_satisfaction(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """CSAT and recommendation accuracy (difficulty calibration)."""
    return {
        "csat": EvaluationService.compute_csat(db, current_user.id),
        "recommendation_accuracy": EvaluationService.compute_recommendation_accuracy(
            db, current_user.id
        ),
        "targets": {"csat": ">4.0/5.0", "recommendation_accuracy": ">0.65"},
        "note": "recommendation_accuracy = % sessions rated as 'just right' difficulty"
    }


@router.get("/plan-stability")
async def get_plan_stability(
    weeks: int = 4,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Plan stability — measures how consistently plans are maintained.
    Target: >0.70. Plans should change for good reasons, not arbitrarily.
    """
    return {
        "plan_stability": EvaluationService.compute_plan_stability(
            db, current_user.id, weeks
        ),
        "target": ">0.70",
        "period_weeks": weeks,
    }


@router.post("/assign-experiment")
async def assign_experiment(
    experiment_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign the current user to an experiment arm (A or B).
    Assignment is deterministic (hash-based) — same user always gets same arm.
    """
    arm = EvaluationService.assign_experiment_arm(
        db, current_user.id, experiment_name
    )
    if arm is None:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment '{experiment_name}' not found or inactive"
        )
    return {
        "experiment": experiment_name,
        "arm": arm,
        "user_id": current_user.id,
        "note": "Deterministic assignment — will always return same arm for this user"
    }


@router.get("/history")
async def get_metric_history(
    metric_name: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get historical evaluation metric values for trend analysis."""
    from app.models.evaluation import EvaluationMetric
    query = db.query(EvaluationMetric).filter(
        EvaluationMetric.user_id == current_user.id
    )
    if metric_name:
        query = query.filter(EvaluationMetric.metric_name == metric_name)
    metrics = query.order_by(
        EvaluationMetric.computed_at.desc()
    ).limit(limit).all()

    return {
        "history": [{
            "metric": m.metric_name,
            "value": m.metric_value,
            "computed_at": m.computed_at.isoformat()
        } for m in metrics]
    }
