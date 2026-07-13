import apiClient from '@/shared/api/client';
import { XPTransaction } from '@/entities/gamification/types';

interface XPHistoryResponse {
  items: XPTransaction[];
  total: number;
  page: number;
  size: number;
}

export const getXPHistory = async (
  userId: string,
  page: number = 1,
  size: number = 20
): Promise<XPHistoryResponse> => {
  const response = await apiClient.get<XPHistoryResponse>(
    `/api/v1/gamification/xp/${userId}/history`,
    { params: { page, size } }
  );
  return response.data;
};
