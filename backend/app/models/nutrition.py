"""
NutritionLog model — tracks planned vs. actual meals.
Separate rows per meal enable per-meal adherence scoring,
not just per-day. This feeds the Nutrition Agent's context.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weekly_plan_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=True)

    log_date = Column(Date, nullable=False)
    meal_type = Column(String(30), nullable=True)  # breakfast/lunch/dinner/snack/pre_workout

    # Planned (from Nutrition Agent)
    planned_meal = Column(JSON, nullable=True)     # {name, ingredients, calories, protein, carbs, fat}

    # Actual (from user log)
    actual_meal = Column(JSON, nullable=True)
    calories_actual = Column(Integer, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)

    adherence = Column(Boolean, nullable=True)     # Did user eat what was planned?
    swap_reason = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)        # WHY this meal was recommended

    # Legacy compatibility
    plan_data = Column(Text, nullable=True)        # old full JSON plan string
    day = Column(Integer, nullable=True)
    day_name = Column(String(20), nullable=True)
    calories = Column(Integer, nullable=True)
    grocery_list = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="nutrition_logs")


class NutritionPlan(Base):
    """Legacy table — kept for backward compatibility. New code uses NutritionLog."""
    __tablename__ = "nutrition_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day = Column(Integer, nullable=False)
    day_name = Column(String(20), nullable=True)
    plan_data = Column(Text, nullable=False)
    calories = Column(Integer, nullable=True)
    grocery_list = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="nutrition_plans_legacy")
