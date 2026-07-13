import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createTestToken } from '@/test/helpers';

// --- Mocks ---

// По умолчанию возвращаем resolved promise, чтобы .catch() не падал
const mockPost = vi.fn().mockResolvedValue(undefined);
const mockGet = vi.fn().mockResolvedValue(undefined);

vi.mock('@/shared/api/client', () => ({
  default: {
    post: (...args: unknown[]) => mockPost(...args),
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

import { authStore } from '@/store/authStore';

const TEST_USER = {
  user_id: 'user-1',
  username: 'testuser',
  role: 'trainer' as const,
  access_token: createTestToken({
    sub: 'user-1', username: 'testuser', role: 'trainer',
    exp: Math.floor(Date.now() / 1000) + 3600,
  }),
  refresh_token: 'refresh-token-1',
  token_type: 'bearer' as const,
};

const TEST_USER_INFO = {
  user_id: 'user-1',
  username: 'testuser',
  role: 'trainer' as const,
  email: 'test@example.com',
  is_active: true,
};

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    authStore.getState().logout();
  });

  describe('initial state', () => {
    it('has correct initial values', () => {
      const state = authStore.getState();
      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
    });
  });

  describe('setTokens', () => {
    it('sets tokens and marks authenticated', () => {
      authStore.getState().setTokens('access-123', 'refresh-456');
      const state = authStore.getState();
      expect(state.accessToken).toBe('access-123');
      expect(state.refreshToken).toBe('refresh-456');
      expect(state.isAuthenticated).toBe(true);
    });
  });

  describe('setUser', () => {
    it('sets user in state', () => {
      const user = {
        id: 'user-1',
        username: 'testuser',
        email: '',
        name: 'testuser',
        role: 'trainer' as const,
        xpTotal: 0,
        level: 1,
        isActive: true,
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      };
      authStore.getState().setUser(user);
      expect(authStore.getState().user).toEqual(user);
    });
  });

  describe('login', () => {
    it('calls API and updates state on success', async () => {
      mockPost.mockResolvedValueOnce({ data: TEST_USER });

      await authStore.getState().login('testuser', 'creds123');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/login', {
        username: 'testuser',
        password: expect.any(String),
      });

      const state = authStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.accessToken).toBe(TEST_USER.access_token);
      expect(state.refreshToken).toBe(TEST_USER.refresh_token);
      expect(state.user).not.toBeNull();
      expect(state.user?.id).toBe('user-1');
      expect(state.user?.username).toBe('testuser');
      expect(state.user?.role).toBe('trainer');
    });

    it('sets isLoading false and re-throws on API error', async () => {
      const apiError = new Error('Invalid credentials');
      mockPost.mockRejectedValueOnce(apiError);

      await expect(
        authStore.getState().login('bad', 'wrong')
      ).rejects.toThrow('Invalid credentials');
      expect(authStore.getState().isLoading).toBe(false);
    });
  });

  describe('register', () => {
    it('calls API and updates state on success', async () => {
      mockPost.mockResolvedValueOnce({ data: TEST_USER });

      await authStore.getState().register('newuser', 'secur3!');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/register', {
        username: 'newuser',
        password: expect.any(String),
      });

      const state = authStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.accessToken).toBe(TEST_USER.access_token);
      expect(state.user?.username).toBe('testuser');
    });

    it('sets isLoading false and re-throws on API error', async () => {
      mockPost.mockRejectedValueOnce(new Error('Username taken'));

      await expect(
        authStore.getState().register('taken', 'pwd')
      ).rejects.toThrow();
      expect(authStore.getState().isLoading).toBe(false);
    });
  });

  describe('refresh', () => {
    it('calls API and updates tokens', async () => {
      const newTokens = {
        access_token: 'new-access',
        refresh_token: 'new-refresh',
        token_type: 'bearer' as const,
      };
      mockPost.mockResolvedValueOnce({ data: newTokens });

      const result = await authStore.getState().refresh('old-refresh');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        refresh_token: 'old-refresh',
      });
      expect(result).toEqual(newTokens);

      const state = authStore.getState();
      expect(state.accessToken).toBe('new-access');
      expect(state.refreshToken).toBe('new-refresh');
    });

    it('clears auth on refresh failure', async () => {
      mockPost.mockResolvedValueOnce({ data: TEST_USER });
      await authStore.getState().login('testuser', 'pwd1');

      mockPost.mockRejectedValueOnce(new Error('Token invalid'));
      await expect(
        authStore.getState().refresh('bad-token')
      ).rejects.toThrow();

      const state = authStore.getState();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears all auth state', async () => {
      mockPost.mockResolvedValueOnce({ data: TEST_USER });
      await authStore.getState().login('testuser', 'pwd2');
      expect(authStore.getState().isAuthenticated).toBe(true);

      authStore.getState().logout();

      const state = authStore.getState();
      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('calls logout API when refresh token exists', () => {
      authStore.getState().setTokens('at', 'rt');
      authStore.getState().logout();

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/logout', {
        refresh_token: 'rt',
      });
    });

    it('does not call logout API when no refresh token', () => {
      authStore.getState().logout();
      expect(mockPost).not.toHaveBeenCalled();
    });
  });

  describe('getCurrentUser', () => {
    it('returns user and updates state on success', async () => {
      mockGet.mockResolvedValueOnce({ data: TEST_USER_INFO });

      const user = await authStore.getState().getCurrentUser();

      expect(mockGet).toHaveBeenCalledWith('/api/v1/auth/me');
      expect(user).not.toBeNull();
      expect(user?.id).toBe('user-1');
      expect(user?.email).toBe('test@example.com');
      expect(authStore.getState().user?.email).toBe('test@example.com');
    });

    it('returns null and does not throw on API error', async () => {
      mockGet.mockRejectedValueOnce(new Error('Network error'));

      const user = await authStore.getState().getCurrentUser();
      expect(user).toBeNull();
    });
  });

  describe('checkAuth', () => {
    it('returns false when no tokens', async () => {
      const result = await authStore.getState().checkAuth();
      expect(result).toBe(false);
      expect(authStore.getState().isAuthenticated).toBe(false);
    });

    it('returns true when tokens are valid and user loaded', async () => {
      authStore.getState().setTokens(
        createTestToken({
          sub: 'user-1', username: 'testuser', role: 'trainer',
          exp: Math.floor(Date.now() / 1000) + 3600,
        }),
        'rt'
      );
      mockGet.mockResolvedValueOnce({ data: TEST_USER_INFO });

      const result = await authStore.getState().checkAuth();
      expect(result).toBe(true);
      expect(authStore.getState().isAuthenticated).toBe(true);
      expect(authStore.getState().user?.id).toBe('user-1');
    });

    it('refreshes token when access token is expired', async () => {
      const expiredAccess = createTestToken({
        sub: 'user-1', username: 'testuser', role: 'trainer',
        exp: Math.floor(Date.now() / 1000) - 1000,
      });

      authStore.getState().setTokens(expiredAccess, 'rt-123');

      mockPost.mockResolvedValueOnce({
        data: {
          access_token: createTestToken({
            sub: 'user-1', username: 'testuser', role: 'trainer',
            exp: Math.floor(Date.now() / 1000) + 3600,
          }),
          refresh_token: 'new-rt',
          token_type: 'bearer',
        },
      });

      mockGet.mockResolvedValueOnce({ data: TEST_USER_INFO });

      const result = await authStore.getState().checkAuth();
      expect(result).toBe(true);
      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/auth/refresh',
        { refresh_token: 'rt-123' }
      );
      expect(authStore.getState().refreshToken).toBe('new-rt');
    });

    it('returns false when refresh fails', async () => {
      const expiredAccess = createTestToken({
        sub: 'user-1', username: 'testuser', role: 'trainer',
        exp: Math.floor(Date.now() / 1000) - 1000,
      });

      authStore.getState().setTokens(expiredAccess, 'rt-bad');

      mockPost.mockRejectedValueOnce(new Error('Refresh failed'));

      const result = await authStore.getState().checkAuth();
      expect(result).toBe(false);
      expect(authStore.getState().isAuthenticated).toBe(false);
      expect(authStore.getState().accessToken).toBeNull();
    });
  });

  describe('persist', () => {
    it('persists auth state to localStorage', async () => {
      mockPost.mockResolvedValueOnce({ data: TEST_USER });
      await authStore.getState().login('testuser', 'pwd3');

      const saved = JSON.parse(localStorage.getItem('auth-storage') || '{}');
      expect(saved.state.accessToken).toBe(TEST_USER.access_token);
      expect(saved.state.isAuthenticated).toBe(true);
      expect(saved.state.user?.id).toBe('user-1');
    });
  });
});
