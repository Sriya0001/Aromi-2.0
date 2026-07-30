from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class WorkoutPlanResponse(BaseModel):
    id: int
    user_id: int
    day: int
    day_name: Optional[str]
    exercises: str   # JSON
    warmup: Optional[str]
    cooldown: Optional[str]
    tips: Optional[str]
    duration_minutes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class NutritionPlanResponse(BaseModel):
    id: int
    user_id: int
    day: int
    day_name: Optional[str]
    meals: str   # JSON
    calories: Optional[int]
    protein: Optional[float]
    carbs: Optional[float]
    fat: Optional[float]
    grocery_list: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProgressCreate(BaseModel):
    calories_burned: float = 0
    workouts_completed: int = 0
    weight: Optional[float] = None
    sets_completed: int = 0
    workout_duration: int = 0
    healthy_meals: int = 0
    notes: Optional[str] = None
    date: Optional[str] = None


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    date: str
    calories_burned: float
    workouts_completed: int
    weight: Optional[float]
    sets_completed: int
    workout_duration: int
    healthy_meals: int
    notes: Optional[str]

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime

    class Config:
        from_attributes = True
