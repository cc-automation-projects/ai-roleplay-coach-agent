import apiClient from '@/shared/api/client';
import { GamificationStats } from '@/entities/gamification/types';

export const getXPStats = async (userId: string): Promise<GamificationStats> => {
  const response = await apiClient.get<GamificationStats>(`/api/v1/gamification/xp/${userId}`);
  return response.data;
};
