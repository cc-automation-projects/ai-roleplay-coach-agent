import apiClient from '@/shared/api/client';

export interface ComponentHealth {
  name: string;
  status: 'ok' | 'degraded' | 'down';
  latency?: number;
  details?: Record<string, unknown>;
}

export interface SystemHealth {
  status: 'ok' | 'degraded' | 'down';
  components: ComponentHealth[];
  uptime_seconds: number;
  version: string;
}

export const getSystemHealth = async (): Promise<SystemHealth> => {
  const response = await apiClient.get<SystemHealth>('/ready');
  return response.data;
};
