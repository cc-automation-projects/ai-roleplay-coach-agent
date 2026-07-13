import apiClient from '@/shared/api/client';
import { MicroQuiz } from '@/entities/curator/types';

export const generateQuiz = async (
  scenarioId: string,
  questionCount: number = 5
): Promise<MicroQuiz> => {
  const response = await apiClient.post<MicroQuiz>('/api/v1/curator/quiz', {
    scenario_id: scenarioId,
    question_count: questionCount,
  });
  return response.data;
};
