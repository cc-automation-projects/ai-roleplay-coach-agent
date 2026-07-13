import { createRouter, Route, RouterProvider } from '@tanstack/react-router';
import { RootLayout } from '@/widgets/layout/RootLayout';
import { AuthGuard } from '@/features/auth/ui/AuthGuard';

// Страницы
import { LoginPage } from '@/pages/login';
import { RegisterPage } from '@/pages/register';
import { OperatorDashboard } from '@/pages/operator/dashboard';
import { TrainerDashboard } from '@/pages/trainer/dashboard';
import { AdminDashboard } from '@/pages/admin/dashboard';

// Роуты
const rootRoute = new Route({
  getParentRoute: () => undefined,
  id: 'root',
  component: RootLayout,
});

const loginRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
});

const registerRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/register',
  component: RegisterPage,
});

// Операторские маршруты
const operatorRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/operator',
  component: () => (
    <AuthGuard allowedRoles={['operator', 'trainer', 'admin']}>
      <OperatorDashboard />
    </AuthGuard>
  ),
});

// Тренерские маршруты
const trainerRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/trainer',
  component: () => (
    <AuthGuard allowedRoles={['trainer', 'admin']}>
      <TrainerDashboard />
    </AuthGuard>
  ),
});

// Админские маршруты
const adminRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/admin',
  component: () => (
    <AuthGuard allowedRoles={['admin']}>
      <AdminDashboard />
    </AuthGuard>
  ),
});

// Главный редирект
const indexRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => {
    const { user } = useAuth();
    if (user?.role === 'admin') {
      return <AdminDashboard />;
    }
    if (user?.role === 'trainer') {
      return <TrainerDashboard />;
    }
    return <OperatorDashboard />;
  },
});

// Сборка роутера
const routeTree = rootRoute.addChildren([
  loginRoute,
  registerRoute,
  operatorRoute,
  trainerRoute,
  adminRoute,
  indexRoute,
]);

export const router = createRouter({ routeTree });

// Объявляем типы для хуков
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
