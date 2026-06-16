import api from './client';
import type { MealPlan } from '../types/plan';

export const plansApi = {
  getPlansByClient: async (clientId: string) => {
    const response = await api.get<{ plans: MealPlan[]; total: number }>(`/clients/${clientId}/plans`);
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

  generatePlan: async (
    clientId: string,
    data: { week_start_date: string; custom_instructions?: string; protocol_id?: string }
  ) => {
    const response = await api.post<MealPlan>(`/clients/${clientId}/plans/generate`, data);
    return response.data;
  },

  regeneratePlan: async (
    planId: string,
    data: { custom_instructions?: string; week_start_date?: string; protocol_id?: string }
  ) => {
    const response = await api.post<MealPlan>(`/plans/${planId}/regenerate`, data);
    return response.data;
  },
};
