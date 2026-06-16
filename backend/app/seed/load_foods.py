import asyncio
import json
import logging
import os
import sys

# Add the project root to sys.path if not running from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from app.database import async_session
from app.models.food_item import FoodItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_food_items(file_path: str):
    logger.info(f"Loading food items from {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    async with async_session() as session:
        for item_data in data:
            # Check if exists
            # We can use the name as a unique check for seed purposes
            from sqlalchemy import select
            result = await session.execute(
                select(FoodItem).where(FoodItem.name == item_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                food = FoodItem(**item_data)
                session.add(food)
                logger.info(f"Added: {food.name}")
            else:
                logger.debug(f"Skipped (already exists): {existing.name}")
                
        await session.commit()
    logger.info("Food database seeding complete.")


if __name__ == "__main__":
    # Expect the file to be at backend/seed/food_items.json
    seed_file = os.path.join(os.path.dirname(__file__), "../..", "seed", "food_items.json")
    asyncio.run(load_food_items(seed_file))
