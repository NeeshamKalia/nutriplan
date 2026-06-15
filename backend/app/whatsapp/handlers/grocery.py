from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.client import Client
from app.models.meal_plan import MealPlan, MealPlanDay
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.message_formatter import format_grocery_list

async def handle_grocery(db: AsyncSession, client: Client, to_number: str):
    result = await db.execute(
        select(MealPlan)
        .options(selectinload(MealPlan.days).selectinload(MealPlanDay.items))
        .where(MealPlan.client_id == client.id)
        .where(MealPlan.status == 'delivered')
        .order_by(MealPlan.created_at.desc())
    )
    plan = result.scalar_first()
    
    if not plan:
        await whatsapp_service.send_text_message(to_number, "You don't have an active meal plan yet.")
        return
        
    msg = format_grocery_list(plan)
    await whatsapp_service.send_text_message(to_number, msg)
