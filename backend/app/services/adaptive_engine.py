import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.progress import ProgressRecord
from app.models.workout import WorkoutPlan
from app.services.ai_service import generate_plan_with_groq
from app.ai.prompts import get_workout_prompt
from app.services.workout_service import generate_7_day_plan

class AdaptiveEngine:
    @staticmethod
    def get_last_7_days_progress(db: Session, user_id: int):
        """Fetch progress records for the last 7 days."""
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        records = db.query(ProgressRecord).filter(
            ProgressRecord.user_id == user_id,
            ProgressRecord.date >= seven_days_ago
        ).all()
        return records

    @staticmethod
    def get_progress_trend(db: Session, user_id: int, days: int = 14):
        """Analyze the trend of progress over the last N days."""
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        records = db.query(ProgressRecord).filter(
            ProgressRecord.user_id == user_id,
            ProgressRecord.date >= start_date
        ).order_by(ProgressRecord.date.asc()).all()
        
        if len(records) < 7:
            return "insufficient_data"
        
        # Simple trend check: Compare first half with second half
        mid = len(records) // 2
        first_half = records[:mid]
        second_half = records[mid:]
        
        avg_calories_1 = sum(r.calories_burned for r in first_half) / len(first_half)
        avg_calories_2 = sum(r.calories_burned for r in second_half) / len(second_half)
        
        if avg_calories_2 <= avg_calories_1 * 1.05: # Less than 5% improvement
             return "plateau"
        return "improving"

    @staticmethod
    async def analyze_and_regenerate_plan(db: Session, user: any):
        """Analyze performance and regenerate the plan with goal-specific strategies."""
        records = AdaptiveEngine.get_last_7_days_progress(db, user.id)
        trend = AdaptiveEngine.get_progress_trend(db, user.id)
        
        total_workouts = sum(r.workouts_completed for r in records)
        total_calories = sum(r.calories_burned for r in records)
        
        completion_ratio = total_workouts / 7.0
        
        # Base adjustment
        adjustment_note = ""
        if completion_ratio >= 0.8:
            adjustment_note = "High completion. Apply progressive overload (+10% reps)."
        elif completion_ratio < 0.4:
            adjustment_note = "Low completion. Scale back intensity."
            
        # Plateau adjustment
        if trend == "plateau":
            adjustment_note += " PLATEU DETECTED: Increase training stimulus and vary exercises to break stagnant progress."

        # Goal-Specific Strategy
        goal = (user.fitness_goal or "").lower()
        strategy = "General improvement."
        if "loss" in goal:
             strategy = "Focus: Calorie Deficit + HIIT. Optimize for fat oxidation."
        elif "muscle" in goal or "gain" in goal:
             strategy = "Focus: Progressive Overload. Optimize for hypertrophy (8-12 rep ranges)."
        elif "endurance" in goal:
             strategy = "Focus: Volume Progression. Increase duration and reduce rest."
        elif "mobility" in goal or "flexibility" in goal:
             strategy = "Focus: Recovery & Active Stretching. Prioritize range of motion."

        user_profile = {
            "age": user.age,
            "gender": user.gender,
            "weight": user.weight,
            "height": user.height,
            "fitness_level": user.fitness_level,
            "fitness_goal": user.fitness_goal,
            "performance_context": f"{adjustment_note} {strategy}",
            "total_workouts_last_week": total_workouts,
            "total_calories_burned_last_week": total_calories
        }

        return await generate_7_day_plan(user_profile, db, user.id)

adaptive_engine = AdaptiveEngine()
