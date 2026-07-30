from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ExerciseBase(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    sets: str
    reps: str
    rest_seconds: Optional[int] = 60
    instructions: Optional[str] = None
    youtube_query: Optional[str] = None
    video: Optional[dict] = None

class WorkoutBase(BaseModel):
    day: int
    day_name: Optional[str] = None
    exercises: List[ExerciseBase]
    warmup: Optional[str] = None
    cooldown: Optional[str] = None
    tips: Optional[Any] = None
    duration_minutes: Optional[int] = 45

class FavouriteExerciseCreate(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    sets: Optional[str] = None
    reps: Optional[str] = None
    rest_seconds: Optional[int] = 60
    instructions: Optional[str] = None
    video_url: Optional[str] = None
    video_id: Optional[str] = None

class FavouriteExerciseResponse(BaseModel):
    id: int
    user_id: int
    name: str
    muscle_group: Optional[str] = None
    sets: Optional[str] = None
    reps: Optional[str] = None
    rest_seconds: Optional[int] = 60
    instructions: Optional[str] = None
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
