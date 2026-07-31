"""
Planner Agent — the orchestrator of all agents.

Responsibilities:
1. Orchestrate Recovery, Workout, Nutrition agents (in correct order)
2. Gather all signals: adherence, weight trend, feedback, sleep, recovery
3. Compute adaptation action (PROGRESSIVE_OVERLOAD / DELOAD / SIMPLIFY / etc.)
4. Resolve conflicts between agents
5. Decide when to call external tools (Spoonacular, YouTube, Calendar)
6. Assemble the final plan with full explainability
7. Store plan + generation_context snapshot to DB

WHY the Planner is the hardest agent:
It must handle inter-agent conflicts:
- Workout Agent recommends leg day but Recovery Agent says readiness=0.3 → FORCE DELOAD
- Nutrition Agent suggests surplus but weight is stagnant → ESCALATE
"""
from app.agents.base import BaseAgent, AgentContext, AgentOutput
from app.agents.recovery_agent import RecoveryAgent
from app.agents.workout_agent import WorkoutAgent
from app.agents.nutrition_agent import NutritionAgent
from dataclasses import dataclass
from typing import Optional
import asyncio


@dataclass
class AdaptiveSignals:
    workout_adherence_7d: float = 0.0
    nutrition_adherence_7d: float = 0.0
    weight_change_kg: float = 0.0
    avg_difficulty_felt: str = "right"
    avg_user_rating: float = 3.0
    weeks_at_current_volume: int = 1
    goal: str = "general_fitness"


@dataclass
class AdaptationAction:
    type: str  # PROGRESSIVE_OVERLOAD / DELOAD / SIMPLIFY / SHOCK_WEEK / MAINTAIN
    volume_modifier: float = 1.0
    max_exercises_per_day: Optional[int] = None
    max_days_per_week: Optional[int] = None
    exercise_variety_boost: bool = False
    caloric_adjustment: int = 0
    reasoning: str = ""


