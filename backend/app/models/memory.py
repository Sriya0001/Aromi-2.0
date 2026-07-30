"""
UserMemory and UserSemanticMemory models.

UserMemory: Structured relational facts with Ebbinghaus forgetting decay.
UserSemanticMemory: Qualitative user feedback & chat notes for similarity retrieval.
"""
import math
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class UserMemory(Base):
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    memory_type = Column(String(50), nullable=False)  # preference / achievement / avoidance / pattern / injury / feedback_summary
    key = Column(String(200), nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="inferred")  # user_explicit / inferred / behavioral
    decay_rate = Column(Float, default=0.01)

    last_reinforced = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_memories")

    def current_confidence(self) -> float:
        """
        Calculates Ebbinghaus forgetting curve confidence:
        Confidence(t) = V * exp( - delta_t / (tau * (1 + log(1 + F))) )
        """
        delta_days = (datetime.utcnow() - self.last_reinforced).total_seconds() / 86400.0
        v = 1.0 if self.source == "user_explicit" else 0.7
        tau = 30.0  # 30 day half-life
        
        decayed = v * math.exp(-delta_days / tau)
        return round(max(0.05, min(1.0, decayed)), 3)


class UserSemanticMemory(Base):
    __tablename__ = "user_semantic_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    memory_type = Column(String(50), nullable=False)  # 'feedback', 'injury_report', 'preference_note'
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="user_explicit")
    last_reinforced = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="semantic_memories")
