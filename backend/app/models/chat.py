"""
AIConversation model replaces ChatSession.
Stores individual messages (not pairs) for proper conversation threading.
Tool calls are logged for evaluation and debugging.

ChatSession kept for backward compatibility.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AIConversation(Base):
    """Individual conversation messages — enables multi-agent conversation threading."""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), nullable=True)     # groups messages into a session
    role = Column(String(20), nullable=False)           # user/assistant/system
    content = Column(Text, nullable=False)
    agent_name = Column(String(50), nullable=True)      # workout_agent/nutrition_agent/planner_agent
    tool_calls = Column(JSON, nullable=True)            # which tools were invoked
    token_count = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ai_conversations")


class ChatSession(Base):
    """Legacy table — kept for backward compatibility. New code uses AIConversation."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions_legacy")
