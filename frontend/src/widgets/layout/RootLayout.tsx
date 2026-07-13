import React from 'react';
import { Outlet } from '@tanstack/react-router';

export const RootLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-background">
      <Outlet />
    </div>
  );
};
