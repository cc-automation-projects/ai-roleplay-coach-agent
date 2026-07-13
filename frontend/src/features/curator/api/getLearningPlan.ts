import apiClient from '@/shared/api/client';
import { LearningPlan } from '@/entities/curator/types';

export const getLearningPlan = async (scenarioId: string): Promise<LearningPlan> => {
  const response = await apiClient.post<LearningPlan>('/api/v1/curator/learning-plan', {
    scenario_id: scenarioId,
  });
  return response.data;
};
