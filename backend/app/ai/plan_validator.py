"""Validation rules for generated AI meal plans."""

from app.models.client import Client

def check_allergens(plan_data: dict, allergies: list[str]) -> dict:
    """Check every food item against client's allergen list."""
    if not allergies:
        return {"type": "allergens", "passed": True, "severity": "info", "message": "No allergies to check."}
    
    allergen_lower = [a.lower() for a in allergies]
    violations = []
    
    for day in plan_data.get("days", []):
        for item in day.get("items", []):
            food_name = item.get("food_name", "").lower()
            for allergen in allergen_lower:
                if allergen in food_name:
                    violations.append(item.get("food_name"))
    
    if violations:
        return {
            "type": "allergens", 
            "passed": False, 
            "severity": "critical", 
            "message": f"CRITICAL: Found possible allergens in: {', '.join(set(violations))}"
        }
    return {"type": "allergens", "passed": True, "severity": "info", "message": "No allergens detected."}

def check_calorie_range(plan_data: dict, target: int, tolerance: float = 0.1) -> dict:
    """Check if average daily calories are within target ±tolerance."""
    if not target:
        return {"type": "calories", "passed": True, "severity": "info", "message": "No calorie target specified."}
    
    total_cals = 0
    days_count = len(plan_data.get("days", []))
    if days_count == 0:
        return {"type": "calories", "passed": False, "severity": "high", "message": "No days found in plan."}
        
    for day in plan_data.get("days", []):
        day_cals = sum(item.get("calories", 0) for item in day.get("items", []))
        total_cals += day_cals
        
    avg_cals = total_cals / days_count
    lower_bound = target * (1 - tolerance)
    upper_bound = target * (1 + tolerance)
    
    if lower_bound <= avg_cals <= upper_bound:
        return {"type": "calories", "passed": True, "severity": "info", "message": f"Calories ({avg_cals:.0f}) within target range."}
    else:
        return {
            "type": "calories", 
            "passed": False, 
            "severity": "medium", 
            "message": f"Average calories ({avg_cals:.0f}) outside target range ({lower_bound:.0f}-{upper_bound:.0f})."
        }

def check_dietary_type(plan_data: dict, dietary_type: str) -> dict:
    """Check no meat for veg, no dairy for vegan, etc."""
    if not dietary_type:
        return {"type": "dietary_type", "passed": True, "severity": "info", "message": "No dietary type specified."}
        
    diet_lower = dietary_type.lower()
    violations = []
    
    # Simple keyword checks
    non_veg_keywords = ["chicken", "meat", "beef", "pork", "fish", "egg", "mutton"]
    vegan_keywords = ["milk", "paneer", "ghee", "curd", "yogurt", "butter", "cheese", "honey"] + non_veg_keywords
    
    keywords_to_check = []
    if "vegan" in diet_lower:
        keywords_to_check = vegan_keywords
    elif "veg" in diet_lower and "non" not in diet_lower:
        if "egg" not in diet_lower:
            keywords_to_check = non_veg_keywords
        
    if not keywords_to_check:
         return {"type": "dietary_type", "passed": True, "severity": "info", "message": f"Dietary type {dietary_type} check passed."}
         
    for day in plan_data.get("days", []):
        for item in day.get("items", []):
            food_name = item.get("food_name", "").lower()
            for kw in keywords_to_check:
                if kw in food_name:
                    violations.append(item.get("food_name"))
                    
    if violations:
        return {
            "type": "dietary_type",
            "passed": False,
            "severity": "high",
            "message": f"Found non-{dietary_type} items: {', '.join(set(violations))}"
        }
    return {"type": "dietary_type", "passed": True, "severity": "info", "message": f"Dietary type {dietary_type} check passed."}

def run_all_validations(plan_data: dict, client: Client) -> list[dict]:
    """Run all checks, return list of {type, passed, severity, message}."""
    results = []
    results.append(check_allergens(plan_data, client.allergies or []))
    results.append(check_calorie_range(plan_data, client.daily_calorie_target or 0))
    results.append(check_dietary_type(plan_data, client.dietary_type or ""))
    return results
