"""
HealthProfile — the feature vector for all downstream recommendations.
Stored separately from User (auth) for privacy boundaries and versioning.
Every field here changes at least one downstream recommendation.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    version = Column(Integer, default=1)

    # ── Biometrics ───────────────────────────────────────────
    # WHY: BMR/TDEE calculation requires age, gender, height, weight.
    # Body fat % is a better body composition predictor than BMI.
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)          # male/female/other
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
    # BMI is computed: weight_kg / (height_m^2)

    # ── Fitness Context ───────────────────────────────────────
    # WHY: Determines training frequency, exercise selection, volume tolerance.
    fitness_level = Column(String(30), nullable=True)   # beginner/intermediate/advanced
    activity_level = Column(String(30), nullable=True)  # sedentary/lightly_active/very_active
    occupation_type = Column(String(50), nullable=True) # desk_job/physical_labor/student
    years_training = Column(Float, nullable=True)

    # ── Goals ─────────────────────────────────────────────────
    # WHY: The optimization objective for every recommendation.
    primary_goal = Column(String(50), nullable=True)    # fat_loss/muscle_gain/endurance/mobility
    secondary_goal = Column(String(50), nullable=True)
    target_weight_kg = Column(Float, nullable=True)
    goal_deadline_weeks = Column(Integer, nullable=True)

    # ── Schedule / Logistics ──────────────────────────────────
    # WHY: Hard constraints on plan structure.
    available_days_per_week = Column(Integer, nullable=True)
    session_duration_min = Column(Integer, nullable=True)
    preferred_workout_time = Column(String(20), nullable=True)  # morning/afternoon/evening
    workout_location = Column(String(30), nullable=True)        # home/gym/outdoor

    # WHY: Equipment determines the feasible exercise search space.
    equipment_available = Column(JSON, nullable=True)   # ["barbell","dumbbells","pull_up_bar"]

    # ── Dietary Context ───────────────────────────────────────
    # WHY: Diet type, allergies, and meal frequency directly constrain
    # the Nutrition Agent's output.
    diet_type = Column(String(30), nullable=True)       # vegetarian/vegan/keto/omnivore
    meal_frequency = Column(Integer, nullable=True)     # meals per day
    food_allergies = Column(JSON, nullable=True)        # ["gluten","lactose","nuts"]
    cuisine_preference = Column(JSON, nullable=True)    # ["Indian","Mediterranean"]
    weekly_food_budget_usd = Column(Float, nullable=True)

    # ── Lifestyle Signals ─────────────────────────────────────
    # WHY: Recovery capacity and metabolic rate depend on these.
    sleep_hours_avg = Column(Float, nullable=True)
    sleep_quality = Column(String(20), nullable=True)   # poor/fair/good/excellent
    stress_level = Column(Integer, nullable=True)       # 1-10
    water_intake_liters = Column(Float, nullable=True)
    smoking = Column(Boolean, default=False)
    alcohol_units_week = Column(Integer, nullable=True)

    # ── Clinical / Medical ────────────────────────────────────
    # WHY: Pregnancy status changes allowable exercise categories fundamentally.
    is_pregnant = Column(Boolean, default=False)
    pregnancy_trimester = Column(Integer, nullable=True)  # 1/2/3

    # ── Adherence Predictors ──────────────────────────────────
    # WHY: Best predictors of future adherence and plan complexity tolerance.
    motivation_level = Column(Integer, nullable=True)   # 1-10
    past_program_adherence = Column(String(20), nullable=True)  # never/low/medium/high
    reason_for_starting = Column(Text, nullable=True)

    # ── Legacy fields (kept for backward compat) ──────────────
    fitness_goal = Column(String(50), nullable=True)    # maps to primary_goal
    workout_preference = Column(String(30), nullable=True)  # maps to workout_location
    workout_time = Column(String(20), nullable=True)    # maps to preferred_workout_time
    diet_preference = Column(String(30), nullable=True) # maps to diet_type
    allergies = Column(Text, nullable=True)             # maps to food_allergies JSON
    health_conditions = Column(Text, nullable=True)     # free text (legacy)
    injuries = Column(Text, nullable=True)              # free text (legacy)
    medications = Column(Text, nullable=True)           # free text (legacy)
    medical_history = Column(Text, nullable=True)

    profile_complete = Column(Boolean, default=False)
    assessment_completed = Column(String(10), default="no")  # backward compat

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="health_profile")

    def compute_bmi(self) -> float | None:
        """Compute BMI from height and weight."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            return round(self.weight_kg / ((self.height_cm / 100) ** 2), 1)
        return None

    def to_agent_context(self) -> dict:
        """Serialize profile to a clean dict for agent prompts."""
        return {
            "age": self.age or 25,
            "gender": self.gender or "not specified",
            "height_cm": self.height_cm or 170,
            "weight_kg": self.weight_kg or 70,
            "body_fat_pct": self.body_fat_pct,
            "bmi": self.compute_bmi(),
            "fitness_level": self.fitness_level or "beginner",
            "activity_level": self.activity_level or "sedentary",
            "primary_goal": self.primary_goal or self.fitness_goal or "general_fitness",
            "secondary_goal": self.secondary_goal,
            "available_days_per_week": self.available_days_per_week or 3,
            "session_duration_min": self.session_duration_min or 45,
            "workout_location": self.workout_location or self.workout_preference or "home",
            "equipment_available": self.equipment_available or [],
            "diet_type": self.diet_type or self.diet_preference or "vegetarian",
            "food_allergies": self.food_allergies or [],
            "cuisine_preference": self.cuisine_preference or ["Indian"],
            "sleep_hours_avg": self.sleep_hours_avg or 7.0,
            "sleep_quality": self.sleep_quality or "fair",
            "stress_level": self.stress_level or 5,
            "water_intake_liters": self.water_intake_liters or 2.0,
            "smoking": self.smoking or False,
            "alcohol_units_week": self.alcohol_units_week or 0,
            "is_pregnant": self.is_pregnant or False,
            "pregnancy_trimester": self.pregnancy_trimester,
            "motivation_level": self.motivation_level or 5,
            "target_weight_kg": self.target_weight_kg,
            "goal_deadline_weeks": self.goal_deadline_weeks,
            "meal_frequency": self.meal_frequency or 3,
            "years_training": self.years_training or 0,
        }
