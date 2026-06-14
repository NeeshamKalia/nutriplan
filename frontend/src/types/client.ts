export interface Client {
  id: string;
  full_name: string;
  whatsapp_number: string;
  email: string | null;
  age: number | null;
  gender: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  target_weight_kg: number | null;
  activity_level: string | null;
  medical_conditions: string[] | null;
  allergies: string[] | null;
  food_preferences: string[] | null;
  cuisine_preference: string | null;
  dietary_type: string | null;
  primary_goal: string | null;
  monthly_food_budget_inr: number | null;
  daily_calorie_target: number | null;
  meals_per_day: number | null;
  notes: string | null;
  lifestyle_notes: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
  archived_at: string | null;
  onboarded_at: string | null;
}

export interface ClientListResponse {
  clients: Client[];
  total: number;
}
