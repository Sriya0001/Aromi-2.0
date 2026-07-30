from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.calendar_service import calendar_service
from app.core.config import settings
import json

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("/authorize")
async def authorize(current_user: User = Depends(get_current_user)):
    flow = calendar_service.get_flow()
    # Pass user_id in state to link back in callback
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=str(current_user.id)
    )
    return {"authorization_url": authorization_url}

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    user_id = request.query_params.get("state")
    
    if not code or not user_id:
        raise HTTPException(status_code=400, detail="Required parameters missing")
    
    flow = calendar_service.get_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    token_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # Save to user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user:
        user.google_token_data = json.dumps(token_data)
        user.calendar_sync = "yes"
        db.commit()
    
    # Redirect back to frontend dashboard
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?calendar=success")

@router.post("/sync")
async def sync_calendar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.google_token_data:
        raise HTTPException(status_code=400, detail="Google account not linked")
    
    try:
        from app.services.workout_service import get_all_workouts
        from app.services.nutrition_service import get_all_nutrition
        from datetime import datetime, timedelta
        
        workouts = get_all_workouts(db, current_user.id)
        nutrition = get_all_nutrition(db, current_user.id)
        
        # Start syncing for the next 7 days starting today
        start_date = datetime.now()
        
        events_created = 0
        
        for i in range(7):
            current_day_date = start_date + timedelta(days=i)
            day_num = current_day_date.weekday() + 1
            
            # Find workout for this day
            day_workout = next((w for w in workouts if w['day'] == day_num), None)
            if day_workout:
                exercises_str = "\n".join([f"- {ex['name']}: {ex['sets']} sets x {ex['reps']} reps" for ex in day_workout['exercises']])
                description = f"Workout focus: {day_workout.get('focus', 'General')}\n\nExercises:\n{exercises_str}\n\nWarmup: {day_workout['warmup']}\nCooldown: {day_workout['cooldown']}"
                
                # Default workout time: 8 AM
                st = current_day_date.replace(hour=8, minute=0, second=0, microsecond=0)
                et = st + timedelta(minutes=day_workout.get('duration_minutes', 45))
                
                calendar_service.create_event(
                    current_user.google_token_data,
                    f"🏋️ Workout: {day_workout['day_name']}",
                    description,
                    st, et
                )
                events_created += 1

            # Find nutrition for this day
            day_nutri = next((n for n in nutrition if n['day'] == day_num), None)
            if day_nutri:
                meals = day_nutri.get('meals', {})
                for meal_type, meal_desc in meals.items():
                    # Map meal types to times
                    hour = 9 if meal_type == 'breakfast' else 13 if meal_type == 'lunch' else 16 if meal_type == 'snack' else 20
                    st = current_day_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    et = st + timedelta(minutes=30)
                    
                    calendar_service.create_event(
                        current_user.google_token_data,
                        f"🥗 {meal_type.capitalize()}: {meal_desc}",
                        f"Nutrition Goal: {day_nutri['calories']} kcal\nProtein: {day_nutri['protein']}g, Carbs: {day_nutri['carbs']}g, Fat: {day_nutri['fat']}g",
                        st, et
                    )
                    events_created += 1

        return {"status": "success", "message": f"Successfully synced {events_created} events to your Google Calendar! 📅"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
