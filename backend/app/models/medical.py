"""
MedicalCondition, InjuryRecord, and Contraindication models.
Deterministic medical safety guardrails.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Contraindication(Base):
    __tablename__ = "contraindications"

    id = Column(Integer, primary_key=True, index=True)
    condition_name = Column(String(100), nullable=False, index=True)  # 'Hypertension', 'Osteoporosis', 'Pregnancy_T3'
    prohibited_movement_pattern = Column(String(100), nullable=True)   # 'Valsalva', 'Lumbar Flexion', 'Inversions'
    max_heart_rate_cap = Column(Integer, nullable=True)                # e.g., 130 bpm
    max_intraocular_pressure_risk = Column(Boolean, default=False)
    reasoning = Column(Text, nullable=False)


class MedicalCondition(Base):
    __tablename__ = "medical_conditions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    condition_name = Column(String(100), nullable=False)  # Type2Diabetes, Hypertension, Osteoporosis, Glaucoma, Asthma
    severity = Column(String(20), nullable=True)        # mild/moderate/severe
    diagnosed_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    affects_exercise = Column(Boolean, default=True)
    affects_nutrition = Column(Boolean, default=True)

    medications = Column(JSON, nullable=True)           # ["BetaBlockers", "Metformin"]
    exercise_restrictions = Column(JSON, nullable=True) # ["no_valsalva", "hr_cap_130", "rpe_only"]
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="medical_conditions")


class InjuryRecord(Base):
    __tablename__ = "injury_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    body_part = Column(String(50), nullable=False)      # left_knee, lumbar_spine, right_shoulder
    injury_type = Column(String(100), nullable=True)   # ACL tear, herniated disc
    is_current = Column(Boolean, default=False)
    severity = Column(String(20), nullable=True)       # mild/moderate/severe
    cleared_for_exercise = Column(Boolean, default=True)

    restrictions = Column(JSON, nullable=True)         # ["no_squats", "no_running"]
    injury_date = Column(DateTime, nullable=True)
    recovery_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="injury_history")
