import React from 'react';
import { RegisterForm } from '@/features/auth/ui/RegisterForm';

export const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <RegisterForm />
    </div>
  );
};
