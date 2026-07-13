import apiClient from '@/shared/api/client';
import { Session } from '@/entities/session/types';

export const getSession = async (sessionId: string): Promise<Session> => {
  const response = await apiClient.get<Session>(`/api/v1/sessions/${sessionId}`);
  return response.data;
};
