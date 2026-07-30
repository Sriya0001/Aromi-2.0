from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse
from typing import List

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/", response_model=List[ReviewResponse])
def get_reviews(db: Session = Depends(get_db)):
    return db.query(Review).order_by(Review.created_at.desc()).limit(10).all()

@router.post("/", response_model=ReviewResponse)
def create_review(
    review: ReviewCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review_data = review.dict()
    review_data["user_id"] = current_user.id
    
    db_review = Review(**review_data)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
