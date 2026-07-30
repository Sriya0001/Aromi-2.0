"""
Workout Agent — generates safe, progressive, personalized exercise prescriptions.

Reasoning Process (Chain of Thought):
1. Filter exercise universe by equipment constraints (hard)
2. Apply medical/injury exclusion rules via safety filter (hard)
3. Apply progressive overload formula from history
4. Select exercises (favorites > novel > neutral > disliked)
5. Adjust volume by recovery_signal.volume_modifier
6. Generate EXPLAINED prescription with per-exercise reasoning

WHY CoT prompting:
Asking the agent to reason step-by-step before generating a plan reduces
hallucinations and improves safety constraint adherence.
(Experiment 5 in evaluation framework)
"""
from app.agents.base import BaseAgent, AgentContext, AgentOutput
from datetime import date, timedelta
from typing import Optional


ACTIVE_RECOVERY_PLAN = [
    {"name": "Dynamic Stretching", "sets": 2, "reps": "10 min", "rest_seconds": 30,
     "muscle_group": "Full Body", "instructions": "Focus on breathing and range of motion."},
    {"name": "Light Yoga Flow", "sets": 1, "reps": "15 min", "rest_seconds": 0,
     "muscle_group": "Full Body", "instructions": "Hold poses gently, no strain."},
    {"name": "Foam Rolling", "sets": 1, "reps": "10 min", "rest_seconds": 0,
     "muscle_group": "Full Body", "instructions": "Focus on tight areas."},
]


