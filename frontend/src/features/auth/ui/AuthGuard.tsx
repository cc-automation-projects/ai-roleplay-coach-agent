import { useEffect, useRef, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuth } from '@/hooks/useAuth';
import type { UserRole } from '@/entities/user/types';

interface AuthGuardProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
  fallbackPath?: string;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  allowedRoles,
  fallbackPath = '/login',
}) => {
  const { isAuthenticated, user, isLoading, checkAuth } = useAuth();
  const [isChecking, setIsChecking] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const mounted = { current: true };

    const verify = async () => {
      const authenticated = await checkAuth();
      if (!mounted.current) return;
      setIsChecking(false);
      if (!authenticated) {
        await navigate({ to: fallbackPath });
        return;
      }
      if (allowedRoles && user && !allowedRoles.includes(user.role)) {
        await navigate({ to: '/' });
      }
    };
    verify();

    return () => {
      mounted.current = false;
    };
  }, [checkAuth, fallbackPath, navigate, allowedRoles, user]);

  if (isChecking || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
};
