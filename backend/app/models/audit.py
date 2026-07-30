"""
AuditLog model — HIPAA & security compliance logging for user actions,
profile modifications, and safety filter engagements.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # 'PROFILE_UPDATE', 'SAFETY_FILTER_ENGAGED', 'DATA_EXPORT'
    details = Column(JSON, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
