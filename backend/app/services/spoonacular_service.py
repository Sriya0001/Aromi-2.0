import httpx
from typing import Optional
from app.core.config import settings


async def search_recipe(meal_name: str) -> Optional[dict]:
    """Search Spoonacular for a recipe matching the meal name.
    Returns recipe image, source URL, and nutrition data."""
    if not settings.SPOONACULAR_API_KEY:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spoonacular.com/recipes/complexSearch",
                params={
                    "query": meal_name,
                    "number": 1,
                    "addRecipeInformation": True,
                    "addRecipeNutrition": True,
                    "apiKey": settings.SPOONACULAR_API_KEY,
                },
                timeout=10.0,
            )
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            recipe = results[0]

            # Extract nutrition safely
            nutrition = recipe.get("nutrition", {})
            nutrients = {
                n["name"]: round(n["amount"], 1)
                for n in nutrition.get("nutrients", [])
                if n["name"] in ("Calories", "Protein", "Carbohydrates", "Fat")
            }

            return {
                "recipe_id": recipe.get("id"),
                "recipe_title": recipe.get("title"),
                "recipe_image": recipe.get("image"),
                "recipe_url": recipe.get("sourceUrl"),
                "ready_in_minutes": recipe.get("readyInMinutes"),
                "servings": recipe.get("servings"),
                "spoonacular_calories": nutrients.get("Calories"),
                "spoonacular_protein": nutrients.get("Protein"),
                "spoonacular_carbs": nutrients.get("Carbohydrates"),
                "spoonacular_fat": nutrients.get("Fat"),
            }

    except Exception as e:
        print(f"Spoonacular API error for '{meal_name}': {e}")
        return None


async def enrich_meal(meal: dict) -> dict:
    """Add Spoonacular recipe data to a meal dict (same pattern as enrich_exercise)."""
    meal_name = meal.get("name", "")
    if not meal_name:
        return meal

    recipe_info = await search_recipe(meal_name)
    meal["spoonacular"] = recipe_info  # None if API fails — handled gracefully
    return meal
