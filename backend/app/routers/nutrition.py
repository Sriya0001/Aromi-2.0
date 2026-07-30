from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.nutrition_service import generate_meal_plan, get_all_nutrition, get_shopping_list

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


def _get_user_profile(user: User, db: Session) -> dict:
    """Build user profile dict from HealthProfile (AroMi 2.0 schema)."""
    from app.models.health_profile import HealthProfile
    profile = db.query(HealthProfile).filter(
        HealthProfile.user_id == user.id
    ).first()
    if profile:
        return profile.to_agent_context()
    # Fallback for users without a profile
    return {
        "age": None, "gender": None, "weight_kg": 70, "height_cm": 170,
        "fitness_level": "beginner", "primary_goal": "general_fitness",
        "diet_type": "vegetarian", "food_allergies": [],
        "health_conditions": None, "injuries": None,
        # legacy keys
        "fitness_goal": "general_fitness", "diet_preference": "vegetarian",
        "allergies": "none",
    }


@router.post("/generate")
async def generate_nutrition_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered 7-day nutrition plan."""
    user_profile = _get_user_profile(current_user, db)
    
    try:
        plan = await generate_meal_plan(user_profile, db, current_user.id)
        return {"status": "success", "plan": plan, "message": "Your 7-day nutrition plan is ready!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan")
def get_nutrition_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all nutrition plans."""
    plans = get_all_nutrition(db, current_user.id)
    return {"plan": plans}


@router.get("/shopping-list")
def get_shopping_list_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consolidated weekly shopping list."""
    items = get_shopping_list(db, current_user.id)
    first_item_query = items[0]["name"] if items else "groceries"
    bigbasket_url = f"https://www.bigbasket.com/ps/?q={first_item_query}"
    return {
        "items": items,
        "bigbasket_url": bigbasket_url,
        "total_items": len(items)
    }
