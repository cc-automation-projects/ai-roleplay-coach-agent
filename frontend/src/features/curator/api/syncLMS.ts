import apiClient from '@/shared/api/client';

export const syncLMS = async (planId: string): Promise<{ status: string; lms_course_id: string; lms_url: string }> => {
  const response = await apiClient.post('/api/v1/curator/sync-lms', {
    plan_id: planId,
  });
  return response.data;
};
