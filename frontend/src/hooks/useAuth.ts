import { useStore } from 'zustand';
import { authStore } from '@/store/authStore';

export const useAuth = () => {
  const state = useStore(authStore);
  return {
    ...state,
    // Оборачиваем действия, чтобы не терять контекст
    login: state.login,
    register: state.register,
    logout: state.logout,
    refresh: state.refresh,
    checkAuth: state.checkAuth,
  };
};
