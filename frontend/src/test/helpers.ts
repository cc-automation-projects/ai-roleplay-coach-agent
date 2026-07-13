import { vi } from 'vitest';

/**
 * Создаёт JWT-подобный токен с заданным payload.
 * Настоящей подписи нет — это НЕ валидный JWT, но jwtDecode
 * парсит только payload (вторую часть), так что для тестов годится.
 */
export function createTestToken(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.fake-signature`;
}

/** Токен с истёкшим сроком (exp в прошлом). */
export const expiredToken = createTestToken({
  sub: 'user-1',
  username: 'testuser',
  role: 'trainer',
  exp: Math.floor(Date.now() / 1000) - 3600, // час назад
});

/** Токен с действующим сроком (exp в будущем). */
export const validToken = createTestToken({
  sub: 'user-1',
  username: 'testuser',
  role: 'trainer',
  exp: Math.floor(Date.now() / 1000) + 3600, // через час
});

/** Абсолютно невалидный токен. */
export const invalidToken = 'not-a-jwt-token';
