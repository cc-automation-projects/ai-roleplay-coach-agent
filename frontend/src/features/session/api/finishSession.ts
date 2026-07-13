import apiClient from '@/shared/api/client';
import { Session } from '@/entities/session/types';

export const finishSession = async (sessionId: string): Promise<Session> => {
  const response = await apiClient.post<Session>(`/api/v1/sessions/${sessionId}/finish`);
  return response.data;
};
