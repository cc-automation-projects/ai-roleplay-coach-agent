import apiClient from '@/shared/api/client';

export const getStreak = async (userId: string): Promise<{ user_id: string; streak: number }> => {
  const response = await apiClient.get<{ user_id: string; streak: number }>(
    `/api/v1/gamification/streak/${userId}`
  );
  return response.data;
};
