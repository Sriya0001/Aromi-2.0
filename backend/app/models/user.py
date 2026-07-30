"""
User model — auth and identity only.
Health data lives in health_profiles for HIPAA-like privacy boundaries.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)

    # Google Calendar OAuth
    calendar_sync = Column(String(10), default="no")
    google_token_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete")
    medical_conditions = relationship("MedicalCondition", back_populates="user", cascade="all, delete")
    injury_history = relationship("InjuryRecord", back_populates="user", cascade="all, delete")
    weekly_plans = relationship("WeeklyPlan", back_populates="user", cascade="all, delete")
    workout_sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete")
    nutrition_logs = relationship("NutritionLog", back_populates="user", cascade="all, delete")
    nutrition_plans_legacy = relationship("NutritionPlan", back_populates="user", cascade="all, delete")
    progress_metrics = relationship("ProgressMetric", back_populates="user", cascade="all, delete")
    sleep_logs = relationship("SleepLog", back_populates="user", cascade="all, delete")
    hydration_logs = relationship("HydrationLog", back_populates="user", cascade="all, delete")
    feedback_events = relationship("FeedbackEvent", back_populates="user", cascade="all, delete")
    user_memories = relationship("UserMemory", back_populates="user", cascade="all, delete")
    semantic_memories = relationship("UserSemanticMemory", back_populates="user", cascade="all, delete")
    ai_conversations = relationship("AIConversation", back_populates="user", cascade="all, delete")
    chat_sessions_legacy = relationship("ChatSession", back_populates="user", cascade="all, delete")
    evaluation_metrics = relationship("EvaluationMetric", back_populates="user", cascade="all, delete")
    favourite_exercises = relationship("FavouriteExercise", back_populates="user", cascade="all, delete")
    reviews = relationship("Review", back_populates="user", cascade="all, delete")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete")
