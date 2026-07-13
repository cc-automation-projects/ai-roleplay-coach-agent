import { vi } from 'vitest';

// API-клиент в проекте не сгенерирован (orval не запущен),
// поэтому создаём заглушку, которая используется в authStore.
// В тестах мы мокаем всё через vi.mock('@/shared/api/client').

export const mockApiClient = {
  post: vi.fn(),
  get: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
};

export default mockApiClient;
