import apiClient from '@/shared/api/client';
import { Session } from '@/entities/session/types';

export const sendTurn = async (sessionId: string, userId: string, message: string): Promise<Session> => {
  const response = await apiClient.post<Session>(`/api/v1/sessions/${sessionId}/turns`, {
    user_id: userId,
    message,
  });
  return response.data;
};
