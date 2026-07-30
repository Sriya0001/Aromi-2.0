"""
ProgressMetric, SleepLog, HydrationLog — biometric time-series data.

WHY separate tables for sleep and hydration:
- Sleep is a PRIMARY signal for the Recovery Agent readiness computation.
- Hydration affects performance and nutrition targets.
- Storing them separately allows efficient time-range queries per signal type.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ProgressMetric(Base):
    """Body composition measurements — the ground truth for goal evaluation."""
    __tablename__ = "progress_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    weight_kg = Column(Float, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    bicep_cm = Column(Float, nullable=True)

    # Performance markers
    resting_hr_bpm = Column(Integer, nullable=True)
    vo2max_estimate = Column(Float, nullable=True)
    one_rep_max = Column(JSON, nullable=True)      # {"squat": 80, "bench": 60}

    # Legacy fields
    date = Column(String(50), nullable=True)
    workouts_completed = Column(Integer, nullable=True)
    calories_burned = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="progress_metrics")


class SleepLog(Base):
    """
    WHY: Sleep quality and HRV are the two highest-signal recovery indicators.
    Recovery Agent uses 3-day rolling sleep average for readiness computation.
    Poor sleep (<6h) → volume reduction in next workout session.
    """
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sleep_date = Column(Date, nullable=False)
    duration_hours = Column(Float, nullable=True)
    quality_score = Column(Integer, nullable=True)   # 1-10 user-reported
    hrv_ms = Column(Float, nullable=True)            # Heart Rate Variability (recovery proxy)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sleep_logs")


class HydrationLog(Base):
    """
    WHY: Dehydration >2% bodyweight impairs performance measurably.
    Nutrition Agent uses hydration data to adjust electrolyte recommendations
    during high-volume training weeks.
    """
    __tablename__ = "hydration_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(Date, nullable=False)
    water_ml = Column(Integer, nullable=True)
    target_ml = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="hydration_logs")


# Backward-compatibility alias: legacy routers/progress.py and adaptive_engine.py
# import ProgressRecord. The new name is ProgressMetric (clearer semantics).
ProgressRecord = ProgressMetric
