def format_daily_plan(plan_day) -> str:
    """Format a single day's plan into an emoji-rich WhatsApp message."""
    msg = f"📅 *{plan_day.day_label}'s Plan*\n\n"
    
    # Sort items by sort_order
    items = sorted(plan_day.items, key=lambda x: x.sort_order) if hasattr(plan_day, "items") else []
    
    for item in items:
        # map meal types to emojis
        emoji = "🍽️"
        if item.meal_type == "breakfast":
            emoji = "🌅"
        elif item.meal_type == "lunch":
            emoji = "☀️"
        elif item.meal_type == "dinner":
            emoji = "🌙"
        elif "snack" in item.meal_type:
            emoji = "🍎"
        
        msg += f"{emoji} *{item.meal_type.title().replace('_', ' ')}*\n"
        msg += f"• {item.food_name} ({item.portion_description})\n"
        if item.preparation_notes:
            msg += f"  _Note: {item.preparation_notes}_\n"
        msg += "\n"
        
    msg += f"📊 Totals: {plan_day.total_calories or 0} kcal | {plan_day.total_protein_g or 0}g Protein\n"
    return msg


def format_weekly_summary(
    first_name: str,
    completed: int,
    skipped: int,
    deviated: int,
    adherence_pct: float,
) -> str:
    """Format a 7-day adherence summary for WhatsApp."""
    total = completed + skipped + deviated
    msg = f"📊 *Weekly Check-in, {first_name}!*\n\n"
    msg += f"Last 7 days: *{adherence_pct:.0f}%* adherence\n"
    msg += f"✅ Completed: {completed}\n"
    msg += f"⏭️ Skipped: {skipped}\n"
    msg += f"🔄 Swapped/deviated: {deviated}\n"
    msg += f"📝 Total meals logged: {total}\n\n"
    if adherence_pct >= 80:
        msg += "Great consistency — keep it up! 💪"
    elif adherence_pct >= 60:
        msg += "Solid progress. Small improvements add up!"
    else:
        msg += "Reply *today* anytime to see your plan. You've got this!"
    return msg


def format_grocery_list(plan) -> str:
    """Aggregate ingredients for a weekly plan with quantities."""
    msg = "🛒 *Grocery List*\n\n"

    aggregated: dict[str, dict] = {}
    days = plan.days if hasattr(plan, "days") else []

    for day in days:
        items = day.items if hasattr(day, "items") else []
        for item in items:
            key = item.food_name.strip().lower()
            portion = (item.portion_description or "").strip()
            grams = float(item.portion_grams) if item.portion_grams else None

            if key not in aggregated:
                aggregated[key] = {
                    "name": item.food_name,
                    "portions": [],
                    "total_grams": 0.0,
                }

            if portion:
                aggregated[key]["portions"].append(portion)
            if grams:
                aggregated[key]["total_grams"] += grams

    if not aggregated:
        msg += "No items found in the plan."
        return msg

    for entry in sorted(aggregated.values(), key=lambda x: x["name"].lower()):
        line = f"• {entry['name']}"
        if entry["total_grams"] > 0:
            line += f" — ~{entry['total_grams']:.0f}g total"
        elif entry["portions"]:
            unique_portions = list(dict.fromkeys(entry["portions"]))
            if len(unique_portions) == 1:
                count = len(entry["portions"])
                line += f" — {count}× {unique_portions[0]}"
            else:
                line += f" — {', '.join(unique_portions)}"
        msg += line + "\n"

    return msg


def format_article_broadcast(
    dietitian_name: str,
    title: str,
    summary: str | None,
    article_link: str,
) -> str:
    """Format a published article for WhatsApp broadcast to clients."""
    msg = f"📚 *New article from {dietitian_name}*\n\n"
    msg += f"*{title}*\n"
    if summary:
        msg += f"{summary.strip()}\n"
    msg += f"\nRead more: {article_link}"
    return msg
