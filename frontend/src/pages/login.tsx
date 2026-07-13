import React from 'react';
import { LoginForm } from '@/features/auth/ui/LoginForm';

export const LoginPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <LoginForm />
    </div>
  );
};
