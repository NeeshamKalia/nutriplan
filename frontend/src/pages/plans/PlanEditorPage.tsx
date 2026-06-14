import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { plansApi } from '../../api/plans';
import { MealPlan, MealPlanDay, FoodItem, MealPlanItem } from '../../types/plan';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { FoodSearchModal } from '../../components/plans/FoodSearchModal';

import './PlanEditorPage.css';

const MEAL_TYPES = ['breakfast', 'mid_morning', 'lunch', 'evening_snack', 'dinner', 'bedtime'];

export const PlanEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeDay, setActiveDay] = useState<number>(1);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null);

  useEffect(() => {
    loadPlan();
  }, [id]);

  const loadPlan = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await plansApi.getPlan(id);
      setPlan(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load meal plan.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!plan) return;
    try {
      await plansApi.approvePlan(plan.id);
      await loadPlan(); // Reload to get updated status
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve plan.');
    }
  };

  const handleAddFoodClick = (mealType: string) => {
    setSelectedMealType(mealType);
    setIsSearchOpen(true);
  };

  const handleFoodSelect = async (food: FoodItem) => {
    setIsSearchOpen(false);
    if (!plan || !currentDay || !selectedMealType) return;
    
    // In a real app, we would make an API call here to add the item
    // For now, we update local state to reflect UI changes
    const newItem: MealPlanItem = {
      id: Math.random().toString(),
      meal_plan_day_id: currentDay.id,
      meal_type: selectedMealType as any,
      sort_order: 0,
      food_name: food.name,
      food_name_hindi: food.name_hindi,
      portion_description: food.default_serving_description,
      portion_grams: food.default_serving_grams,
      calories: food.calories_per_100g, // naive calculation
      protein_g: food.protein_per_100g,
      carbs_g: food.carbs_per_100g,
      fat_g: food.fat_per_100g,
    };
    
    const updatedPlan = { ...plan };
    const dayIndex = updatedPlan.days.findIndex(d => d.id === currentDay.id);
    if (dayIndex >= 0) {
      updatedPlan.days[dayIndex].items.push(newItem);
      
      // Attempt API update (assuming updating the whole plan works)
      try {
        await plansApi.updatePlan(plan.id, { days: updatedPlan.days });
        setPlan(updatedPlan);
      } catch (err) {
        alert('Failed to add food to meal plan.');
      }
    }
  };

  if (loading) {
    return <div className="plan-editor-loading"><LoadingSpinner size="lg" /></div>;
  }

  if (error || !plan) {
    return <div className="plan-editor-error">{error || 'Plan not found.'}</div>;
  }

  const currentDay = plan.days.find(d => d.day_number === activeDay);

  return (
    <div className="plan-editor-container">
      <header className="plan-editor-header">
        <div>
          <button className="btn-back" onClick={() => navigate(`/clients/${plan.client_id}`)}>
            &larr; Back to Client
          </button>
          <h1 className="plan-title">{plan.title || 'Untitled Plan'}</h1>
          <div className="plan-meta">
            <span className={`status-badge status-${plan.status}`}>{plan.status.toUpperCase()}</span>
            <span className="date-badge">Starts: {plan.week_start_date}</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-secondary">AI Generate</button>
          {plan.status === 'draft' && (
            <button className="btn-primary" onClick={handleApprove}>Approve & Send</button>
          )}
        </div>
      </header>

      <div className="plan-totals">
        <div className="total-stat">
          <span className="stat-label">Avg Calories</span>
          <span className="stat-value">{plan.avg_daily_calories || 0} kcal</span>
        </div>
        <div className="total-stat">
          <span className="stat-label">Protein</span>
          <span className="stat-value">{plan.avg_daily_protein_g || 0}g</span>
        </div>
        <div className="total-stat">
          <span className="stat-label">Carbs</span>
          <span className="stat-value">{plan.avg_daily_carbs_g || 0}g</span>
        </div>
        <div className="total-stat">
          <span className="stat-label">Fat</span>
          <span className="stat-value">{plan.avg_daily_fat_g || 0}g</span>
        </div>
      </div>

      <div className="day-tabs">
        {[1, 2, 3, 4, 5, 6, 7].map(day => (
          <button 
            key={day}
            className={`day-tab ${activeDay === day ? 'active' : ''}`}
            onClick={() => setActiveDay(day)}
          >
            Day {day}
          </button>
        ))}
      </div>

      <div className="day-content">
        {currentDay ? (
          <div className="meal-slots">
            {MEAL_TYPES.map(mealType => {
              const items = currentDay.items.filter(item => item.meal_type === mealType);
              
              return (
                <div key={mealType} className="meal-slot">
                  <h3 className="meal-type-title">{mealType.replace('_', ' ').toUpperCase()}</h3>
                  
                  {items.length === 0 ? (
                    <div className="empty-meal">No items added</div>
                  ) : (
                    <div className="meal-items-list">
                      {items.map(item => (
                        <div key={item.id} className="meal-item-card">
                          <div className="meal-item-main">
                            <span className="food-name">{item.food_name}</span>
                            <span className="food-portion">{item.portion_description || `${item.portion_grams}g`}</span>
                          </div>
                          <div className="meal-item-macros">
                            <span>{item.calories} kcal</span>
                            <span>P: {item.protein_g}g</span>
                            <span>C: {item.carbs_g}g</span>
                            <span>F: {item.fat_g}g</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  <button className="btn-add-food" onClick={() => handleAddFoodClick(mealType)}>
                    + Add Food
                  </button>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="empty-day">
            <p>No day structure found.</p>
            <button className="btn-secondary">Initialize Day</button>
          </div>
        )}
      </div>

      <FoodSearchModal 
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelect={handleFoodSelect}
      />
    </div>
  );
};