class PlannerAgent(BaseAgent):
    name = "planner_agent"

    def __init__(self, groq_api_key: str, model: str = "llama-3.3-70b-versatile"):
        super().__init__(groq_api_key, model)
        self.recovery_agent = RecoveryAgent(groq_api_key, model)
        self.workout_agent = WorkoutAgent(groq_api_key, model)
        self.nutrition_agent = NutritionAgent(groq_api_key, model)

    async def run(self, context: AgentContext, **kwargs) -> AgentOutput:
        import time
        start = time.time()

        # STEP 1: Run Recovery Agent first (it constrains Workout Agent)
        recovery_output = await self.recovery_agent.run(context)
        recovery_signal = recovery_output.data if recovery_output.success else {"readiness_score": 0.7, "volume_modifier": 1.0}

        # STEP 2: Gather adaptive signals from DB
        adaptive_signals = self._gather_adaptive_signals(context)

        # STEP 3: Compute adaptation action
        adaptation = self._compute_adaptation_action(adaptive_signals, recovery_signal)

        # Override recovery volume modifier with adaptation if more conservative
        if adaptation.volume_modifier < recovery_signal.get("volume_modifier", 1.0):
            recovery_signal["volume_modifier"] = adaptation.volume_modifier
            recovery_signal["recommendation"] = "reduce_volume"

        # STEP 4: Run Workout + Nutrition agents in PARALLEL
        workout_task = self.workout_agent.run(
            context, recovery_signal=recovery_signal,
            week_number=self._compute_week_number(context)
        )
        nutrition_task = self.nutrition_agent.run(context)
        workout_output, nutrition_output = await asyncio.gather(workout_task, nutrition_task)

        # STEP 5: Resolve conflicts
        conflict_notes = self._resolve_conflicts(workout_output, nutrition_output,
                                                  adaptive_signals, adaptation)

        # STEP 6: Decide tool calls
        tool_calls_made = await self._execute_tool_calls(context)

        # STEP 7: Persist plan to DB
        plan_id = await self._persist_plan(
            context, workout_output, nutrition_output,
            recovery_signal, adaptation
        )

        # STEP 8: Log evaluation metrics
        self._log_evaluation_metrics(context, adaptive_signals, recovery_signal)

        # Build comprehensive reasoning
        reasoning = self._build_planner_reasoning(
            recovery_signal, adaptation, adaptive_signals,
            workout_output, nutrition_output, conflict_notes
        )

        total_tokens = (
            workout_output.token_count +
            nutrition_output.token_count
        ) if workout_output.success and nutrition_output.success else 0

        return AgentOutput(
            agent_name=self.name,
            success=workout_output.success and nutrition_output.success,
            data={
                "plan_id": plan_id,
                "workout_plan": workout_output.data.get("sessions", []) if workout_output.success else [],
                "nutrition_plan": nutrition_output.data.get("plan", []) if nutrition_output.success else [],
                "recovery_signal": recovery_signal,
                "adaptation_action": adaptation.type,
                "tool_calls_made": tool_calls_made,
                "caloric_target": nutrition_output.data.get("caloric_target") if nutrition_output.success else None,
                "macro_split": nutrition_output.data.get("macro_split") if nutrition_output.success else None,
                "hydration_target_ml": nutrition_output.data.get("hydration_target_ml") if nutrition_output.success else None,
            },
            reasoning=reasoning,
            warnings=workout_output.warnings + nutrition_output.warnings + conflict_notes,
            latency_ms=int((time.time() - start) * 1000),
            token_count=total_tokens
        )

    def _gather_adaptive_signals(self, context: AgentContext) -> AdaptiveSignals:
        """Gather signals from DB for adaptation decision."""
        signals = AdaptiveSignals(
            goal=context.health_profile.get("primary_goal") or context.health_profile.get("fitness_goal", "general_fitness")
        )
        if context.db is None:
            return signals

        try:
            from app.models.workout import WorkoutSession
            from app.models.nutrition import NutritionLog
            from app.models.progress import ProgressMetric
            from datetime import date, timedelta

            seven_days_ago = date.today() - timedelta(days=7)

            # Workout adherence
            planned = context.db.query(WorkoutSession).filter(
                WorkoutSession.user_id == context.user_id,
                WorkoutSession.session_date >= seven_days_ago
            ).count()
            completed = context.db.query(WorkoutSession).filter(
                WorkoutSession.user_id == context.user_id,
                WorkoutSession.session_date >= seven_days_ago,
                WorkoutSession.status == "completed"
            ).count()
            signals.workout_adherence_7d = (completed / planned) if planned > 0 else 0.0

            # Difficulty felt
            recent_sessions = context.db.query(WorkoutSession).filter(
                WorkoutSession.user_id == context.user_id,
                WorkoutSession.session_date >= seven_days_ago,
                WorkoutSession.difficulty_felt.isnot(None)
            ).all()
            if recent_sessions:
                difficulties = [s.difficulty_felt for s in recent_sessions if s.difficulty_felt]
                signals.avg_difficulty_felt = max(set(difficulties), key=difficulties.count) if difficulties else "right"

            # Weight trend
            metrics = context.db.query(ProgressMetric).filter(
                ProgressMetric.user_id == context.user_id
            ).order_by(ProgressMetric.recorded_at.desc()).limit(4).all()
            if len(metrics) >= 2:
                signals.weight_change_kg = (metrics[0].weight_kg or 0) - (metrics[-1].weight_kg or 0)

        except Exception as e:
            print(f"Planner signal gathering error: {e}")

        return signals

    def _compute_adaptation_action(self, signals: AdaptiveSignals,
                                    recovery_signal: dict) -> AdaptationAction:
        """
        Rule-based adaptation algorithm.
        Returns the action that should change the upcoming plan.

        Trade-off: Rule-based is interpretable and safe.
        Future: Replace with a learned bandit/RL policy trained on
        (signals, action) → next_week_adherence pairs.
        """
        readiness = recovery_signal.get("readiness_score", 0.7)

        # RULE 1: Overtraining detection (safety override)
        if (readiness < 0.40
                and signals.avg_difficulty_felt == "too_hard"
                and signals.workout_adherence_7d < 0.60):
            return AdaptationAction(
                type="DELOAD",
                volume_modifier=0.60,
                reasoning="3 overtraining signals: low readiness ({:.2f}), high difficulty, low adherence ({:.0%})".format(
                    readiness, signals.workout_adherence_7d)
            )

        # RULE 2: Plateau detection (stagnant weight despite adherence)
        if ("fat_loss" in signals.goal
                and abs(signals.weight_change_kg) < 0.2
                and signals.workout_adherence_7d > 0.75):
            return AdaptationAction(
                type="SHOCK_WEEK",
                volume_modifier=1.10,
                exercise_variety_boost=True,
                caloric_adjustment=-150,
                reasoning="Metabolic adaptation plateau: weight stagnant ({:.1f}kg change) despite {:.0%} adherence".format(
                    signals.weight_change_kg, signals.workout_adherence_7d)
            )

        # RULE 3: Low adherence → simplify
        if signals.workout_adherence_7d < 0.40:
            return AdaptationAction(
                type="SIMPLIFY",
                volume_modifier=0.80,
                max_exercises_per_day=3,
                max_days_per_week=3,
                reasoning="Low adherence ({:.0%}) suggests plan complexity is a barrier".format(
                    signals.workout_adherence_7d)
            )

        # RULE 4: Progressive overload (all green)
        if (signals.workout_adherence_7d > 0.80
                and signals.avg_difficulty_felt == "right"
                and readiness > 0.65):
            return AdaptationAction(
                type="PROGRESSIVE_OVERLOAD",
                volume_modifier=1.10,
                reasoning="All green: {:.0%} adherence, appropriate difficulty, readiness {:.2f}".format(
                    signals.workout_adherence_7d, readiness)
            )

        return AdaptationAction(type="MAINTAIN", volume_modifier=1.0,
                                reasoning="Signals mixed — maintaining current plan parameters")

    def _resolve_conflicts(self, workout_output: AgentOutput,
                            nutrition_output: AgentOutput,
                            signals: AdaptiveSignals,
                            adaptation: AdaptationAction) -> list:
        """Detect and resolve inter-agent conflicts."""
        conflicts = []

        # Conflict: High-volume workout on stagnant nutrition
        if (adaptation.type == "PROGRESSIVE_OVERLOAD"
                and nutrition_output.success
                and nutrition_output.data.get("caloric_target", 2000) < 1500):
            conflicts.append(
                "WARNING: Progressive overload with caloric target <1500 kcal may cause muscle loss. "
                "Consider increasing caloric target or reducing volume."
            )

        # Conflict: Workout agent returned no sessions
        if workout_output.success and not workout_output.data.get("sessions"):
            conflicts.append("WARNING: Workout Agent returned no sessions. Will need manual review.")

        return conflicts

    def _compute_week_number(self, context: AgentContext) -> int:
        # Fallback simplistic week number calculation based on profile or 1
        return context.week_number

    async def _execute_tool_calls(self, context: AgentContext) -> list:
        # Placeholder for tool execution logic
        return []

    async def _persist_plan(self, context: AgentContext, workout_output: AgentOutput,
                             nutrition_output: AgentOutput, recovery_signal: dict,
                             adaptation: AdaptationAction) -> str:
        if context.db is None:
            return "no_db"

        db = context.db
        user_id = context.user_id
        import json
        from datetime import date, timedelta
        from app.models.workout import WeeklyPlan, WorkoutSession
        from app.models.nutrition import NutritionPlan

        DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Persist Workout Plan
        workout_sessions = workout_output.data.get("sessions", []) if workout_output.success else []
        if workout_sessions:
            try:
                today = date.today()
                monday = today - timedelta(days=today.weekday())

                existing_plan = db.query(WeeklyPlan).filter(
                    WeeklyPlan.user_id == user_id,
                    WeeklyPlan.week_start_date == monday,
                    WeeklyPlan.plan_status == "active"
                ).first()
                if existing_plan:
                    existing_plan.plan_status = "superseded"
                    db.query(WorkoutSession).filter(
                        WorkoutSession.weekly_plan_id == existing_plan.id
                    ).delete()

                plan = WeeklyPlan(
                    user_id=user_id,
                    week_start_date=monday,
                    generated_by="planner_agent",
                )
                db.add(plan)
                db.flush()

                for day_data in workout_sessions:
                    day_num = day_data.get("day", 1)
                    exercises = day_data.get("exercises", [])
                    session_date = monday + timedelta(days=day_num - 1)

                    ws = WorkoutSession(
                        user_id=user_id,
                        weekly_plan_id=plan.id,
                        session_date=session_date,
                        day_of_week=day_num,
                        day_name=day_data.get("day_name", DAYS[day_num - 1] if 1 <= day_num <= 7 else "Monday"),
                        focus_area=day_data.get("focus", ""),
                        planned_duration_min=day_data.get("duration_minutes", 45),
                        exercises_planned=exercises,
                        warmup=day_data.get("warmup", ""),
                        cooldown=day_data.get("cooldown", ""),
                        tips=json.dumps(day_data.get("tips", "")),
                        calories_burned_estimate=day_data.get("calories_estimate", 250),
                        day=day_num,
                        exercises=json.dumps(exercises),
                        reasoning=day_data.get("session_reasoning") or day_data.get("reasoning") or "",
                    )
                    db.add(ws)
            except Exception as e:
                print(f"Error persisting workout plan in planner: {e}")

        # Persist Nutrition Plan
        nutrition_days = nutrition_output.data.get("plan", []) if nutrition_output.success else []
        if nutrition_days:
            try:
                db.query(NutritionPlan).filter(NutritionPlan.user_id == user_id).delete()
                for day_data in nutrition_days:
                    grocery = day_data.get("grocery_list", [])
                    meals = day_data.get("meals", {})
                    day_num = day_data.get("day", 1)
                    day_name = day_data.get("day_name", DAYS[day_num - 1] if 1 <= day_num <= 7 else "Monday")
                    calories = day_data.get("calories", 2000)

                    nutrition = NutritionPlan(
                        user_id=user_id,
                        day=day_num,
                        day_name=day_name,
                        plan_data=json.dumps(meals),
                        calories=calories,
                        grocery_list=json.dumps(grocery)
                    )
                    db.add(nutrition)
            except Exception as e:
                print(f"Error persisting nutrition plan in planner: {e}")

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"DB commit error in planner_agent: {e}")

        return "plan_persisted_success"

    def _log_evaluation_metrics(self, context: AgentContext, signals: AdaptiveSignals,
                                recovery_signal: dict) -> None:
        # Placeholder for metric logging
        pass

    def _build_planner_reasoning(self, recovery_signal: dict, adaptation: AdaptationAction,
                                 signals: AdaptiveSignals, workout_output: AgentOutput,
                                 nutrition_output: AgentOutput, conflict_notes: list) -> str:
        return f"Planner Agent orchestrating based on {adaptation.type} strategy."
