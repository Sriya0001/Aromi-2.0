"""
Workout models: WeeklyPlan, WorkoutSession, FavouriteExercise.

KEY DESIGN DECISION: WorkoutSession stores PLANNED vs ACTUAL exercises.
This enables:
  - Adherence computation (planned != completed → missed)
  - Delta analysis (what was skipped and why)
  - Progressive overload tracking (actual load progression)
  - Explainability (reasoning field explains WHY each exercise was chosen)
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean,
    JSON, ForeignKey, Date
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class WeeklyPlan(Base):
    """Container for a week's plan. Plans are versioned events, not static rows."""
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    plan_version = Column(Integer, default=1)
    generated_by = Column(String(50), default="planner_agent_v1")

    # Snapshot of all signals used to generate this plan — enables reproducibility
    generation_context = Column(JSON, nullable=True)

    plan_status = Column(String(20), default="active")  # active/superseded/completed
    adaptation_action = Column(String(50), nullable=True)  # PROGRESSIVE_OVERLOAD/DELOAD/etc.
    adaptation_reasoning = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="weekly_plans")
    sessions = relationship("WorkoutSession", back_populates="weekly_plan", cascade="all, delete")


class WorkoutSession(Base):
    """Individual workout session: planned vs. actual for adherence tracking."""
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weekly_plan_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=True)

    session_date = Column(Date, nullable=False)
    day_of_week = Column(Integer, nullable=True)        # 1=Monday, 7=Sunday
    day_name = Column(String(20), nullable=True)
    focus_area = Column(String(100), nullable=True)     # "Upper Body", "Legs", etc.
    planned_duration_min = Column(Integer, default=45)

    # Planned exercises (from Workout Agent)
    exercises_planned = Column(JSON, nullable=True)     # [{name, sets, reps, rest, muscle_group, instructions, video_url}]
    warmup = Column(Text, nullable=True)
    cooldown = Column(Text, nullable=True)
    tips = Column(Text, nullable=True)

    # Actual completion (from user)
    exercises_actual = Column(JSON, nullable=True)
    actual_duration_min = Column(Integer, nullable=True)

    # Status tracking
    status = Column(String(20), default="planned")     # planned/completed/skipped/partial
    completion_pct = Column(Float, nullable=True)       # 0.0 - 1.0
    skipped_reason = Column(Text, nullable=True)

    # Explainability — WHY this plan was generated
    reasoning = Column(Text, nullable=True)
    agent_version = Column(String(50), nullable=True)

    calories_burned_estimate = Column(Integer, nullable=True)

    # User feedback
    user_rating = Column(Integer, nullable=True)        # 1-5
    user_feedback = Column(Text, nullable=True)
    difficulty_felt = Column(String(20), nullable=True) # too_easy/right/too_hard

    # Legacy compatibility fields
    exercises = Column(Text, nullable=True)             # old JSON string format
    day = Column(Integer, nullable=True)                # old day number field
    youtube_queries = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_sessions")
    weekly_plan = relationship("WeeklyPlan", back_populates="sessions")


class FavouriteExercise(Base):
    __tablename__ = "favourite_exercises"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    muscle_group = Column(String(50), nullable=True)
    sets = Column(String(20), nullable=True)
    reps = Column(String(20), nullable=True)
    rest_seconds = Column(Integer, default=60)
    instructions = Column(Text, nullable=True)
    video_url = Column(String(255), nullable=True)
    video_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favourite_exercises")


# Backward-compatibility alias: legacy code imports WorkoutPlan
# The new name is WeeklyPlan (clearer semantics), but we alias here
# to avoid breaking intent_service.py and workout_service.py.
WorkoutPlan = WeeklyPlan
