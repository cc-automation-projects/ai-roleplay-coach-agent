import apiClient from '@/shared/api/client';
import { Evaluation } from '@/entities/evaluation/types';

export const evaluateSession = async (sessionId: string): Promise<Evaluation> => {
  const response = await apiClient.post<Evaluation>(`/api/v1/sessions/${sessionId}/evaluate`);
  return response.data;
};
