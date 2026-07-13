import apiClient from '@/shared/api/client';
import { Session } from '@/entities/session/types';

export const createSession = async (scenarioId: string): Promise<Session> => {
  const response = await apiClient.post<Session>('/api/v1/sessions', {
    scenario_id: scenarioId,
  });
  return response.data;
};
