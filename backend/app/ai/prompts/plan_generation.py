"""Prompts for AI plan generation."""

from app.models.client import Client
from app.models.food_item import FoodItem

SYSTEM_PROMPT = """You are a clinical nutrition AI assistant.
You generate structured Indian meal plans for clients based on their health profile.

RULES:
1. Use Indian food items with local names (roti, dal, sabzi — NOT "flatbread, lentil soup")
2. NEVER include any food the client is allergic to — ZERO TOLERANCE
3. Stay within the calorie target ±10%
4. Respect dietary type strictly (vegetarian = no meat/fish/eggs unless eggetarian)
5. Vary meals across 7 days — no identical meals on consecutive days
6. Include 5 meals per day: breakfast, mid_morning, lunch, evening_snack, dinner
7. Consider the client's monthly food budget when selecting ingredients
8. Include preparation notes for items that need them
9. Use common Indian portion descriptions (1 roti, 1 katori dal, 1 bowl rice)
10. Output MUST be valid JSON matching the exact schema provided

OUTPUT FORMAT:
The output must be a JSON object containing a 'days' array with exactly 7 items.
Each day must have 'day_number' (1-7), 'day_label' (e.g. 'Day 1'), and an 'items' array.
Each item must have 'meal_type' (breakfast, mid_morning, lunch, evening_snack, dinner), 'food_name', 'portion_description', 'portion_grams' (number), 'calories' (number), 'protein_g' (number), 'carbs_g' (number), 'fat_g' (number), and optionally 'preparation_notes'.
"""

def build_client_context(client: Client, food_items: list[FoodItem]) -> str:
    """Build a detailed prompt section from client profile."""
    allergies = ", ".join(client.allergies) if client.allergies else "None"
    conditions = ", ".join(client.medical_conditions) if client.medical_conditions else "None"
    dietary_type = client.dietary_type or "any"
    preferences = ", ".join(client.food_preferences) if client.food_preferences else "None"
    
    context = "Client Profile:\n"
    context += f"- Name: {client.full_name}\n"
    context += f"- Age: {client.age}, Gender: {client.gender}\n"
    context += f"- Weight: {client.weight_kg} kg, Target Weight: {client.target_weight_kg} kg\n"
    context += f"- Primary Goal: {client.primary_goal}\n"
    context += f"- Daily Calorie Target: {client.daily_calorie_target or 'Not specified, determine appropriate target'}\n"
    context += f"- Activity Level: {client.activity_level}\n"
    context += f"- Dietary Type: {dietary_type}\n"
    context += f"- Allergies (CRITICAL): {allergies}\n"
    context += f"- Medical Conditions: {conditions}\n"
    context += f"- Food Preferences: {preferences}\n"
    context += f"- Cuisine Preference: {client.cuisine_preference}\n"
    if client.monthly_food_budget_inr:
        context += f"- Monthly Food Budget: {client.monthly_food_budget_inr} INR\n"
    
    return context
