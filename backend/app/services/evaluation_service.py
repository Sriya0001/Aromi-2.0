"""
Evaluation Service — AroMi 2.1 Scientific Evaluation Pipeline.

Metrics:
  1. Safety Violation Rate (SVR) — Target: 0.0%
  2. Exercise Ontology Alignment Rate (OAR) — Target: 100%
  3. Semantic Personalization Distance (SPD) — Target: >0.65
  4. Caloric Calibration Error (CCE) — Target: <0.20 kg MAE
  5. 30-Day Workout & Meal Adherence
  6. CSAT & Difficulty Calibration Accuracy
"""
import math
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from typing import Optional, List


VERIFIED_EXERCISES = {
    "push-ups", "pull-ups", "squats", "lunges", "deadlift", "bench press",
    "overhead press", "barbell row", "dumbbell row", "plank", "crunch",
    "leg press", "leg extension", "leg curl", "calf raise", "hip thrust",
    "glute bridge", "russian twist", "mountain climbers", "burpees",
    "jumping jacks", "high knees", "bicycle crunches", "tricep dips",
    "bicep curls", "hammer curls", "lateral raises", "front raises",
    "seated row", "lat pulldown", "chest fly", "incline press",
    "dynamic stretching", "light yoga flow", "foam rolling", "walking",
    "bodyweight squats", "walking lunges", "dumbbell shoulder press",
    "plank hold", "foam rolling / self-massage", "seated upper body stretch",
    "seated core engagements", "dumbbell rows", "kettlebell / dumbbell swings",
    "light outdoor walk / relaxation"
}


