import api from './index';
import { FoodItem } from '../types/plan';

export const foodsApi = {
  searchFoods: async (params?: { q?: string; category?: string; is_vegetarian?: boolean }) => {
    const response = await api.get<{ items: FoodItem[]; total: number }>('/foods', { params });
    return response.data;
  },
};
