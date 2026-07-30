"""
Evaluation and experiment models.

WHY: Without automated metric logging, there is no science — only vibes.
Every plan generation logs KPIs. Experiment assignments enable A/B testing.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FeedbackEvent(Base):
    """
    Every thumbs up/down, difficulty rating, or text comment is a labeled
    training example for evaluation and future fine-tuning.
    """
    __tablename__ = "feedback_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(50), nullable=True)    # workout_session/meal/recommendation
    entity_id = Column(Integer, nullable=True)
    feedback_type = Column(String(30), nullable=True)  # thumbs_up/thumbs_down/rating/text
    rating = Column(Integer, nullable=True)            # 1-5
    text_feedback = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)     # computed sentiment: -1 to 1
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedback_events")


class Experiment(Base):
    """A/B experiment definition."""
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    arm_a_config = Column(JSON, nullable=True)         # {"agent_mode": "single"}
    arm_b_config = Column(JSON, nullable=True)         # {"agent_mode": "multi"}
    metric_primary = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assignments = relationship("ExperimentAssignment", back_populates="experiment")


class ExperimentAssignment(Base):
    """Maps users to experiment arms for A/B testing."""
    __tablename__ = "experiment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    arm = Column(String(10), nullable=False)           # A or B
    assigned_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="assignments")


class EvaluationMetric(Base):
    """
    Automated metric logging — every plan generation computes and stores KPIs.
    Logged metrics: workout_adherence, meal_adherence, personalization_score,
    plan_stability, latency_ms, token_cost, hallucination_rate, diversity_score, csat.
    """
    __tablename__ = "evaluation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime, default=datetime.utcnow)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=True)

    user = relationship("User", back_populates="evaluation_metrics")
