import { describe, it, expect } from 'vitest';
import { decodeToken, isTokenExpired, getAuthHeaders } from '@/shared/lib/auth';
import { createTestToken, validToken, expiredToken, invalidToken } from '@/test/helpers';

describe('decodeToken', () => {
  it('returns payload for a valid token', () => {
    const result = decodeToken(validToken);
    expect(result).not.toBeNull();
    expect(result?.sub).toBe('user-1');
    expect(result?.username).toBe('testuser');
    expect(result?.role).toBe('trainer');
    expect(result?.exp).toBeGreaterThan(0);
  });

  it('returns null for an invalid token string', () => {
    const result = decodeToken(invalidToken);
    expect(result).toBeNull();
  });

  it('returns null for empty string', () => {
    const result = decodeToken('');
    expect(result).toBeNull();
  });

  it('returns null for malformed JSON in payload', () => {
    const header = btoa(JSON.stringify({ alg: 'HS256' }));
    const body = btoa('not-json');
    const token = `${header}.${body}.sig`;
    const result = decodeToken(token);
    expect(result).toBeNull();
  });
});

describe('isTokenExpired', () => {
  it('returns true for an expired token', () => {
    expect(isTokenExpired(expiredToken)).toBe(true);
  });

  it('returns false for a valid (unexpired) token', () => {
    expect(isTokenExpired(validToken)).toBe(false);
  });

  it('returns true for an invalid token (falls back to decodeToken → null)', () => {
    expect(isTokenExpired(invalidToken)).toBe(true);
  });

  it('returns true for empty string', () => {
    expect(isTokenExpired('')).toBe(true);
  });
});

describe('getAuthHeaders', () => {
  it('returns Bearer authorization header', () => {
    const result = getAuthHeaders('my-test-token');
    expect(result).toEqual({ Authorization: 'Bearer my-test-token' });
  });
});
