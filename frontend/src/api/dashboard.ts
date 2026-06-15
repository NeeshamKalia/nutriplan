import api from './client';

export interface AttentionClient {
  id: string;
  name: string;
  adherence_pct: number;
  last_interaction?: string | null;
}

export interface RecentActivity {
  type: string;
  client: string;
  timestamp: string;
  detail?: string | null;
}

export interface DashboardOverview {
  total_clients: number;
  active_clients: number;
  plans_this_month: number;
  pending_approvals: number;
  avg_adherence_pct: number;
  clients_needing_attention: AttentionClient[];
  recent_activity: RecentActivity[];
}

export interface DashboardStats {
  active_clients: number;
  plans_generated_this_month: number;
  pending_approvals: number;
}

export const dashboardApi = {
  getOverview: async () => {
    const response = await api.get<DashboardOverview>('/dashboard');
    return response.data;
  },
  getStats: async () => {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
};
