import apiClient from '@/shared/api/client';
import { Badge } from '@/entities/gamification/types';

export const getAllBadges = async (): Promise<Badge[]> => {
  const response = await apiClient.get<Badge[]>('/api/v1/gamification/badges');
  return response.data;
};

export const getUserBadges = async (userId: string): Promise<Badge[]> => {
  const response = await apiClient.get<Badge[]>(`/api/v1/gamification/badges/${userId}`);
  return response.data;
};
