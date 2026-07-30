"""
AI Router — AroMi 2.0 multi-agent endpoints.

Key endpoints:
  POST /ai/chat          — Chat with AROMI (Groq SDK + intent detection engine)
  POST /ai/generate-plan — Generate weekly plan via Planner Agent (new)
  POST /ai/adaptive-regen — Adaptive regeneration via Planner Agent (new)
  GET  /ai/chat/history  — Chat history
  GET  /ai/session-reasoning/{id} — Explainability for a specific session

WHY keep /chat backward-compatible:
  The existing intent-detection chat is still useful for
  real-time plan modifications (remove exercise, compress workout, etc.).
  The /generate-plan endpoint handles full weekly plan generation via agents.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession
from app.schemas.fitness import ChatRequest
from app.services.ai_service import chat_with_aromi
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI Coach"])


def _build_user_profile_from_db(user: User, db: Session) -> dict:
    """
    Build a complete user profile dict from the new HealthProfile model,
    with keys expected by intent_service.py.
    """
    from app.models.health_profile import HealthProfile
    profile = db.query(HealthProfile).filter(
        HealthProfile.user_id == user.id
    ).first()

    if profile:
        hp = profile.to_agent_context()
        # Keys expected by intent_service.py
        hp["age"] = hp.get("age")
        hp["gender"] = hp.get("gender")
        hp["weight"] = hp.get("weight_kg")
        hp["height"] = hp.get("height_cm")
        hp["fitness_goal"] = hp.get("primary_goal")
        hp["workout_preference"] = hp.get("workout_location")
        hp["workout_time"] = hp.get("preferred_workout_time")
        hp["diet_preference"] = hp.get("diet_type")
        hp["health_conditions"] = profile.health_conditions
        hp["injuries"] = profile.injuries
        hp["username"] = user.username
        return hp
    else:
        # Fallback for users without a health profile yet
        return {
            "age": None, "gender": None, "weight": 70, "height": 170,
            "fitness_level": "beginner", "fitness_goal": "general_fitness",
            "workout_preference": "home", "workout_time": "flexible",
            "diet_preference": "vegetarian", "allergies": "none",
            "health_conditions": "none", "injuries": "none",
            "username": user.username
        }


def _get_agent_context(user: User, db: Session):
    """Build full AgentContext for multi-agent plan generation."""
    from app.agents.base import AgentContext
    from app.models.health_profile import HealthProfile
    from app.models.medical import MedicalCondition, InjuryRecord
    from app.services.memory_service import MemoryService

    profile = db.query(HealthProfile).filter(
        HealthProfile.user_id == user.id
    ).first()
    hp_dict = profile.to_agent_context() if profile else {}

    conditions = db.query(MedicalCondition).filter(
        MedicalCondition.user_id == user.id,
        MedicalCondition.is_active == True
    ).all()
    medical = [
        {"condition": c.condition_name, "restrictions": c.exercise_restrictions or []}
        for c in conditions
    ]

    injuries = db.query(InjuryRecord).filter(
        InjuryRecord.user_id == user.id,
        InjuryRecord.is_current == True
    ).all()
    injury_list = [
        {"body_part": i.body_part, "restrictions": i.restrictions or []}
        for c in injuries
    ]

    memory_context = MemoryService.get_user_memory_context(db, user.id)

    return AgentContext(
        user_id=user.id,
        health_profile=hp_dict,
        medical_conditions=medical,
        injury_restrictions=injury_list,
        long_term_memory=memory_context,
        db=db
    )


# ─── Chat Endpoint (Groq SDK + Intent Engine) ───────────────────────────

@router.post("/chat")
async def chat_with_aromi_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with AROMI AI coach.
    Uses Groq SDK + intent detection for real-time plan modifications.
    """
    user_profile = _build_user_profile_from_db(current_user, db)

    # Get recent chat history (working memory — last 6 turns)
    recent_chats = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.timestamp.desc()).limit(6).all()

    chat_history = [
        {"message": c.message, "response": c.response}
        for c in reversed(recent_chats)
    ]

    response_text, plan_modified = await chat_with_aromi(
        user_message=request.message,
        user_profile=user_profile,
        chat_history=chat_history,
        db=db,
        user_id=current_user.id
    )

    return {
        "response": response_text,
        "plan_modified": plan_modified,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/chat/history")
def get_chat_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AROMI chat history."""
    chats = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.timestamp.asc()).limit(limit).all()

    return {
        "history": [
            {
                "id": c.id,
                "message": c.message,
                "response": c.response,
                "timestamp": c.timestamp.isoformat()
            }
            for c in chats
        ]
    }


# ─── Multi-Agent Plan Generation (new) ───────────────────────────────────────

@router.post("/generate-plan")
async def generate_full_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a personalized weekly plan using the multi-agent Planner.

    Flow:
      1. Recovery Agent computes readiness score
      2. Workout + Nutrition agents run in PARALLEL (conditioned on recovery)
      3. Planner Agent resolves conflicts, applies adaptation algorithm
      4. Plan persisted to DB with full generation_context snapshot
      5. Evaluation metrics logged automatically

    Returns explainability reasoning for every recommendation.
    """
    from app.agents.planner_agent import PlannerAgent

    context = _get_agent_context(current_user, db)
    planner = PlannerAgent(groq_api_key=settings.GROQ_API_KEY)

    try:
        output = await planner.run(context)
        return {
            "status": "success" if output.success else "partial",
            "message": "Your personalized plan is ready!" if output.success
                       else "Plan generated with warnings.",
            "plan_id": output.data.get("plan_id"),
            "workout_plan": output.data.get("workout_plan", []),
            "nutrition_plan": output.data.get("nutrition_plan", []),
            "recovery_signal": output.data.get("recovery_signal"),
            "adaptation_action": output.data.get("adaptation_action"),
            "caloric_target": output.data.get("caloric_target"),
            "macro_split": output.data.get("macro_split"),
            "hydration_target_ml": output.data.get("hydration_target_ml"),
            "reasoning": output.reasoning,
            "warnings": output.warnings,
            "latency_ms": output.latency_ms,
            "tokens_used": output.token_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adaptive-regen")
async def trigger_adaptive_regen(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adaptive plan regeneration using the Planner Agent.
    Analyzes last 7 days of adherence, recovery, and feedback
    to decide the adaptation action before generating the new plan.
    """
    return await generate_full_plan(current_user=current_user, db=db)


# ─── Explainability Endpoint (new) ───────────────────────────────────────────

@router.get("/session-reasoning/{session_id}")
async def get_session_reasoning(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the full explainability reasoning for a specific workout session.
    This answers: "Why did AroMi recommend these exercises for this session?"
    """
    from app.models.workout import WorkoutSession
    session = db.query(WorkoutSession).filter(
        WorkoutSession.id == session_id,
        WorkoutSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "day_name": session.day_name,
        "focus_area": session.focus_area,
        "reasoning": session.reasoning or (
            "This session was generated before the AroMi 2.0 explainability system. "
            "Generate a new plan to see full reasoning."
        ),
        "agent_version": session.agent_version or "legacy",
        "exercises": session.exercises_planned or [],
    }
