import api from './client';

export interface DashboardStats {
  active_clients: number;
  plans_generated_this_month: number;
  pending_approvals: number;
}

export const dashboardApi = {
  getStats: async () => {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
};
