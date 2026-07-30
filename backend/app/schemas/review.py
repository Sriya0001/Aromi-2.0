from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    name: str
    role: Optional[str] = None
    emoji: Optional[str] = None
    rating: int = 5
    text: str

class ReviewCreate(ReviewBase):
    user_id: Optional[int] = None

class ReviewResponse(ReviewBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
