from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional, List, Any
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class HealthProfileUpdate(BaseModel):
    """Comprehensive health profile — every field feeds downstream recommendations."""
    # Biometrics
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None

    # Fitness context
    fitness_level: Optional[str] = None
    activity_level: Optional[str] = None
    occupation_type: Optional[str] = None
    years_training: Optional[float] = None

    # Goals
    primary_goal: Optional[str] = None
    secondary_goal: Optional[str] = None
    target_weight_kg: Optional[float] = None
    goal_deadline_weeks: Optional[int] = None

    # Schedule
    available_days_per_week: Optional[int] = None
    session_duration_min: Optional[int] = None
    preferred_workout_time: Optional[str] = None
    workout_location: Optional[str] = None
    equipment_available: Optional[List[str]] = None

    # Dietary
    diet_type: Optional[str] = None
    meal_frequency: Optional[int] = None
    food_allergies: Optional[List[str]] = None
    cuisine_preference: Optional[List[str]] = None
    weekly_food_budget_usd: Optional[float] = None

    # Lifestyle
    sleep_hours_avg: Optional[float] = None
    sleep_quality: Optional[str] = None
    stress_level: Optional[int] = None
    water_intake_liters: Optional[float] = None
    smoking: Optional[bool] = None
    alcohol_units_week: Optional[int] = None

    # Clinical
    is_pregnant: Optional[bool] = None
    pregnancy_trimester: Optional[int] = None

    # Adherence predictors
    motivation_level: Optional[int] = None
    past_program_adherence: Optional[str] = None
    reason_for_starting: Optional[str] = None

    # Legacy (for backward compat)
    fitness_goal: Optional[str] = None
    workout_preference: Optional[str] = None
    workout_time: Optional[str] = None
    diet_preference: Optional[str] = None
    allergies: Optional[str] = None
    health_conditions: Optional[str] = None
    injuries: Optional[str] = None
    medications: Optional[str] = None
    medical_history: Optional[str] = None
    calendar_sync: Optional[str] = None
    assessment_completed: Optional[str] = None


# Keep old UserProfile alias for backward compat
UserProfile = HealthProfileUpdate


class MedicalConditionCreate(BaseModel):
    condition_name: str
    severity: Optional[str] = None
    diagnosed_year: Optional[int] = None
    medications: Optional[List[str]] = None
    notes: Optional[str] = None


class InjuryCreate(BaseModel):
    body_part: str
    injury_type: Optional[str] = None
    is_current: bool = False
    severity: Optional[str] = None
    restrictions: Optional[List[str]] = None
    notes: Optional[str] = None


class HealthProfileResponse(BaseModel):
    id: int
    user_id: int
    age: Optional[int]
    gender: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    body_fat_pct: Optional[float]
    fitness_level: Optional[str]
    activity_level: Optional[str]
    primary_goal: Optional[str]
    secondary_goal: Optional[str]
    available_days_per_week: Optional[int]
    session_duration_min: Optional[int]
    preferred_workout_time: Optional[str]
    workout_location: Optional[str]
    equipment_available: Optional[Any]
    diet_type: Optional[str]
    food_allergies: Optional[Any]
    cuisine_preference: Optional[Any]
    sleep_hours_avg: Optional[float]
    stress_level: Optional[int]
    motivation_level: Optional[int]
    profile_complete: Optional[bool]
    assessment_completed: Optional[str]
    # Legacy
    fitness_goal: Optional[str]
    workout_preference: Optional[str]
    diet_preference: Optional[str]
    allergies: Optional[str]
    health_conditions: Optional[str]
    injuries: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    calendar_sync: Optional[str] = None
    # assessment_completed lives on HealthProfile in v2.0; default None for backward compat
    assessment_completed: Optional[str] = None
    google_token_data: Optional[str] = None
    created_at: datetime
    health_profile: Optional[HealthProfileResponse] = None

    # Legacy flat fields — auto-populated from health_profile relationship
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    fitness_level: Optional[str] = None
    fitness_goal: Optional[str] = None
    workout_preference: Optional[str] = None
    workout_time: Optional[str] = None
    diet_preference: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    health_conditions: Optional[str] = None
    injuries: Optional[str] = None
    medications: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def populate_legacy_fields(cls, values):
        """
        Auto-populate legacy flat fields from the health_profile relationship
        so old frontend code that reads user.fitness_goal etc. keeps working.
        """
        # When Pydantic receives an ORM object, access attributes directly
        if hasattr(values, 'health_profile') and values.health_profile:
            hp = values.health_profile
            # assessment_completed lives on HealthProfile now
            if not getattr(values, 'assessment_completed', None):
                object.__setattr__(values, 'assessment_completed',
                                   getattr(hp, 'assessment_completed', None))
        return values

    class Config:
        from_attributes = True
