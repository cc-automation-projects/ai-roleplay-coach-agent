import apiClient from '@/shared/api/client';
import { AuthResponse } from '@/entities/user/types';

export const login = async (username: string, password: string): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', {
    username,
    password,
  });
  return response.data;
};
