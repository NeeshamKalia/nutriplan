"""Tests for AI plan validations."""

from app.ai.plan_validator import check_allergens, check_calorie_range, check_dietary_type

def test_check_allergens():
    plan_data = {
        "days": [
            {
                "items": [
                    {"food_name": "Peanut Butter Toast"},
                    {"food_name": "Apple"}
                ]
            }
        ]
    }
    
    # Should fail due to peanut allergy
    res = check_allergens(plan_data, ["Peanut"])
    assert res["passed"] is False
    assert "Peanut" in res["message"]
    
    # Should pass
    res = check_allergens(plan_data, ["Dairy", "Soy"])
    assert res["passed"] is True

def test_check_calorie_range():
    plan_data = {
        "days": [
            {
                "items": [
                    {"calories": 500},
                    {"calories": 600}
                ]
            },
            {
                "items": [
                    {"calories": 450},
                    {"calories": 550}
                ]
            }
        ]
    }
    # Average is (1100 + 1000) / 2 = 1050
    
    res = check_calorie_range(plan_data, 1000, 0.1) # 900 to 1100
    assert res["passed"] is True
    
    res = check_calorie_range(plan_data, 2000, 0.1) # 1800 to 2200
    assert res["passed"] is False

def test_check_dietary_type():
    plan_data = {
        "days": [
            {
                "items": [
                    {"food_name": "Chicken Curry"},
                    {"food_name": "Roti"}
                ]
            }
        ]
    }
    
    res = check_dietary_type(plan_data, "vegetarian")
    assert res["passed"] is False
    assert "Chicken Curry" in res["message"]
    
    plan_data_veg = {
        "days": [
            {
                "items": [
                    {"food_name": "Paneer Tikka"},
                    {"food_name": "Roti"}
                ]
            }
        ]
    }
    res = check_dietary_type(plan_data_veg, "vegetarian")
    assert res["passed"] is True
    
    res = check_dietary_type(plan_data_veg, "vegan")
    assert res["passed"] is False
    assert "Paneer Tikka" in res["message"]
