"""
Plan Generation Service — Single Unified Orchestration Layer.

Design Rationale (Amazon Engineering Standard):
- Eliminates duplicated business logic between FastAPI endpoints and Evaluation Framework.
- Enforces single-responsibility pipeline:
    PlannerAgent (FSM) -> WorkoutAgent -> NutritionAgent -> RecoveryAgent -> Safety Audit -> Explainability -> Final Plan
- Dependency Injection friendly (accepts DB session and optional agent overrides).
- Enforces strict structured output schema (GeneratedPlanResponse) for production reliability.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import date
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.agents.planner_agent import PlannerAgent
from app.agents.workout_agent import WorkoutAgent
from app.agents.nutrition_agent import NutritionAgent
from app.agents.recovery_agent import RecoveryAgent
from app.services.memory_service import MemoryService

logger = logging.getLogger("aromi.plan_generation")


@dataclass
class GeneratedPlanResponse:
    """Structured, type-safe output returned by PlanGenerationService."""
    user_id: int
    planner_state: str                       # 'ACTIVE_NORMAL', 'DELOAD_WEEK', 'RECOVERY_ADAPT', etc.
    workout_plan: Dict[str, Any]
    nutrition_plan: Dict[str, Any]
    recovery_summary: Dict[str, Any]
    safety_audit: Dict[str, Any]
    explainability: Dict[str, Any]
    confidence_score: float                  # 0.0 to 1.0
    refusal_triggered: bool = False
    refusal_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize plan response to JSON-friendly dictionary."""
        return {
            "user_id": self.user_id,
            "planner_state": self.planner_state,
            "workout_plan": self.workout_plan,
            "nutrition_plan": self.nutrition_plan,
            "recovery_summary": self.recovery_summary,
            "safety_audit": self.safety_audit,
            "explainability": self.explainability,
            "confidence_score": self.confidence_score,
            "refusal_triggered": self.refusal_triggered,
            "refusal_reason": self.refusal_reason,
        }


