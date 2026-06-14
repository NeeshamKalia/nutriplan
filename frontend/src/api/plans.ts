import api from './index';
import { MealPlan } from '../types/plan';

export const plansApi = {
  getPlansByClient: async (clientId: string) => {
    const response = await api.get<{ items: MealPlan[]; total: number }>(`/clients/${clientId}/plans`);
    return response.data;
  },

  getPlan: async (planId: string) => {
    const response = await api.get<MealPlan>(`/plans/${planId}`);
    return response.data;
  },

  createPlan: async (clientId: string, data: Partial<MealPlan>) => {
    const response = await api.post<MealPlan>(`/clients/${clientId}/plans`, data);
    return response.data;
  },

  updatePlan: async (planId: string, data: Partial<MealPlan>) => {
    const response = await api.put<MealPlan>(`/plans/${planId}`, data);
    return response.data;
  },

  approvePlan: async (planId: string) => {
    const response = await api.post<MealPlan>(`/plans/${planId}/approve`);
    return response.data;
  },
};