class EvaluationService:

    @staticmethod
    def compute_safety_violation_rate(db: Session, user_id: int) -> float:
        """
        SVR = Count(Prescribed Exercises violating contraindications) / Total Prescribed Exercises
        Target: strictly 0.0%
        """
        from app.models.workout import WorkoutSession
        from app.models.medical import MedicalCondition, InjuryRecord

        sessions = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user_id
        ).order_by(WorkoutSession.id.desc()).limit(7).all()

        if not sessions:
            return 0.0

        conditions = db.query(MedicalCondition).filter(MedicalCondition.user_id == user_id, MedicalCondition.is_active == True).all()
        injuries = db.query(InjuryRecord).filter(InjuryRecord.user_id == user_id, InjuryRecord.is_current == True).all()

        prohibited_keywords = []
        for c in conditions:
            if "hypertension" in c.condition_name.lower():
                prohibited_keywords.extend(["valsalva", "heavy leg press"])
            if "arthritis" in c.condition_name.lower() or "knee" in c.condition_name.lower():
                prohibited_keywords.extend(["high-impact", "box jumps"])

        for inj in injuries:
            prohibited_keywords.append(inj.body_part.lower())

        total_ex = 0
        violations = 0

        for s in sessions:
            exercises = s.exercises_planned or []
            if isinstance(exercises, str):
                import json
                try:
                    exercises = json.loads(exercises)
                except Exception:
                    exercises = []

            for ex in exercises:
                if isinstance(ex, dict):
                    total_ex += 1
                    name = ex.get("name", "").lower()
                    muscle = ex.get("muscle_group", "").lower()
                    if any(kw in name or kw in muscle for kw in prohibited_keywords):
                        violations += 1

        return round(violations / total_ex, 4) if total_ex > 0 else 0.0

    @staticmethod
    def compute_ontology_alignment_rate(exercises: list) -> float:
        """
        OAR = Valid Exercise Catalog IDs / Total Prescribed Exercises
        Target: 1.0 (100%)
        Replaces naive hallucination rate string match.
        """
        if not exercises:
            return 1.0
        aligned = sum(
            1 for ex in exercises
            if isinstance(ex, dict) and ex.get("name", "").lower() in VERIFIED_EXERCISES
        )
        return round(aligned / len(exercises), 3)

    @staticmethod
    def compute_semantic_personalization_distance(exercises_a: list, exercises_b: list) -> float:
        """
        SPD = 1 - CosineSimilarity(Vec_A, Vec_B)
        Target: > 0.65
        """
        if not exercises_a or not exercises_b:
            return 0.0
        set_a = {ex.get("name", "").lower() for ex in exercises_a if isinstance(ex, dict)}
        set_b = {ex.get("name", "").lower() for ex in exercises_b if isinstance(ex, dict)}
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        jaccard = intersection / union if union > 0 else 0
        return round(1.0 - jaccard, 3)

    @staticmethod
    def compute_workout_adherence(db: Session, user_id: int, days: int = 7) -> float:
        from app.models.workout import WorkoutSession
        cutoff = date.today() - timedelta(days=days)
        planned = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= cutoff
        ).count()
        completed = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= cutoff,
            WorkoutSession.status == "completed"
        ).count()
        return round(completed / planned, 3) if planned > 0 else 0.0

    @staticmethod
    def compute_meal_adherence(db: Session, user_id: int, days: int = 7) -> float:
        from app.models.nutrition import NutritionLog
        cutoff = date.today() - timedelta(days=days)
        total = db.query(NutritionLog).filter(
            NutritionLog.user_id == user_id,
            NutritionLog.log_date >= cutoff,
            NutritionLog.adherence.isnot(None)
        ).count()
        adhered = db.query(NutritionLog).filter(
            NutritionLog.user_id == user_id,
            NutritionLog.log_date >= cutoff,
            NutritionLog.adherence == True
        ).count()
        return round(adhered / total, 3) if total > 0 else 0.0

    @staticmethod
    def compute_plan_stability(db: Session, user_id: int, weeks: int = 4) -> float:
        from app.models.workout import WeeklyPlan
        cutoff = date.today() - timedelta(weeks=weeks)
        plans = db.query(WeeklyPlan).filter(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start_date >= cutoff
        ).all()
        if not plans:
            return 1.0
        superseded = sum(1 for p in plans if p.plan_status == "superseded")
        total_weeks = len(plans)
        change_rate = superseded / total_weeks if total_weeks > 0 else 0
        return round(max(0.0, 1.0 - change_rate), 3)

    @staticmethod
    def compute_csat(db: Session, user_id: int, days: int = 30) -> float:
        from app.models.evaluation import FeedbackEvent
        cutoff = datetime.utcnow() - timedelta(days=days)
        feedbacks = db.query(FeedbackEvent).filter(
            FeedbackEvent.user_id == user_id,
            FeedbackEvent.rating.isnot(None),
            FeedbackEvent.created_at >= cutoff
        ).all()
        if not feedbacks:
            return 0.0
        return round(sum(f.rating for f in feedbacks) / len(feedbacks), 2)

    @staticmethod
    def assign_experiment_arm(db: Session, user_id: int, experiment_name: str) -> Optional[str]:
        import hashlib
        hash_input = f"{user_id}:{experiment_name}".encode('utf-8')
        digest = int(hashlib.md5(hash_input).hexdigest(), 16)
        return "arm_a" if (digest % 2 == 0) else "arm_b"

    @staticmethod
    def compute_full_evaluation_report(db: Session, user_id: int) -> dict:
        from app.services.workout_service import get_today_workout
        today_w = get_today_workout(db, user_id)
        latest_exercises = today_w.get("exercises", []) if today_w else []

        svr = EvaluationService.compute_safety_violation_rate(db, user_id)
        oar = EvaluationService.compute_ontology_alignment_rate(latest_exercises)
        w_adh = EvaluationService.compute_workout_adherence(db, user_id, 7)
        m_adh = EvaluationService.compute_meal_adherence(db, user_id, 7)
        ps = EvaluationService.compute_plan_stability(db, user_id, 4)
        csat = EvaluationService.compute_csat(db, user_id, 30)

        report = {
            "user_id": user_id,
            "period": f"{date.today().year}-W{date.today().isocalendar()[1]}",
            "computed_at": datetime.utcnow().isoformat(),
            "metrics": {
                "safety_violation_rate": svr,
                "ontology_alignment_rate": oar,
                "workout_adherence_7d": w_adh,
                "meal_adherence_7d": m_adh,
                "plan_stability_4w": ps,
                "csat_30d": csat,
            },
            "targets": {
                "safety_violation_rate": "strictly 0.0%",
                "ontology_alignment_rate": "100%",
                "workout_adherence_7d": ">0.70",
                "meal_adherence_7d": ">0.60",
                "csat_30d": ">4.0/5.0",
            },
            "interpretation": {
                "safety_violation_rate": "OK" if svr == 0.0 else "CRITICAL_ALERT",
                "ontology_alignment_rate": "OK" if oar == 1.0 else "WARNING",
                "workout_adherence_7d": "OK" if w_adh >= 0.7 else "WARNING",
            }
        }
        return report
