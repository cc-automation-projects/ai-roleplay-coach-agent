import apiClient from '@/shared/api/client';
import { AuthResponse } from '@/entities/user/types';

export const register = async (username: string, password: string): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', {
    username,
    password,
  });
  return response.data;
};
