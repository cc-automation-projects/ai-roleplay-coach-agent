import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getSystemHealth, resetCircuitBreaker } from '@/features/admin/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Skeleton } from '@/shared/ui/skeleton';
import { cn } from '@/shared/lib/utils';
import { toast } from 'react-hot-toast';
import { CheckCircle2, AlertCircle, XCircle, RefreshCw, Shield } from 'lucide-react';

const statusIconMap = {
  ok: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  degraded: <AlertCircle className="h-4 w-4 text-yellow-500" />,
  down: <XCircle className="h-4 w-4 text-red-500" />,
};

const statusLabelMap = {
  ok: 'Работает',
  degraded: 'Деградирует',
  down: 'Недоступен',
};

const statusBadgeVariantMap = {
  ok: 'default',
  degraded: 'warning',
  down: 'destructive',
} as const;

export const SystemHealth: React.FC = () => {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: getSystemHealth,
    refetchInterval: 60000, // Каждую минуту
    staleTime: 30000,
  });

  const handleResetCB = async (name?: string) => {
    try {
      const result = await resetCircuitBreaker(name);
      toast.success(`Circuit Breaker${name ? ` "${name}"` : ''} сброшен`);
      refetch();
    } catch {
      toast.error('Не удалось сбросить Circuit Breaker');
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Здоровье системы</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Здоровье системы</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Не удалось загрузить данные</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Повторить
          </Button>
        </CardContent>
      </Card>
    );
  }

  const overallStatus = data.status;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Здоровье системы
          <Badge variant={statusBadgeVariantMap[overallStatus]}>
            {statusLabelMap[overallStatus]}
          </Badge>
        </CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
          disabled={isRefetching}
          className="h-8 w-8 p-0"
        >
          <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-xs text-muted-foreground mb-2">
          Версия: {data.version} • Uptime: {Math.floor(data.uptime_seconds / 60)} мин
        </div>
        {data.components.map((comp) => (
          <div
            key={comp.name}
            className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
          >
            <div className="flex items-center gap-2">
              {statusIconMap[comp.status] || statusIconMap.down}
              <span className="text-sm font-medium">{comp.name}</span>
              {comp.latency !== undefined && (
                <span className="text-xs text-muted-foreground">
                  {comp.latency}ms
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={statusBadgeVariantMap[comp.status]} className="text-xs">
                {statusLabelMap[comp.status]}
              </Badge>
              {comp.name === 'Ollama Provider' && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => handleResetCB('llm-coach')}
                >
                  Сбросить CB
                </Button>
              )}
            </div>
          </div>
        ))}
        <Button
          variant="outline"
          size="sm"
          className="w-full mt-2 text-xs"
          onClick={() => handleResetCB()}
        >
          Сбросить все Circuit Breakers
        </Button>
      </CardContent>
    </Card>
  );
};
