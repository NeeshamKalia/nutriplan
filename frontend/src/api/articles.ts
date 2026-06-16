import api from './client';

export interface Article {
  id: string;
  dietitian_id: string;
  title: string;
  slug: string;
  summary: string | null;
  content: string;
  cover_image_url: string | null;
  tags: string[] | null;
  status: string;
  meta_title: string | null;
  meta_description: string | null;
  published_at: string | null;
  broadcasted_at: string | null;
  broadcast_count: number;
  created_at: string;
  updated_at: string;
}

export interface ArticleBroadcastResult {
  article: Article;
  sent_count: number;
  failed_count: number;
  skipped_count: number;
  total_active_clients: number;
}

export interface ArticleListResponse {
  articles: Article[];
  total: number;
}

export interface ArticleCreatePayload {
  title: string;
  slug?: string;
  summary?: string;
  content: string;
  cover_image_url?: string;
  tags?: string[];
  status?: string;
  meta_title?: string;
  meta_description?: string;
}

export interface ArticleUpdatePayload {
  title?: string;
  slug?: string;
  summary?: string;
  content?: string;
  cover_image_url?: string;
  tags?: string[];
  status?: string;
  meta_title?: string;
  meta_description?: string;
}

export interface IntakePayload {
  full_name: string;
  whatsapp_number: string;
  email?: string;
  age?: number;
  primary_goal?: string;
  dietary_type?: string;
  notes?: string;
}

export interface IntakeResponse {
  message: string;
  client_id: string;
}

export interface DietitianPublicProfile {
  id: string;
  full_name: string;
  slug: string;
  bio: string | null;
  photo_url: string | null;
  specializations: string[] | null;
  qualifications: string | null;
  practice_name: string | null;
  phone: string | null;
}

export const articlesApi = {
  list: async (params?: { status?: string; search?: string }) => {
    const response = await api.get<ArticleListResponse>('/articles', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<Article>(`/articles/${id}`);
    return response.data;
  },

  create: async (data: ArticleCreatePayload) => {
    const response = await api.post<Article>('/articles', data);
    return response.data;
  },

  update: async (id: string, data: ArticleUpdatePayload) => {
    const response = await api.put<Article>(`/articles/${id}`, data);
    return response.data;
  },

  publish: async (id: string) => {
    const response = await api.post<Article>(`/articles/${id}/publish`);
    return response.data;
  },

  unpublish: async (id: string) => {
    const response = await api.post<Article>(`/articles/${id}/unpublish`);
    return response.data;
  },

  broadcast: async (id: string) => {
    const response = await api.post<ArticleBroadcastResult>(`/articles/${id}/broadcast`);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/articles/${id}`);
  },
};

export const publicApi = {
  getDietitian: async (slug: string) => {
    const response = await api.get<DietitianPublicProfile>(`/public/dietitians/${slug}`);
    return response.data;
  },

  getArticles: async (dietitianSlug: string) => {
    const response = await api.get<Article[]>(`/public/dietitians/${dietitianSlug}/articles`);
    return response.data;
  },

  getArticle: async (dietitianSlug: string, articleSlug: string) => {
    const response = await api.get<Article>(
      `/public/dietitians/${dietitianSlug}/articles/${articleSlug}`
    );
    return response.data;
  },

  submitIntake: async (slug: string, data: IntakePayload) => {
    const response = await api.post<IntakeResponse>(
      `/public/dietitians/${slug}/intake`,
      data
    );
    return response.data;
  },
};
