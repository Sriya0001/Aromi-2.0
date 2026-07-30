from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.models.medical import MedicalCondition, InjuryRecord
from app.schemas.user import (
    UserResponse, HealthProfileUpdate, HealthProfileResponse,
    MedicalConditionCreate, InjuryCreate
)

router = APIRouter(prefix="/users", tags=["Users"])


def _get_or_create_profile(db: Session, user_id: int) -> HealthProfile:
    """Get existing health profile or create a new one."""
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
    if not profile:
        profile = HealthProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _build_user_response(user: User, profile: HealthProfile) -> dict:
    """Build backward-compatible user response including flat legacy fields."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "calendar_sync": user.calendar_sync,
        "assessment_completed": profile.assessment_completed if profile else "no",
        "google_token_data": user.google_token_data,
        "created_at": user.created_at,
        # Legacy flat fields for frontend backward compat
        "age": profile.age if profile else None,
        "gender": profile.gender if profile else None,
        "height": int(profile.height_cm) if profile and profile.height_cm else None,
        "weight": int(profile.weight_kg) if profile and profile.weight_kg else None,
        "fitness_level": profile.fitness_level if profile else None,
        "fitness_goal": (profile.primary_goal or profile.fitness_goal) if profile else None,
        "workout_preference": (profile.workout_location or profile.workout_preference) if profile else None,
        "workout_time": (profile.preferred_workout_time or profile.workout_time) if profile else None,
        "diet_preference": (profile.diet_type or profile.diet_preference) if profile else None,
        "allergies": profile.allergies if profile else None,
        "health_conditions": profile.health_conditions if profile else None,
        "injuries": profile.injuries if profile else None,
        "medications": profile.medications if profile else None,
        "medical_history": profile.medical_history if profile else None,
    }


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    return _build_user_response(current_user, profile)


@router.get("/profile", response_model=HealthProfileResponse)
async def get_health_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the user's full health profile."""
    profile = _get_or_create_profile(db, current_user.id)
    return profile


@router.put("/profile")
async def update_profile(
    profile_data: HealthProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update health profile. Creates profile if it doesn't exist."""
    profile = _get_or_create_profile(db, current_user.id)
    data = profile_data.model_dump(exclude_unset=True)

    # Update health profile fields
    for field, value in data.items():
        if hasattr(profile, field) and value is not None:
            setattr(profile, field, value)

    # Also update user-level calendar_sync if provided
    if "calendar_sync" in data:
        current_user.calendar_sync = data["calendar_sync"]

    # Check profile completeness (core fields filled)
    core_fields = ["age", "gender", "fitness_level", "primary_goal"]
    legacy_check = ["fitness_goal"]
    is_complete = any(
        getattr(profile, f) for f in core_fields
    ) or any(
        getattr(profile, f) for f in legacy_check
    )
    if data.get("assessment_completed") == "yes" or is_complete:
        profile.assessment_completed = "yes"
        profile.profile_complete = True

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return _build_user_response(current_user, profile)


@router.post("/medical-conditions")
async def add_medical_condition(
    condition: MedicalConditionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a medical condition to the user's profile."""
    # Apply medical safety filter rules
    safety_rules = {
        "HeartDisease": {"exercise_restrictions": ["no_hiit", "hr_cap_120", "no_valsalva"]},
        "Hypertension": {"exercise_restrictions": ["no_valsalva", "hr_cap_130"]},
        "Type2Diabetes": {"exercise_restrictions": ["post_meal_preferred"]},
        "Arthritis": {"exercise_restrictions": ["no_high_impact", "low_joint_stress"]},
        "PCOS": {"exercise_restrictions": ["strength_priority"]},
        "Asthma": {"exercise_restrictions": ["extended_warmup", "avoid_cold_weather"]},
        "KneePain": {"exercise_restrictions": ["no_deep_knee_flexion", "no_running"]},
        "BackPain": {"exercise_restrictions": ["no_heavy_deadlift", "no_sit_ups"]},
        "ShoulderPain": {"exercise_restrictions": ["no_overhead_press", "no_pull_ups"]},
    }
    rules = safety_rules.get(condition.condition_name, {})
    
    db_condition = MedicalCondition(
        user_id=current_user.id,
        condition_name=condition.condition_name,
        severity=condition.severity,
        diagnosed_year=condition.diagnosed_year,
        medications=condition.medications,
        exercise_restrictions=rules.get("exercise_restrictions"),
        notes=condition.notes
    )
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    return db_condition

@router.get("/medical-conditions")
async def get_medical_conditions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the user's medical conditions."""
    return db.query(MedicalCondition).filter(MedicalCondition.user_id == current_user.id).all()

@router.post("/injuries")
async def add_injury(
    injury: InjuryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an injury record to the user's profile."""
    db_injury = InjuryRecord(
        user_id=current_user.id,
        body_part=injury.body_part,
        injury_type=injury.injury_type,
        is_current=injury.is_current,
        severity=injury.severity,
        restrictions=injury.restrictions,
        notes=injury.notes
    )
    db.add(db_injury)
    db.commit()
    db.refresh(db_injury)
    return db_injury

@router.get("/injuries")
async def get_injuries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the user's injury records."""
    return db.query(InjuryRecord).filter(InjuryRecord.user_id == current_user.id).all()