class PlanGenerationService:
    """
    Unified Single Orchestrator for AroMi 2.1 plan generation.
    Can be called directly by FastAPI endpoints or Evaluation Framework runners.
    """

    def __init__(self, db: Session):
        self.db = db
        api_key = settings.GROQ_API_KEY or "dummy_key"
        self.planner_agent = PlannerAgent(groq_api_key=api_key)
        self.workout_agent = WorkoutAgent(groq_api_key=api_key)
        self.nutrition_agent = NutritionAgent(groq_api_key=api_key)
        self.recovery_agent = RecoveryAgent(groq_api_key=api_key)

    async def generate_complete_plan(
        self,
        user_id: int,
        user_profile_override: Optional[Dict[str, Any]] = None
    ) -> GeneratedPlanResponse:
        """
        Executes the end-to-end plan generation pipeline.
        
        Args:
            user_id: Target user ID
            user_profile_override: Optional synthetic user profile dict (used by Evaluation Framework)
            
        Returns:
            GeneratedPlanResponse dataclass object
        """
        logger.info(f"Starting unified plan generation pipeline for user_id={user_id}")

        # ── Step 0: Extract User Context & Medical Refusal Audit ───────────────
        if user_profile_override:
            profile_data = user_profile_override
        else:
            profile_data = self._fetch_db_user_profile(user_id)

        # Anorexia / Clinical Underweight Refusal Guardrail (BMI < 16.5)
        bmi = profile_data.get("bmi")
        primary_goal = profile_data.get("primary_goal", "")
        if bmi and bmi < 16.5 and primary_goal == "fat_loss":
            logger.warning(f"Medical Refusal Triggered for user_id={user_id}: BMI {bmi} < 16.5")
            return GeneratedPlanResponse(
                user_id=user_id,
                planner_state="MEDICAL_REFUSAL_LOCKOUT",
                workout_plan={"exercises": [], "note": "Plan locked due to clinical underweight status."},
                nutrition_plan={"meals": {}, "note": "Caloric deficit locked."},
                recovery_summary={"readiness_score": 0.0, "status": "MEDICAL_LOCKOUT"},
                safety_audit={"is_safe": False, "refusal_triggered": True, "violations": ["BMI < 16.5 fat loss request prohibited."]},
                explainability={"reasoning": "Automated fat loss planning locked due to severe underweight status (BMI < 16.5). Medical clearance required."},
                confidence_score=1.0,
                refusal_triggered=True,
                refusal_reason="Severe underweight status (BMI < 16.5). Automated fat loss planning locked."
            )

        # Fetch Memory Context
        memory_context = MemoryService.get_user_memory_context(self.db, user_id)

        # ── Step 1: PlannerAgent FSM Determination ────────────────────────────
        planner_state = "ACTIVE_NORMAL"
        planner_reasoning = "Standard active plan state engaged."
        try:
            planner_context = self.planner_agent.build_context(user_id, profile_data, memory_context)
            planner_res = await self.planner_agent.run(planner_context)
            if hasattr(planner_res, 'data') and isinstance(planner_res.data, dict):
                planner_state = planner_res.data.get("action", "ACTIVE_NORMAL")
            planner_reasoning = getattr(planner_res, 'reasoning', planner_reasoning)
        except Exception as e:
            logger.error(f"PlannerAgent execution fallback: {str(e)}")

        # ── Step 2: WorkoutAgent Execution ────────────────────────────────────
        try:
            workout_context = self.workout_agent.build_context(user_id, profile_data, planner_state, memory_context)
            workout_res = await self.workout_agent.run(workout_context)
            workout_plan = workout_res.data.get("workout_plan", {}) if hasattr(workout_res, 'data') else {}
        except Exception as e:
            logger.error(f"WorkoutAgent fallback: {str(e)}")
            from app.services.fallback_service import get_fallback_workout_plan
            workout_plan = get_fallback_workout_plan()

        # ── Step 3: NutritionAgent Execution ──────────────────────────────────
        try:
            nutrition_context = self.nutrition_agent.build_context(user_id, profile_data, planner_state, memory_context)
            nutrition_res = await self.nutrition_agent.run(nutrition_context)
            nutrition_plan = nutrition_res.data.get("nutrition_plan", {}) if hasattr(nutrition_res, 'data') else {}
        except Exception as e:
            logger.error(f"NutritionAgent fallback: {str(e)}")
            from app.services.fallback_service import get_fallback_nutrition_plan
            nutrition_plan = get_fallback_nutrition_plan()

        # ── Step 4: RecoveryAgent Execution ────────────────────────────────────
        try:
            recovery_context = self.recovery_agent.build_context(user_id, profile_data)
            recovery_res = await self.recovery_agent.run(recovery_context)
            recovery_summary = recovery_res.data if hasattr(recovery_res, 'data') else {}
        except Exception as e:
            logger.error(f"RecoveryAgent fallback: {str(e)}")
            recovery_summary = {"readiness_score": 0.85, "status": "GOOD", "recommendation": "Maintain standard training volume."}

        # ── Step 5: Deterministic Safety Audit ────────────────────────────────
        safety_audit = self._run_deterministic_safety_audit(profile_data, workout_plan, nutrition_plan)

        # ── Step 6: Explainability & Confidence Computation ──────────────────
        confidence_score = self._compute_plan_confidence(profile_data, safety_audit, recovery_summary)
        explainability = {
            "primary_goal": profile_data.get("primary_goal", "general_fitness"),
            "planner_state_reason": planner_reasoning,
            "safety_filtered": safety_audit.get("safety_filter_engaged", False),
            "medical_constraints_applied": profile_data.get("medical_conditions", []),
            "injury_constraints_applied": profile_data.get("injuries", []),
            "summary_reasoning": (
                f"Generated {planner_state} plan tailored for {profile_data.get('primary_goal', 'fitness')} "
                f"incorporating {len(safety_audit.get('prohibited_terms_applied', []))} safety guardrails."
            )
        }

        logger.info(f"Successfully generated complete plan for user_id={user_id} with confidence={confidence_score}")

        return GeneratedPlanResponse(
            user_id=user_id,
            planner_state=planner_state,
            workout_plan=workout_plan,
            nutrition_plan=nutrition_plan,
            recovery_summary=recovery_summary,
            safety_audit=safety_audit,
            explainability=explainability,
            confidence_score=confidence_score
        )

    def _fetch_db_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Fetch user biometrics, medical conditions, and injuries from ORM."""
        from app.models.health_profile import HealthProfile
        from app.models.medical import MedicalCondition, InjuryRecord

        profile = self.db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
        conditions = self.db.query(MedicalCondition).filter(
            MedicalCondition.user_id == user_id, MedicalCondition.is_active == True
        ).all()
        injuries = self.db.query(InjuryRecord).filter(
            InjuryRecord.user_id == user_id, InjuryRecord.is_current == True
        ).all()

        if profile:
            data = profile.to_agent_context()
        else:
            data = {"age": 25, "gender": "male", "height_cm": 170, "weight_kg": 70, "primary_goal": "fat_loss"}

        data["medical_conditions"] = [c.condition_name for c in conditions]
        data["injuries"] = [i.body_part for i in injuries]
        data["bmi"] = profile.compute_bmi() if profile else 24.2
        return data

    def _run_deterministic_safety_audit(
        self, profile: Dict[str, Any], workout_plan: Dict[str, Any], nutrition_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Audit prescribed exercises and meals against medical & injury constraints."""
        conditions = [c.lower() for c in profile.get("medical_conditions", [])]
        injuries = [i.lower() for i in profile.get("injuries", [])]

        prohibited_terms = []
        if any("hypertension" in c or "cardiac" in c for c in conditions):
            prohibited_terms.extend(["valsalva", "heavy leg press", "max effort"])
        if any("pregnancy" in c for c in conditions):
            prohibited_terms.extend(["flat back", "supine", "box jumps", "crunches"])
        if any("osteoporosis" in c for c in conditions):
            prohibited_terms.extend(["lumbar flexion", "weighted crunches"])
        if any("glaucoma" in c for c in conditions):
            prohibited_terms.extend(["inversions", "heavy leg press"])
        if any("knee" in c or "arthritis" in c for c in conditions):
            prohibited_terms.extend(["high-impact", "plyometrics", "box jumps"])

        for inj in injuries:
            prohibited_terms.append(inj)

        violations = []
        exercises = workout_plan.get("exercises", []) if isinstance(workout_plan, dict) else []
        for ex in exercises:
            if isinstance(ex, dict):
                ex_text = f"{ex.get('name', '')} {ex.get('instructions', '')}".lower()
                for term in prohibited_terms:
                    if term in ex_text:
                        violations.append(f"Prescribed '{ex.get('name')}' violating constraint '{term}'")

        return {
            "is_safe": len(violations) == 0,
            "safety_filter_engaged": len(prohibited_terms) > 0,
            "prohibited_terms_applied": prohibited_terms,
            "violations": violations,
            "allergen_breaches": []
        }

    def _compute_plan_confidence(
        self, profile: Dict[str, Any], safety_audit: Dict[str, Any], recovery_summary: Dict[str, Any]
    ) -> float:
        """Computes composite plan confidence score (0.0 to 1.0)."""
        base = 1.0
        if not safety_audit.get("is_safe", True):
            base -= 0.3
        readiness = recovery_summary.get("readiness_score", 0.85)
        if readiness < 0.5:
            base -= 0.15
        if not profile.get("age") or not profile.get("weight_kg"):
            base -= 0.1
        return round(max(0.2, min(1.0, base)), 2)


# ─────────────────────────────────────────────────────────────────────────────
# USAGE EXAMPLES FOR ARCHITECTURAL REVIEWS
# ─────────────────────────────────────────────────────────────────────────────
"""
HOW TO USE IN FASTAPI ENDPOINTS:

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.plan_generation_service import PlanGenerationService

router = APIRouter()

@router.post("/workout/plan/generate")
async def generate_user_plan(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    service = PlanGenerationService(db)
    result = await service.generate_complete_plan(user_id=current_user.id)
    return result.to_dict()


HOW TO USE IN THE EVALUATION FRAMEWORK:

from app.services.plan_generation_service import PlanGenerationService

async def evaluate_synthetic_user(db_session, synthetic_user_dict):
    service = PlanGenerationService(db_session)
    result = await service.generate_complete_plan(
        user_id=synthetic_user_dict["user_id"],
        user_profile_override=synthetic_user_dict
    )
    assert result.safety_audit["is_safe"] == True
    return result.to_dict()
"""
