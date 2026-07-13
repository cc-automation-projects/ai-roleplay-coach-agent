import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuthGuard } from '@/features/auth/ui/AuthGuard';

// --- Mocks ---

const mockNavigate = vi.fn();

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

// Состояние useAuth будет подменяться в каждом тесте
let mockAuthState = {
  isAuthenticated: false,
  user: null,
  isLoading: false,
  checkAuth: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refresh: vi.fn(),
};

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => mockAuthState,
}));

describe('AuthGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Сброс состояния по умолчанию
    mockAuthState = {
      isAuthenticated: false,
      user: null,
      isLoading: false,
      checkAuth: vi.fn().mockResolvedValue(false),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    };
  });

  it('shows loading spinner when checking auth', () => {
    mockAuthState.isLoading = true;

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    );

    // Ищем спиннер (по классу animate-spin)
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();

    // Контент не должен быть показан
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('shows spinner while isChecking is true', () => {
    // checkAuth не резолвится сразу = isChecking остаётся true
    mockAuthState.checkAuth = vi.fn().mockReturnValue(new Promise(() => {}));

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    );

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('redirects to fallback path when not authenticated', async () => {
    mockAuthState.checkAuth = vi.fn().mockResolvedValue(false);

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    );

    // Ждём эффект (checkAuth асинхронный)
    await vi.waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith({ to: '/login' });
    });
  });

  it('redirects to custom fallbackPath when specified', async () => {
    mockAuthState.checkAuth = vi.fn().mockResolvedValue(false);

    render(
      <AuthGuard fallbackPath="/custom-login">
        <div>Protected</div>
      </AuthGuard>
    );

    await vi.waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith({ to: '/custom-login' });
    });
  });

  it('redirects to home when role not allowed', async () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = {
      id: 'uid-1',
      username: 'opuser',
      role: 'operator',
      email: '',
      name: 'opuser',
      xpTotal: 0,
      level: 1,
      isActive: true,
      createdAt: '',
      updatedAt: '',
    };
    mockAuthState.checkAuth = vi.fn().mockResolvedValue(true);

    render(
      <AuthGuard allowedRoles={['trainer', 'admin']}>
        <div>Admin Only</div>
      </AuthGuard>
    );

    await vi.waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith({ to: '/' });
    });
  });

  it('renders children when authenticated and authorized', async () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = {
      id: 'uid-2',
      username: 'trainer1',
      role: 'trainer',
      email: '',
      name: 'trainer1',
      xpTotal: 0,
      level: 1,
      isActive: true,
      createdAt: '',
      updatedAt: '',
    };
    mockAuthState.checkAuth = vi.fn().mockResolvedValue(true);

    render(
      <AuthGuard allowedRoles={['trainer', 'admin']}>
        <div>Training Dashboard</div>
      </AuthGuard>
    );

    await vi.waitFor(() => {
      expect(screen.getByText('Training Dashboard')).toBeInTheDocument();
    });

    // Не перенаправляет
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('renders children when no role restrictions', async () => {
    mockAuthState.isAuthenticated = true;
    mockAuthState.user = {
      id: 'uid-1',
      username: 'opuser',
      role: 'operator',
      email: '',
      name: 'opuser',
      xpTotal: 0,
      level: 1,
      isActive: true,
      createdAt: '',
      updatedAt: '',
    };
    mockAuthState.checkAuth = vi.fn().mockResolvedValue(true);

    render(
      <AuthGuard>
        <div>Any User Content</div>
      </AuthGuard>
    );

    await vi.waitFor(() => {
      expect(screen.getByText('Any User Content')).toBeInTheDocument();
    });
  });
});
