"""
Memory Service — manages the two-tier long-term memory system.

Tier 1: Working memory — last 10 conversation turns (AIConversation table)
Tier 2: Long-term memory — structured facts (UserMemory table)
"""
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional


class MemoryService:

    @staticmethod
    def get_user_memory_context(db: Session, user_id: int) -> dict:
        """
        Build structured memory context for agent injection.
        Applies confidence decay filter (threshold: 0.3).
        Memories below threshold are excluded (stale / unreliable).
        """
        from app.models.memory import UserMemory

        memories = db.query(UserMemory).filter(
            UserMemory.user_id == user_id
        ).all()

        context = {
            "favorite_exercises": [],
            "disliked_exercises": [],
            "skip_patterns": [],
            "achievements": [],
            "injuries": [],
            "preferences": {},
            "feedback_summaries": [],
        }

        for m in memories:
            current_confidence = m.current_confidence()
            if current_confidence < 0.3:
                continue  # Stale memory — skip

            if m.memory_type == "preference":
                if "favorite" in m.key:
                    context["favorite_exercises"].append(m.value)
                elif any(w in m.key for w in ["dislike", "hate", "avoid"]):
                    context["disliked_exercises"].append(m.value)
                else:
                    context["preferences"][m.key] = m.value
            elif m.memory_type == "avoidance":
                context["skip_patterns"].append({"key": m.key, "value": m.value})
            elif m.memory_type == "achievement":
                context["achievements"].append(m.value)
            elif m.memory_type == "injury":
                context["injuries"].append(m.value)
            elif m.memory_type == "feedback_summary":
                context["feedback_summaries"].append(m.value)

        return context

    @staticmethod
    def upsert_memory(db: Session, user_id: int, memory_type: str, key: str,
                      value: str, source: str = "inferred",
                      confidence: float = 0.8) -> None:
        """
        Insert or update a memory entry.
        If the same key exists: reinforce confidence (capped at 1.0) and update value.
        """
        from app.models.memory import UserMemory

        existing = db.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.key == key
        ).first()

        if existing:
            existing.value = value
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.last_reinforced = datetime.utcnow()
        else:
            memory = UserMemory(
                user_id=user_id,
                memory_type=memory_type,
                key=key,
                value=value,
                confidence=confidence,
                source=source,
            )
            db.add(memory)

        db.commit()

    @staticmethod
    def extract_memories_from_behavior(db: Session, user_id: int) -> int:
        """
        Behavioral & Profile memory extraction — analyzes health profile, biometrics,
        chat interactions, and workout history to build structured long-term facts.
        """
        from app.models.health_profile import HealthProfile
        from app.models.workout import WorkoutSession
        from app.models.chat import ChatSession
        from collections import Counter

        count = 0

        # 1. Profile & Biometric Memory Extraction
        profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
        if profile:
            if profile.primary_goal or profile.fitness_goal:
                goal = profile.primary_goal or profile.fitness_goal
                MemoryService.upsert_memory(
                    db, user_id, "preference", "primary_fitness_goal",
                    f"Targeting {goal.replace('_', ' ').title()}",
                    source="user_explicit", confidence=0.95
                )
                count += 1

            if profile.diet_type or profile.diet_preference:
                diet = profile.diet_type or profile.diet_preference
                MemoryService.upsert_memory(
                    db, user_id, "preference", "dietary_lifestyle",
                    f"Prefers {diet.title()} nutrition plan",
                    source="user_explicit", confidence=0.95
                )
                count += 1

            if profile.workout_location or profile.workout_preference:
                loc = profile.workout_location or profile.workout_preference
                MemoryService.upsert_memory(
                    db, user_id, "preference", "workout_environment",
                    f"Trains primarily at {loc.title()}",
                    source="user_explicit", confidence=0.90
                )
                count += 1

            if profile.fitness_level:
                MemoryService.upsert_memory(
                    db, user_id, "pattern", "experience_level",
                    f"Training experience: {profile.fitness_level.title()}",
                    source="inferred", confidence=0.85
                )
                count += 1

        # 2. Workout History Patterns
        thirty_days_ago = date.today() - timedelta(days=30)
        sessions = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= thirty_days_ago
        ).all()

        if sessions:
            skipped_days: Counter = Counter()
            completed_days: Counter = Counter()
            exercise_completions: Counter = Counter()

            day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
                         5: "Friday", 6: "Saturday", 7: "Sunday"}

            for s in sessions:
                if s.status == "skipped" and s.day_of_week:
                    skipped_days[s.day_of_week] += 1
                elif s.status == "completed" and s.day_of_week:
                    completed_days[s.day_of_week] += 1

                if s.exercises_planned:
                    exercises = s.exercises_planned if isinstance(s.exercises_planned, list) else []
                    for ex in exercises:
                        name = ex.get("name", "") if isinstance(ex, dict) else ""
                        if name:
                            exercise_completions[name] += 1

            for day, skip_count in skipped_days.items():
                total = skip_count + completed_days.get(day, 0)
                if skip_count >= 1:
                    MemoryService.upsert_memory(
                        db, user_id, "avoidance",
                        f"skip_pattern_{day_names.get(day, str(day))}",
                        f"Skipped {day_names.get(day, str(day))} session ({skip_count} time)",
                        source="behavioral", confidence=0.75
                    )
                    count += 1

            for exercise, comp_count in exercise_completions.most_common(5):
                if exercise:
                    MemoryService.upsert_memory(
                        db, user_id, "preference",
                        f"favorite_exercise_{exercise.lower().replace(' ', '_')}",
                        f"Prescribed exercise: {exercise}",
                        source="behavioral", confidence=0.70
                    )
                    count += 1

        # 3. Chat Interaction Insights
        recent_chats = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.timestamp.desc()).limit(10).all()

        for chat in recent_chats:
            msg = chat.message.lower()
            if any(w in msg for w in ["knee", "leg", "back", "shoulder", "wrist"]):
                for body_part in ["knee", "leg", "back", "shoulder", "wrist"]:
                    if body_part in msg:
                        MemoryService.upsert_memory(
                            db, user_id, "injury",
                            f"recent_pain_{body_part}",
                            f"Reported {body_part} discomfort in coach chat",
                            source="user_explicit", confidence=0.90
                        )
                        count += 1

        return count

    @staticmethod
    def add_explicit_memory(db: Session, user_id: int, key: str,
                             value: str, memory_type: str = "preference") -> None:
        """Store explicitly stated user preference."""
        MemoryService.upsert_memory(
            db, user_id, memory_type, key, value,
            source="user_explicit", confidence=0.95
        )

    @staticmethod
    def get_all_memories(db: Session, user_id: int) -> list:
        """Get all memories for display in the Memory Viewer UI."""
        from app.models.memory import UserMemory
        memories = db.query(UserMemory).filter(
            UserMemory.user_id == user_id
        ).order_by(UserMemory.last_reinforced.desc()).all()

        return [{
            "id": m.id,
            "type": m.memory_type,
            "key": m.key,
            "value": m.value,
            "confidence": round(m.current_confidence(), 2),
            "raw_confidence": m.confidence,
            "source": m.source,
            "last_reinforced": m.last_reinforced.isoformat(),
            "created_at": m.created_at.isoformat()
        } for m in memories]

    @staticmethod
    def decay_all_memories(db: Session) -> int:
        """Weekly scheduled job: apply confidence decay to all memories."""
        from app.models.memory import UserMemory

        all_memories = db.query(UserMemory).all()
        pruned = 0

        for m in all_memories:
            current = m.current_confidence()
            if current < 0.2:
                db.delete(m)
                pruned += 1

        db.commit()
        return pruned
