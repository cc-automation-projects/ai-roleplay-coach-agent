import apiClient from '@/shared/api/client';

export interface UserInfo {
  user_id: string;
  username: string;
  role: 'operator' | 'trainer' | 'admin';
  email: string;
  is_active: boolean;
  xp_total?: number;
  level?: number;
  created_at?: string;
}

export interface UsersResponse {
  items: UserInfo[];
  total: number;
  page: number;
  size: number;
}

export const getUsers = async (
  page: number = 1,
  size: number = 20
): Promise<UsersResponse> => {
  const response = await apiClient.get<UsersResponse>('/api/v1/auth/users', {
    params: { page, size },
  });
  return response.data;
};
