import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/entities/user/types';
import type { AuthResponse, UserInfo, TokenPair } from '@/entities/user/types';
import apiClient from '@/shared/api/client';
import { isTokenExpired } from '@/shared/lib/auth';


/** Map AuthResponse to User (login/register both use same shape). */
function fromAuthResponse(data: AuthResponse): User {
  return {
    id: data.user_id,
    username: data.username,
    email: '',
    name: data.username,
    role: data.role,
    xpTotal: 0,
    level: 1,
    isActive: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

/** Map UserInfo (GET /me) to User. */
function fromUserInfo(data: UserInfo): User {
  return {
    id: data.user_id,
    username: data.username,
    email: data.email,
    name: data.username,
    role: data.role,
    xpTotal: 0,
    level: 1,
    isActive: data.is_active,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  refresh: (refreshToken: string) => Promise<TokenPair>;
  logout: () => void;
  getCurrentUser: () => Promise<User | null>;
  checkAuth: () => Promise<boolean>;
}

export const authStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      setTokens: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken, isAuthenticated: true });
      },

      setUser: (user) => set({ user }),

      login: async (username, password) => {
        set({ isLoading: true });
        try {
          const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', {
            username,
            password,
          });
          const data = response.data;
          set({
            user: fromAuthResponse(data),
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (username, password) => {
        set({ isLoading: true });
        try {
          const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', {
            username,
            password,
          });
          const data = response.data;
          set({
            user: fromAuthResponse(data),
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      refresh: async (refreshToken) => {
        try {
          const response = await apiClient.post<TokenPair>('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = response.data;
          set({ accessToken: access_token, refreshToken: refresh_token });
          return response.data;
        } catch (error) {
          set({ accessToken: null, refreshToken: null, isAuthenticated: false });
          throw error;
        }
      },

      logout: () => {
        // Вызываем logout на бэкенде, если есть refresh токен
        const { refreshToken } = get();
        if (refreshToken) {
          apiClient
            .post('/api/v1/auth/logout', { refresh_token: refreshToken })
            .catch(() => {});
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      getCurrentUser: async () => {
        try {
          const response = await apiClient.get<UserInfo>('/api/v1/auth/me');
          const user = fromUserInfo(response.data);
          set({ user });
          return user;
        } catch {
          return null;
        }
      },

      checkAuth: async () => {
        const { accessToken, refreshToken, getCurrentUser } = get();
        if (!accessToken || !refreshToken) {
          set({ isAuthenticated: false });
          return false;
        }

        // Проверяем, не истёк ли access токен
        if (isTokenExpired(accessToken)) {
          try {
            // Пытаемся обновить через refresh
            const tokens = await get().refresh(refreshToken);
            // Токены обновлены, получаем пользователя
            const user = await getCurrentUser();
            if (user) {
              set({ isAuthenticated: true, user });
              return true;
            }
          } catch {
            // Рефреш не удался – разлогиниваем
            set({ isAuthenticated: false, user: null, accessToken: null, refreshToken: null });
            return false;
          }
        }

        // Если токен валиден, но пользователь ещё не загружен – загружаем
        if (!get().user) {
          const user = await getCurrentUser();
          if (user) {
            set({ isAuthenticated: true, user });
            return true;
          }
        }

        return get().isAuthenticated;
      },
    }),
    {
      name: 'auth-storage', // имя ключа в localStorage
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
