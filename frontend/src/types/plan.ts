export interface MealPlanItem {
  id: string;
  meal_plan_day_id: string;
  meal_type: 'breakfast' | 'mid_morning' | 'lunch' | 'evening_snack' | 'dinner' | 'bedtime';
  sort_order: number;
  food_name: string;
  food_name_hindi?: string;
  portion_description?: string;
  portion_grams?: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
  food_item_id?: string;
  preparation_notes?: string;
}

export interface MealPlanDay {
  id: string;
  meal_plan_id: string;
  day_number: number;
  day_label?: string;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  total_fiber_g?: number;
  items: MealPlanItem[];
}

export interface MealPlan {
  id: string;
  client_id: string;
  title: string;
  week_start_date: string;
  status: 'draft' | 'approved' | 'delivered' | 'expired';
  custom_instructions?: string;
  avg_daily_calories: number;
  avg_daily_protein_g: number;
  avg_daily_carbs_g: number;
  avg_daily_fat_g: number;
  avg_daily_fiber_g?: number;
  days: MealPlanDay[];
  validations?: MealPlanValidation[];
  created_at: string;
  updated_at: string;
}

export interface MealPlanValidation {
  id: string;
  validation_type: string;
  passed: boolean;
  severity?: 'warning' | 'error' | 'info' | string;
  message?: string;
}

export interface FoodItem {
  id: string;
  name: string;
  name_hindi?: string;
  category: string;
  subcategory?: string;
  calories_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  fiber_per_100g?: number;
  default_serving_description?: string;
  default_serving_grams?: number;
  is_vegetarian: boolean;
  is_vegan: boolean;
  is_gluten_free: boolean;
  common_allergens: string[];
}
