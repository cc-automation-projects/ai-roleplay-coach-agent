import apiClient from '@/shared/api/client';
import { LeaderboardEntry } from '@/entities/gamification/types';

interface LeaderboardResponse {
  items: LeaderboardEntry[];
  total: number;
  page: number;
  size: number;
}

export const getLeaderboard = async (
  page: number = 1,
  size: number = 20
): Promise<LeaderboardResponse> => {
  const response = await apiClient.get<LeaderboardResponse>('/api/v1/gamification/leaderboard', {
    params: { page, size },
  });
  return response.data;
};
