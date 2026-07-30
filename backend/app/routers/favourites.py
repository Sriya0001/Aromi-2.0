from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workout import FavouriteExercise
from app.schemas.workout import FavouriteExerciseCreate, FavouriteExerciseResponse

router = APIRouter(prefix="/favourites", tags=["Favourites"])

@router.get("/", response_model=List[FavouriteExerciseResponse])
def get_favourites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all favourite exercises for the current user."""
    return db.query(FavouriteExercise).filter(FavouriteExercise.user_id == current_user.id).order_by(FavouriteExercise.created_at.desc()).all()

@router.post("/", response_model=FavouriteExerciseResponse)
def add_favourite(
    exercise: FavouriteExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an exercise to favourites."""
    db_fav = FavouriteExercise(
        user_id=current_user.id,
        name=exercise.name,
        muscle_group=exercise.muscle_group,
        sets=exercise.sets,
        reps=exercise.reps,
        rest_seconds=exercise.rest_seconds,
        instructions=exercise.instructions,
        video_url=exercise.video_url,
        video_id=exercise.video_id
    )
    db.add(db_fav)
    db.commit()
    db.refresh(db_fav)
    return db_fav

@router.delete("/{fav_id}")
def remove_favourite(
    fav_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove an exercise from favourites."""
    db_fav = db.query(FavouriteExercise).filter(
        FavouriteExercise.id == fav_id,
        FavouriteExercise.user_id == current_user.id
    ).first()
    
    if not db_fav:
        raise HTTPException(status_code=404, detail="Favourite exercise not found")
        
    db.delete(db_fav)
    db.commit()
    return {"status": "success", "message": "Exercise removed from favourites"}
