import api from './client';

export interface MealTypeStats {
  meal_type: string;
  completed: number;
  skipped: number;
  deviated: number;
}

export interface DailyAdherence {
  date: string;
  completed: number;
  skipped: number;
  deviated: number;
  adherence_pct: number;
}

export interface RecentMealLog {
  log_date: string;
  meal_type: string;
  status: string;
  deviation_note?: string | null;
  logged_at?: string | null;
}

export interface ClientAdherence {
  client_id: string;
  period_days: number;
  total_completed: number;
  total_skipped: number;
  total_deviated: number;
  adherence_pct: number;
  daily: DailyAdherence[];
  by_meal_type: MealTypeStats[];
  recent_logs: RecentMealLog[];
}

export const adherenceApi = {
  getClientAdherence: async (clientId: string, days = 7) => {
    const response = await api.get<ClientAdherence>(`/clients/${clientId}/adherence`, {
      params: { days },
    });
    return response.data;
  },
};
