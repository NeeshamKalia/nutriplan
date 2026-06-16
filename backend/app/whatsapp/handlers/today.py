from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import date
from app.models.client import Client
from app.models.meal_plan import MealPlan, MealPlanDay
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.message_formatter import format_daily_plan

async def handle_today(db: AsyncSession, client: Client, to_number: str):
    # Fetch active plan
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.client_id == client.id)
        .where(MealPlan.status == 'delivered')
        .order_by(MealPlan.created_at.desc())
    )
    plan = result.scalars().first()
    
    if not plan:
        await whatsapp_service.send_text_message(
            to_number,
            "You don't have an active meal plan yet.",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
        return
        
    # Calculate day number based on week_start_date
    today = date.today()
    if plan.week_start_date:
        delta = (today - plan.week_start_date).days
        day_num = (delta % 7) + 1
    else:
        day_num = today.isoweekday() # 1-7 (Monday is 1)
        
    # Load MealPlanDay with items
    result = await db.execute(
        select(MealPlanDay)
        .options(selectinload(MealPlanDay.items))
        .where(MealPlanDay.meal_plan_id == plan.id)
        .where(MealPlanDay.day_number == day_num)
    )
    day = result.scalars().first()
    
    if not day:
        await whatsapp_service.send_text_message(
            to_number,
            "Couldn't find today's plan details.",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
        return

    msg = format_daily_plan(day)
    await whatsapp_service.send_text_message(
        to_number,
        msg,
        db=db,
        client_id=client.id,
        dietitian_id=client.dietitian_id,
    )
