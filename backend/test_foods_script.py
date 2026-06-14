import asyncio
from app.models.food_item import FoodItem
from app.database import async_session

async def run():
    print("Testing FoodItem creation...")
    foods = [
        FoodItem(
            name="Roti", category="grains", is_vegetarian=True, is_vegan=True,
            is_gluten_free=False, calories_per_100g=297, protein_per_100g=9.0,
            carbs_per_100g=58.0, fat_per_100g=3.0, common_allergens=["wheat"]
        )
    ]
    print(foods[0].name)
    print("Done")

if __name__ == "__main__":
    asyncio.run(run())
