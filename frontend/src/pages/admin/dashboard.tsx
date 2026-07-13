import React from 'react';
import { UserTable } from '@/widgets/Admin/UserTable';
import { SystemHealth } from '@/widgets/Admin/SystemHealth';
import { LMSSyncButton } from '@/widgets/Admin/LMSSyncButton';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';

export const AdminDashboard: React.FC = () => {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Админ-панель</h1>
        <div className="text-sm text-muted-foreground">
          Управление системой и пользователями
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Левая колонка – управление пользователями */}
        <div className="lg:col-span-2">
          <UserTable />
        </div>

        {/* Правая колонка – системные виджеты */}
        <div className="space-y-6">
          <SystemHealth />
          <LMSSyncButton />
          
          {/* Дополнительный виджет: краткая информация о системе */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">О системе</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-1">
              <div>Версия фронтенда: v0.1.0</div>
              <div>Режим: {import.meta.env.DEV ? 'Разработка' : 'Production'}</div>
              <div>API: {import.meta.env.VITE_API_URL}</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
