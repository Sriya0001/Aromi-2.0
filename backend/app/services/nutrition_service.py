import json
import asyncio
from sqlalchemy.orm import Session
from app.models.nutrition import NutritionPlan
from app.services.ai_service import generate_plan_with_groq
from app.ai.prompts import get_nutrition_prompt
from app.services.spoonacular_service import enrich_meal

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


async def generate_meal_plan(user_profile: dict, db: Session, user_id: int) -> list:
    """Generate a 7-day nutrition plan using Groq AI or Fallback."""
    
    prompt = get_nutrition_prompt(user_profile)
    plan_data = await generate_plan_with_groq(prompt)
    
    days_data = plan_data.get("plan", [])
    if not days_data:
        raise Exception("AI returned empty plan data")
        
    try:
        # Delete existing plans for user
        db.query(NutritionPlan).filter(NutritionPlan.user_id == user_id).delete()
        
        saved_plans = []
        for day_data in days_data:
            grocery = day_data.get("grocery_list", [])
            meals = day_data.get("meals", {})

            # Enrich each meal with Spoonacular recipe data (image, URL, macros)
            enriched_meals = {}
            if isinstance(meals, dict):
                for meal_type, meal_data in meals.items():
                    if isinstance(meal_data, dict):
                        enriched = await enrich_meal(meal_data)
                        enriched_meals[meal_type] = enriched
                    else:
                        enriched_meals[meal_type] = meal_data
            elif isinstance(meals, list):
                enriched_meals = {"meals": meals}

            day_num = day_data.get("day", 1)
            day_name = day_data.get("day_name", DAYS[day_num - 1] if 1 <= day_num <= 7 else "Monday")
            calories = day_data.get("calories", 2000)

            nutrition = NutritionPlan(
                user_id=user_id,
                day=day_num,
                day_name=day_name,
                plan_data=json.dumps(enriched_meals),
                calories=calories,
                grocery_list=json.dumps(grocery)
            )
            db.add(nutrition)
            
            plan_dict = {
                "day": day_num,
                "day_name": day_name,
                "meals": enriched_meals,
                "calories": calories,
                "protein": day_data.get("protein_g", day_data.get("protein", 80)),
                "carbs": day_data.get("carbs_g", day_data.get("carbs", 200)),
                "fat": day_data.get("fat_g", day_data.get("fat", 50)),
                "grocery_list": grocery,
                "hydration": day_data.get("hydration", "Drink 8 glasses of water")
            }
            saved_plans.append(plan_dict)
        
        db.commit() # Atomic commit for the entire 7-day meal plan
        return saved_plans
        
    except Exception as e:
        db.rollback()
        print(f"Database error in nutrition generation: {e}")
        raise Exception(f"Failed to save nutrition plan: {str(e)}")


def get_all_nutrition(db: Session, user_id: int) -> list:
    """Get all saved nutrition plans. Requires completed health assessment."""
    from app.models.health_profile import HealthProfile
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
    if not profile or profile.assessment_completed != "yes":
        return []

    plans = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == user_id
    ).order_by(NutritionPlan.day).all()

    # If user has an incomplete plan (e.g. 1-day fallback from earlier run), auto-regenerate 7-day plan
    if len(plans) < 7:
        try:
            from app.models.health_profile import HealthProfile
            profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
            user_profile = profile.to_agent_context() if profile else {"fitness_goal": "general_fitness"}
            
            # Run async generate_meal_plan synchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If called from an active event loop, run in task or separate loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, generate_meal_plan(user_profile, db, user_id))
                        future.result()
                else:
                    asyncio.run(generate_meal_plan(user_profile, db, user_id))
            except Exception:
                asyncio.run(generate_meal_plan(user_profile, db, user_id))

            plans = db.query(NutritionPlan).filter(
                NutritionPlan.user_id == user_id
            ).order_by(NutritionPlan.day).all()
        except Exception as e:
            print(f"Auto-regeneration of 7-day plan notice: {e}")
    
    # Deduplicate by day (keep the latest id for each day)
    unique_plans = {}
    for n in plans:
        d = n.day or 1
        if d not in unique_plans or n.id > unique_plans[d].id:
            unique_plans[d] = n

    deduped_plans = [unique_plans[d] for d in sorted(unique_plans.keys())]

    result = []
    for n in deduped_plans:
        meals_dict = {}
        if n.plan_data:
            try:
                meals_dict = json.loads(n.plan_data)
            except Exception:
                meals_dict = {}
        grocery = []
        if n.grocery_list:
            try:
                grocery = json.loads(n.grocery_list)
            except Exception:
                grocery = []

        result.append({
            "id": n.id,
            "day": n.day,
            "day_name": n.day_name,
            "meals": meals_dict,
            "calories": n.calories,
            "protein": 80,
            "carbs": 200,
            "fat": 50,
            "grocery_list": grocery
        })

    # Always sanitize returned plan for user's allergens & medical conditions
    try:
        from app.agents.nutrition_agent import NutritionAgent
        from app.agents.base import AgentContext
        nut_agent = NutritionAgent("dummy")
        hp = profile.to_agent_context() if profile else {}
        ctx = AgentContext(user_id=user_id, health_profile=hp, db=db)
        result = nut_agent._apply_nutrition_safety_filter(result, hp, ctx)
    except Exception as e:
        print(f"Notice: nutrition safety filter pass: {e}")

    return result


def get_shopping_list(db: Session, user_id: int) -> list:
    """Get consolidated shopping list from nutrition plans."""
    plans = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == user_id
    ).all()

    if not plans or len(plans) < 7:
        get_all_nutrition(db, user_id)
        plans = db.query(NutritionPlan).filter(
            NutritionPlan.user_id == user_id
        ).all()
    
    item_map = {}
    for plan in plans:
        if plan.grocery_list:
            try:
                items = json.loads(plan.grocery_list)
            except Exception:
                items = []
            for item in items:
                if isinstance(item, str):
                    name = item
                    quantity = "1 unit"
                elif isinstance(item, dict):
                    name = item.get("name", "Unknown")
                    quantity = item.get("quantity", "1 unit")
                else:
                    continue
                
                if name not in item_map:
                    item_map[name] = quantity
    
    result = []
    for name, qty in item_map.items():
        result.append({"name": name, "quantity": qty, "checked": True})
        
    return sorted(result, key=lambda x: x["name"])
