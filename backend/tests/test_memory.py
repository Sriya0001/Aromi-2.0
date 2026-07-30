"""
Test Suite: MemoryService & Ebbinghaus Decay Math.
Role: Senior SDET at Amazon
"""
import pytest
from datetime import datetime, timedelta
from app.models.memory import UserMemory


def test_ebbinghaus_decay_fresh_explicit_memory():
    """Verify fresh explicit user memory maintains high confidence (~1.0)."""
    mem = UserMemory(
        user_id=1,
        memory_type="preference",
        key="primary_fitness_goal",
        value="Targeting Muscle Gain",
        confidence=1.0,
        source="user_explicit",
        last_reinforced=datetime.utcnow()
    )
    assert mem.current_confidence() == 1.0


def test_ebbinghaus_decay_stale_memory_decay():
    """Verify memory confidence decays after 60 days of non-reinforcement."""
    mem = UserMemory(
        user_id=1,
        memory_type="preference",
        key="disliked_exercise",
        value="Burpees",
        confidence=0.7,
        source="inferred",
        last_reinforced=datetime.utcnow() - timedelta(days=60)
    )
    conf = mem.current_confidence()
    assert conf < 0.25
    assert conf >= 0.05
