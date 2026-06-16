import api from './client';

export interface Protocol {
  id: string;
  dietitian_id: string;
  name: string;
  description?: string | null;
  target_conditions?: string[] | null;
  target_goals?: string[] | null;
  calorie_range_min?: number | null;
  calorie_range_max?: number | null;
  macro_split?: Record<string, number> | null;
  general_guidelines?: string | null;
  preferred_foods?: string[] | null;
  avoided_foods?: string[] | null;
  sample_plan?: Record<string, unknown> | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProtocolCreatePayload {
  name: string;
  description?: string;
  target_conditions?: string[];
  target_goals?: string[];
  calorie_range_min?: number;
  calorie_range_max?: number;
  general_guidelines?: string;
  preferred_foods?: string[];
  avoided_foods?: string[];
}

export const protocolsApi = {
  list: async (params?: { search?: string; active_only?: boolean }) => {
    const response = await api.get<{ protocols: Protocol[]; total: number }>(
      '/protocols',
      { params }
    );
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<Protocol>(`/protocols/${id}`);
    return response.data;
  },

  create: async (data: ProtocolCreatePayload) => {
    const response = await api.post<Protocol>('/protocols', data);
    return response.data;
  },

  update: async (id: string, data: Partial<ProtocolCreatePayload> & { is_active?: boolean }) => {
    const response = await api.put<Protocol>(`/protocols/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/protocols/${id}`);
  },

  savePlanAsProtocol: async (
    planId: string,
    data: { name: string; description?: string; general_guidelines?: string }
  ) => {
    const response = await api.post<Protocol>(`/plans/${planId}/save-as-protocol`, data);
    return response.data;
  },
};
