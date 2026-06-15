import api from './client';

export interface ProgressLog {
  id: string;
  client_id: string;
  log_date: string;
  weight_kg?: number;
  waist_cm?: number;
  hip_cm?: number;
  chest_cm?: number;
  notes?: string;
  logged_via: string;
  created_at: string;
}

export interface ProgressLogCreate {
  log_date: string;
  weight_kg?: number;
  waist_cm?: number;
  hip_cm?: number;
  chest_cm?: number;
  notes?: string;
}

export const progressApi = {
  getLogs: (clientId: string) => api.get<ProgressLog[]>(`/clients/${clientId}/progress`).then(res => res.data),
  logProgress: (clientId: string, data: ProgressLogCreate) => api.post<ProgressLog>(`/clients/${clientId}/progress`, data).then(res => res.data),
  updateLog: (clientId: string, logId: string, data: Partial<ProgressLogCreate>) => api.put<ProgressLog>(`/clients/${clientId}/progress/${logId}`, data).then(res => res.data),
  deleteLog: (clientId: string, logId: string) => api.delete(`/clients/${clientId}/progress/${logId}`).then(res => res.data),
};