class WorkoutAgent(BaseAgent):
    name = "workout_agent"

    SYSTEM_PROMPT = """You are a specialized Exercise Physiologist AI. Your ONLY job is to generate safe, progressive workout plans.

Reasoning process (follow this EXACTLY before generating exercises):
1. CONSTRAINTS: List all equipment and medical/injury constraints that eliminate exercises
2. HISTORY: Note any exercises the user has completed successfully or dislikes
3. VOLUME: Calculate appropriate volume based on readiness modifier provided
4. SELECTION: Select exercises respecting all constraints, prioritizing user history
5. OUTPUT: Generate the plan in the exact JSON format specified

Return ONLY valid JSON. No markdown, no extra text."""

    async def run(self, context: AgentContext, recovery_signal: dict = None,
                  week_number: int = 1, **kwargs) -> AgentOutput:
        import time
        start = time.time()

        # Handle active recovery case immediately (no LLM call needed)
        if recovery_signal and recovery_signal.get("recommendation") == "active_recovery_only":
            return AgentOutput(
                agent_name=self.name,
                success=True,
                data={"sessions": self._build_active_recovery_week(context)},
                reasoning=f"Active recovery week forced by Recovery Agent (readiness={recovery_signal['readiness_score']:.2f}). "
                          f"No high-intensity training prescribed.",
                latency_ms=int((time.time() - start) * 1000)
            )

        # Get recent workout history for progressive overload
        history = self._get_workout_history(context)

        # Build Chain-of-Thought prompt
        user_prompt = self._build_cot_prompt(context, recovery_signal, history, week_number)

        try:
            raw_response, token_count = await self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=4096
            )
            plan_data = self._parse_json_response(raw_response)
        except Exception as e:
            plan_data = {}

        if not plan_data or not plan_data.get("plan"):
            from app.services.fallback_service import get_fallback_workout_plan
            plan_data = get_fallback_workout_plan()

        # Post-process: apply safety filter on each exercise
        sessions = plan_data.get("plan", [])
        sessions, safety_warnings = self._apply_safety_filter(sessions, context)

        # Enrich with YouTube videos if applicable
        sessions = await self._enrich_videos(sessions, context)

        # Attach per-session reasoning
        overall_reasoning = (
            f"Workout Agent v1 | Week {week_number} | "
            f"Goal: {context.health_profile.get('primary_goal', 'general_fitness')} | "
            f"Volume modifier: {recovery_signal.get('volume_modifier', 1.0) if recovery_signal else 1.0:.0%} | "
            f"Safety exclusions: {len(safety_warnings)}"
        )

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={"sessions": sessions, "raw_plan": plan_data},
            reasoning=overall_reasoning,
            warnings=safety_warnings,
            latency_ms=int((time.time() - start) * 1000),
            token_count=token_count
        )

    def _build_cot_prompt(self, context: AgentContext, recovery_signal: dict,
                          history: dict, week_number: int) -> str:
        hp = context.health_profile
        volume_mod = recovery_signal.get('volume_modifier', 1.0) if recovery_signal else 1.0
        readiness = recovery_signal.get('readiness_score', 0.7) if recovery_signal else 0.7
        extra_rest = recovery_signal.get('rest_duration_increase', 0) if recovery_signal else 0

        memory = context.long_term_memory
        favorites = memory.get('favorite_exercises', [])
        dislikes = memory.get('disliked_exercises', [])

        # Format medical/injury constraints
        medical_constraints = ""
        for cond in context.medical_conditions:
            medical_constraints += f"- {cond.get('condition', '')}: restrictions={cond.get('restrictions', [])}\n"
        for inj in context.injury_restrictions:
            medical_constraints += f"- Injury ({inj.get('body_part', '')}): restrictions={inj.get('restrictions', [])}\n"
        if not medical_constraints:
            medical_constraints = "None"

        return f"""STEP 1 - CONSTRAINTS:
Equipment available: {hp.get('equipment_available', []) or hp.get('workout_location', 'home')}
Workout location: {hp.get('workout_location', 'home')}
Medical/Injury constraints (HARD - cannot be violated):
{medical_constraints}

STEP 2 - USER HISTORY:
Favorite exercises (prioritize): {favorites}
Disliked exercises (avoid if possible): {dislikes}
Past week completions: {history.get('recent_sessions', 'no data')}
Current 1RM estimates: {history.get('one_rm', {})}

STEP 3 - VOLUME CALCULATION:
Readiness score: {readiness:.2f} | Volume modifier: {volume_mod:.0%}
Extra rest per set: +{extra_rest}s
Target sessions per week: {hp.get('available_days_per_week', 3)}
Session duration: {hp.get('session_duration_min', 45)} minutes
Week number (for progressive overload): {week_number}

STEP 4 - USER PROFILE:
Age: {hp.get('age', 25)} | Gender: {hp.get('gender', 'not specified')}
Weight: {hp.get('weight_kg', 70)}kg | Height: {hp.get('height_cm', 170)}cm
Fitness level: {hp.get('fitness_level', 'beginner')}
Primary goal: {hp.get('primary_goal', 'general_fitness')}
Pregnant: {hp.get('is_pregnant', False)} | Trimester: {hp.get('pregnancy_trimester', None)}

STEP 5 - GENERATE PLAN:
Generate a {hp.get('available_days_per_week', 3)}-day workout plan for the week.
For each session, provide a per-session reasoning field explaining WHY these exercises were chosen.

Return ONLY this JSON structure:
{{
  "plan": [
    {{
      "day": 1,
      "day_name": "Monday",
      "focus": "Upper Body Push",
      "duration_minutes": {hp.get('session_duration_min', 45)},
      "warmup": "5-minute brisk walk and arm circles",
      "exercises": [
        {{
          "name": "Push-ups",
          "sets": 3,
          "reps": "10-12",
          "rest_seconds": {60 + extra_rest},
          "muscle_group": "Chest",
          "instructions": "Keep your core tight and lower chest to ground",
          "youtube_query": "push-ups proper form tutorial",
          "reasoning": "Selected because: goal=muscle_gain, no upper body restrictions, compound movement for efficiency"
        }}
      ],
      "cooldown": "5-minute stretching",
      "tips": "Stay hydrated",
      "calories_estimate": 250,
      "session_reasoning": "Upper Push Day selected to balance the pull session. Volume at {volume_mod:.0%} of baseline due to readiness score."
    }}
  ]
}}"""

    def _apply_safety_filter(self, sessions: list, context: AgentContext) -> tuple[list, list]:
        """Post-generation safety pass. Removes unsafe exercises, logs warnings."""
        warnings = []
        cleaned_sessions = []

        for session in sessions:
            cleaned_exercises = []
            for exercise in session.get("exercises", []):
                is_safe, reason = self._medical_safety_check(context, exercise.get("name", ""))
                if is_safe:
                    cleaned_exercises.append(exercise)
                else:
                    warnings.append(f"Removed '{exercise.get('name')}': {reason}")
            session["exercises"] = cleaned_exercises
            cleaned_sessions.append(session)

        return cleaned_sessions, warnings

    def _get_workout_history(self, context: AgentContext) -> dict:
        """Fetch recent workout history for progressive overload context."""
        if context.db is None:
            return {}
        try:
            from app.models.workout import WorkoutSession
            from datetime import date
            two_weeks_ago = date.today() - timedelta(days=14)
            sessions = context.db.query(WorkoutSession).filter(
                WorkoutSession.user_id == context.user_id,
                WorkoutSession.session_date >= two_weeks_ago,
                WorkoutSession.status == "completed"
            ).order_by(WorkoutSession.session_date.desc()).limit(14).all()

            recent_names = []
            for s in sessions[:5]:
                exercises = s.exercises_planned or []
                recent_names.extend([ex.get("name") for ex in exercises if ex.get("name")])

            return {"recent_sessions": f"{len(sessions)} completed in last 14 days",
                    "recent_exercises": list(set(recent_names))[:10]}
        except Exception:
            return {}

    def _build_active_recovery_week(self, context: AgentContext) -> list:
        """Build a full active recovery week when readiness is critically low."""
        today = date.today()
        # Start from Monday of current week
        monday = today - timedelta(days=today.weekday())
        sessions = []
        for i in range(7):
            day = monday + timedelta(days=i)
            sessions.append({
                "day": i + 1,
                "day_name": day.strftime("%A"),
                "focus": "Active Recovery",
                "duration_minutes": 20,
                "exercises": ACTIVE_RECOVERY_PLAN,
                "warmup": "3 min gentle walking",
                "cooldown": "Deep breathing 2 min",
                "tips": "Listen to your body. This is a recovery week.",
                "calories_estimate": 80,
                "session_reasoning": "Active recovery forced by Recovery Agent due to critically low readiness score."
            })
        return sessions

    async def _enrich_videos(self, sessions: list, context: AgentContext) -> list:
        """Intelligently call YouTube API only when warranted."""
        hp = context.health_profile
        # WHY call: Beginners need form guidance. Skip for advanced users.
        should_enrich = hp.get("fitness_level", "beginner") in ["beginner", "intermediate"]
        if not should_enrich:
            return sessions

        try:
            from app.services.youtube_service import enrich_exercise
            for session in sessions:
                for exercise in session.get("exercises", []):
                    await enrich_exercise(exercise)
        except Exception:
            pass  # Graceful degradation
        return sessions
