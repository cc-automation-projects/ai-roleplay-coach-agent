import apiClient from '@/shared/api/client';

export const logout = async (refreshToken: string): Promise<void> => {
  await apiClient.post('/api/v1/auth/logout', {
    refresh_token: refreshToken,
  });
};
