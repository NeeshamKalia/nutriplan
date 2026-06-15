def format_daily_plan(plan_day) -> str:
    """Format a single day's plan into an emoji-rich WhatsApp message."""
    msg = f"📅 *{plan_day.day_label}'s Plan*\n\n"
    
    # Sort items by sort_order
    items = sorted(plan_day.items, key=lambda x: x.sort_order) if hasattr(plan_day, "items") else []
    
    for item in items:
        # map meal types to emojis
        emoji = "🍽️"
        if item.meal_type == "breakfast": emoji = "🌅"
        elif item.meal_type == "lunch": emoji = "☀️"
        elif item.meal_type == "dinner": emoji = "🌙"
        elif "snack" in item.meal_type: emoji = "🍎"
        
        msg += f"{emoji} *{item.meal_type.title().replace('_', ' ')}*\n"
        msg += f"• {item.food_name} ({item.portion_description})\n"
        if item.preparation_notes:
            msg += f"  _Note: {item.preparation_notes}_\n"
        msg += "\n"
        
    msg += f"📊 Totals: {plan_day.total_calories or 0} kcal | {plan_day.total_protein_g or 0}g Protein\n"
    return msg

def format_grocery_list(plan) -> str:
    """Aggregate all ingredients for a weekly plan."""
    msg = "🛒 *Grocery List*\n\n"
    
    items_set = set()
    days = plan.days if hasattr(plan, "days") else []
    
    for day in days:
        items = day.items if hasattr(day, "items") else []
        for item in items:
            items_set.add(item.food_name)
    
    for food in sorted(items_set):
        msg += f"• {food}\n"
        
    if not items_set:
        msg += "No items found in the plan."
        
    return msg
