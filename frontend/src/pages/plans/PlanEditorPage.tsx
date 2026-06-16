import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { plansApi } from '../../api/plans';
import { protocolsApi } from '../../api/protocols';
import type { MealPlan, FoodItem, MealPlanItem } from '../../types/plan';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { FoodSearchModal } from '../../components/plans/FoodSearchModal';
import { AIGenerateModal, type ProtocolOption } from '../../components/plans/AIGenerateModal';

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
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isSavingProtocol, setIsSavingProtocol] = useState(false);
  const [protocolOptions, setProtocolOptions] = useState<ProtocolOption[]>([]);

  useEffect(() => {
    loadPlan();
  }, [id]);

  useEffect(() => {
    protocolsApi.list().then((data) => {
      setProtocolOptions(data.protocols.map((p) => ({ id: p.id, name: p.name })));
    }).catch(() => setProtocolOptions([]));
  }, []);

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
    
    if (!window.confirm('Are you sure you want to approve and send this plan to the client?')) {
      return;
    }

    try {
      setIsApproving(true);
      await plansApi.approvePlan(plan.id);
      await loadPlan(); // Reload to get updated status
      alert('Plan approved and sent successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve plan.');
    } finally {
      setIsApproving(false);
    }
  };

  const handleAddFoodClick = (mealType: string) => {
    setSelectedMealType(mealType);
    setIsSearchOpen(true);
  };

  const handleGeneratePlan = async (instructions: string, protocolId?: string) => {
    if (!plan) return;
    try {
      setIsGenerating(true);
      const hasContent = plan.days.some((d) => d.items.length > 0);
      const payload = {
        custom_instructions: instructions || undefined,
        protocol_id: protocolId,
      };

      const updatedPlan = hasContent
        ? await plansApi.regeneratePlan(plan.id, payload)
        : await plansApi.generatePlan(plan.client_id, {
            week_start_date: plan.week_start_date,
            ...payload,
          });

      setIsGenerating(false);
      setIsAIModalOpen(false);
      if (hasContent) {
        setPlan(updatedPlan);
      } else {
        navigate(`/plans/${updatedPlan.id}`, { replace: true });
      }
    } catch (err) {
      console.error(err);
      alert('Failed to regenerate plan.');
      setIsGenerating(false);
    }
  };

  const handleSaveAsProtocol = async () => {
    if (!plan) return;
    const name = window.prompt('Protocol name:', plan.title || 'My Protocol');
    if (!name?.trim()) return;

    try {
      setIsSavingProtocol(true);
      await protocolsApi.savePlanAsProtocol(plan.id, { name: name.trim() });
      const data = await protocolsApi.list();
      setProtocolOptions(data.protocols.map((p) => ({ id: p.id, name: p.name })));
      alert('Protocol saved. You can reuse it when generating plans.');
    } catch (err) {
      console.error(err);
      alert('Failed to save protocol.');
    } finally {
      setIsSavingProtocol(false);
    }
  };

  const handleFoodSelect = async (food: FoodItem) => {
    setIsSearchOpen(false);
    if (!plan || !currentDay || !selectedMealType) return;
    
    // In a real app, we would make an API call here to add the item
    // For now, we update local state to reflect UI changes
    const multiplier = (food.default_serving_grams || 100) / 100;
    
    const newItem: MealPlanItem = {
      id: Math.random().toString(),
      meal_plan_day_id: currentDay.id,
      meal_type: selectedMealType as any,
      sort_order: 0,
      food_name: food.name,
      food_name_hindi: food.name_hindi,
      portion_description: food.default_serving_description,
      portion_grams: food.default_serving_grams,
      calories: Math.round(food.calories_per_100g * multiplier),
      protein_g: Number((food.protein_per_100g * multiplier).toFixed(1)),
      carbs_g: Number((food.carbs_per_100g * multiplier).toFixed(1)),
      fat_g: Number((food.fat_per_100g * multiplier).toFixed(1)),
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

  const handleDeleteItem = async (dayId: string, itemId: string) => {
    if (!plan) return;
    
    const updatedPlan = { ...plan };
    const dayIndex = updatedPlan.days.findIndex(d => d.id === dayId);
    if (dayIndex >= 0) {
      updatedPlan.days[dayIndex].items = updatedPlan.days[dayIndex].items.filter(item => item.id !== itemId);
      
      try {
        await plansApi.updatePlan(plan.id, { days: updatedPlan.days });
        setPlan(updatedPlan);
      } catch (err) {
        alert('Failed to delete item from meal plan.');
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
          <button
            className="btn-secondary"
            onClick={handleSaveAsProtocol}
            disabled={isSavingProtocol || plan.days.every((d) => d.items.length === 0)}
          >
            {isSavingProtocol ? 'Saving...' : 'Save as Protocol'}
          </button>
          <button className="btn-secondary" onClick={() => setIsAIModalOpen(true)}>
            {plan.status === 'draft' && plan.days.some(d => d.items.length > 0) ? 'Regenerate with AI' : 'AI Generate'}
          </button>
          {plan.status === 'draft' && (
            <button className="btn-primary" onClick={handleApprove} disabled={isApproving}>
              {isApproving ? 'Approving...' : 'Approve & Send'}
            </button>
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

      {plan.validations && plan.validations.length > 0 && (
        <div className="plan-validations" style={{ 
          marginTop: '1rem', 
          padding: '1rem', 
          backgroundColor: 'var(--surface-subtle)', 
          borderRadius: '8px',
          border: '1px solid var(--border-color)'
        }}>
          <h3 className="text-sm font-semibold mb-2 text-muted">AI Validations</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {plan.validations.map(val => (
              <div key={val.id} style={{ 
                display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
                color: val.passed ? 'var(--color-success-600)' : 'var(--color-danger-600)'
              }}>
                <span>{val.passed ? '✅' : '❌'}</span>
                <div>
                  <div className="font-medium text-sm">{val.validation_type.replace('_', ' ').toUpperCase()}</div>
                  {val.message && <div className="text-xs text-muted">{val.message}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="day-tabs" style={{ marginTop: '2rem' }}>
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
                        <div key={item.id} className="meal-item-card" style={{ position: 'relative' }}>
                          <button 
                            onClick={() => handleDeleteItem(currentDay.id, item.id)}
                            style={{ 
                              position: 'absolute', top: '8px', right: '8px', 
                              background: 'transparent', border: 'none', color: 'var(--color-danger-600)', 
                              cursor: 'pointer', padding: '4px' 
                            }}
                            title="Remove item"
                          >
                            ✕
                          </button>
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
      
      <AIGenerateModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        onGenerate={handleGeneratePlan}
        isLoading={isGenerating}
        protocols={protocolOptions}
      />
    </div>
  );
};
