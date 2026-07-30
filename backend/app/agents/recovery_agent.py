"""
Recovery Agent — computes readiness score from biometric signals.

WHY this agent exists:
The current system has no concept of recovery readiness. It generates the same
intensity workout regardless of sleep, HRV, consecutive training days, or soreness.
This agent is the system's safeguard against overtraining and injury.

The readiness score is a HARD CONSTRAINT passed to the Workout Agent:
- readiness >= 0.7  → allow progressive overload
- 0.4 <= readiness < 0.7  → maintain current volume
- readiness < 0.4  → force deload or active recovery

Evaluation: Track correlation between readiness score and self-reported
difficulty_felt (too_hard correlation should be negative with readiness).
"""
from app.agents.base import BaseAgent, AgentContext, AgentOutput
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional


class RecoveryAgent(BaseAgent):
    name = "recovery_agent"

    # Readiness score weights — can be tuned via ablation study
    WEIGHTS = {
        "sleep_quality": 0.35,      # Most impactful recovery signal
        "consecutive_days": 0.30,   # Cumulative fatigue
        "hrv": 0.20,                # Objective physiological marker
        "user_energy": 0.15,        # Self-reported, lower weight (subjective)
    }

    async def run(self, context: AgentContext, **kwargs) -> AgentOutput:
        """
        Compute readiness score from available signals.
        Gracefully degrades when signals are missing.
        """
        import time
        start = time.time()
        db = context.db
        user_id = context.user_id

        signals = self._gather_signals(db, user_id, context)
        readiness_score = self._compute_readiness(signals)
        recommendation = self._get_recommendation(readiness_score)
        volume_modifier = self._get_volume_modifier(readiness_score)

        reasoning = self._build_reasoning(signals, readiness_score, recommendation)

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "readiness_score": round(readiness_score, 3),
                "recommendation": recommendation,
                "volume_modifier": volume_modifier,
                "signals_used": signals,
                "rest_duration_increase": self._rest_increase(readiness_score),
            },
            reasoning=reasoning,
            latency_ms=int((time.time() - start) * 1000)
        )

    def _gather_signals(self, db, user_id: int, context: AgentContext) -> dict:
        """Gather all recovery signals from DB and profile."""
        signals = {
            "sleep_quality_avg": 5.0,     # default: fair
            "sleep_hours_avg": 7.0,
            "hrv_score": None,             # None = not available
            "consecutive_training_days": 0,
            "user_energy": 5,             # default from profile
            "data_quality": "low",        # how many signals available
        }

        if db is None:
            return signals

        try:
            from app.models.progress import SleepLog
            from app.models.workout import WorkoutSession
            from datetime import date

            # Sleep signals (last 3 days)
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            sleep_logs = db.query(SleepLog).filter(
                SleepLog.user_id == user_id,
                SleepLog.sleep_date >= three_days_ago.date()
            ).all()

            if sleep_logs:
                signals["sleep_quality_avg"] = sum(s.quality_score or 5 for s in sleep_logs) / len(sleep_logs)
                signals["sleep_hours_avg"] = sum(s.duration_hours or 7 for s in sleep_logs) / len(sleep_logs)
                hrv_values = [s.hrv_ms for s in sleep_logs if s.hrv_ms is not None]
                if hrv_values:
                    signals["hrv_score"] = sum(hrv_values) / len(hrv_values)

            # Consecutive training days
            today = date.today()
            completed_sessions = db.query(WorkoutSession).filter(
                WorkoutSession.user_id == user_id,
                WorkoutSession.status == "completed",
                WorkoutSession.session_date >= today - timedelta(days=7)
            ).order_by(WorkoutSession.session_date.desc()).all()

            consecutive = 0
            check_date = today
            for session in completed_sessions:
                if session.session_date == check_date or session.session_date == check_date - timedelta(days=1):
                    consecutive += 1
                    check_date = session.session_date - timedelta(days=1)
                else:
                    break
            signals["consecutive_training_days"] = consecutive

            # Data quality
            available_signals = sum([
                1 if sleep_logs else 0,
                1 if signals["hrv_score"] is not None else 0,
                1 if consecutive > 0 else 0,
            ])
            signals["data_quality"] = ["low", "medium", "high"][min(available_signals, 2)]

        except Exception as e:
            print(f"Recovery Agent signal gathering error: {e}")

        # User energy from profile (stress level as proxy)
        stress = context.health_profile.get("stress_level", 5)
        signals["user_energy"] = max(1, 10 - stress)  # high stress → low energy

        return signals

    def _compute_readiness(self, signals: dict) -> float:
        """
        Weighted readiness score: 0.0 (exhausted) to 1.0 (fully recovered).

        Formula:
          readiness = w_sleep * norm(sleep_quality) +
                      w_consecutive * norm(8 - consecutive_days) +  # cap at 8
                      w_hrv * norm(hrv) +
                      w_energy * norm(user_energy)

        Trade-off: Rule-based is interpretable but brittle.
        Future: replace with learned policy from (signals → next_day_performance) data.
        """
        w = self.WEIGHTS

        # Normalize sleep quality (1-10 → 0-1)
        sleep_score = (signals["sleep_quality_avg"] - 1) / 9
        # Penalize if sleep hours < 6
        if signals["sleep_hours_avg"] < 6:
            sleep_score *= 0.7

        # Consecutive days penalty (4+ days → score drops)
        consec_days = signals["consecutive_training_days"]
        consecutive_score = max(0.0, 1.0 - (consec_days / 6.0))

        # HRV (if available) — normalize relative to 40ms baseline
        hrv = signals.get("hrv_score")
        hrv_score = min(1.0, (hrv / 60.0)) if hrv is not None else 0.5  # default 0.5 when unavailable

        # User energy (1-10 → 0-1)
        energy_score = (signals["user_energy"] - 1) / 9

        readiness = (
            w["sleep_quality"] * sleep_score +
            w["consecutive_days"] * consecutive_score +
            w["hrv"] * hrv_score +
            w["user_energy"] * energy_score
        )

        return round(max(0.0, min(1.0, readiness)), 3)

    def _get_recommendation(self, score: float) -> str:
        if score >= 0.70:
            return "progressive_overload"
        elif score >= 0.50:
            return "maintain_volume"
        elif score >= 0.35:
            return "reduce_volume"
        else:
            return "active_recovery_only"

    def _get_volume_modifier(self, score: float) -> float:
        """Volume multiplier for workout agent."""
        if score >= 0.70:
            return 1.10
        elif score >= 0.50:
            return 1.00
        elif score >= 0.35:
            return 0.75
        else:
            return 0.50

    def _rest_increase(self, score: float) -> int:
        """Additional rest seconds per set based on readiness."""
        if score >= 0.70:
            return 0
        elif score >= 0.50:
            return 15
        elif score >= 0.35:
            return 30
        else:
            return 60

    def _build_reasoning(self, signals: dict, score: float, recommendation: str) -> str:
        parts = [
            f"Readiness score: {score:.2f} ({recommendation.replace('_', ' ').title()})",
            f"Sleep quality avg (3d): {signals['sleep_quality_avg']:.1f}/10, {signals['sleep_hours_avg']:.1f}h",
            f"Consecutive training days: {signals['consecutive_training_days']}",
        ]
        if signals.get("hrv_score"):
            parts.append(f"HRV: {signals['hrv_score']:.0f}ms")
        parts.append(f"Data quality: {signals['data_quality']} (more wearable data improves accuracy)")
        return ". ".join(parts)
