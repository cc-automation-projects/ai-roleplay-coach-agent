import apiClient from '@/shared/api/client';

export const resetCircuitBreaker = async (name?: string): Promise<{ status: string }> => {
  const url = name
    ? `/api/v1/admin/circuit-breaker/reset?name=${encodeURIComponent(name)}`
    : '/api/v1/admin/circuit-breaker/reset';
  const response = await apiClient.post<{ status: string }>(url);
  return response.data;
};
