import apiClient from '@/shared/api/client';
import { TokenPair } from '@/entities/user/types';

export const refresh = async (refreshToken: string): Promise<TokenPair> => {
  const response = await apiClient.post<TokenPair>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
};
