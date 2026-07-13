import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getFairnessReport } from '@/features/fairness/api/getFairnessReport';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Skeleton } from '@/shared/ui/skeleton';
import { cn } from '@/shared/lib/utils';
import { toast } from 'react-hot-toast';

const statusColorMap = {
  ok: 'text-green-600 bg-green-50 border-green-200',
  warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  alert: 'text-red-600 bg-red-50 border-red-200',
};

const statusLabelMap = {
  ok: '✅ В норме',
  warning: '⚠️ Требует внимания',
  alert: '🚨 Требует аудита',
};

export const FairnessDashboard: React.FC = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['fairness'],
    queryFn: getFairnessReport,
    staleTime: 1000 * 60 * 60, // 1 час
  });

  const handleRefresh = () => {
    refetch();
    toast.success('Данные обновлены');
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 text-center">
        <p className="text-muted-foreground">Нет данных для отображения</p>
        <Button className="mt-4" onClick={handleRefresh}>
          Обновить
        </Button>
      </div>
    );
  }

  const alertCount = data.metrics.filter((m) => m.status === 'alert').length;
  const warningCount = data.metrics.filter((m) => m.status === 'warning').length;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Fairness-аудит</h1>
        <div className="flex items-center gap-3">
          <Badge variant={data.summary.status === 'ok' ? 'default' : 'destructive'}>
            {data.summary.status === 'ok' ? '✅ OK' : '⚠️ Внимание'}
          </Badge>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Обновить
          </Button>
        </div>
      </div>

      {/* Сводка */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Всего метрик
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{data.metrics.length}</p>
          </CardContent>
        </Card>
        <Card className="border-yellow-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Предупреждения
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-yellow-600">{warningCount}</p>
          </CardContent>
        </Card>
        <Card className={alertCount > 0 ? 'border-red-200' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Критические нарушения
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className={cn('text-2xl font-bold', alertCount > 0 ? 'text-red-600' : 'text-green-600')}>
              {alertCount}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Таблица метрик */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Детальные метрики</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium text-muted-foreground">Группа</th>
                  <th className="text-left py-2 font-medium text-muted-foreground">Метрика</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Значение</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Ожидаемый диапазон</th>
                  <th className="text-right py-2 font-medium text-muted-foreground">Статус</th>
                </tr>
              </thead>
              <tbody>
                {data.metrics.map((metric, idx) => (
                  <tr key={idx} className="border-b last:border-0">
                    <td className="py-2">{metric.group}</td>
                    <td className="py-2">{metric.metric}</td>
                    <td className="py-2 text-right font-mono">{metric.value.toFixed(1)}</td>
                    <td className="py-2 text-right font-mono text-muted-foreground">
                      {metric.expected_range
                        ? `${metric.expected_range.min} – ${metric.expected_range.max}`
                        : '—'}
                    </td>
                    <td className="py-2 text-right">
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded-full text-xs font-medium',
                          statusColorMap[metric.status]
                        )}
                      >
                        {statusLabelMap[metric.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-xs text-muted-foreground">
            * Аудит основан на анализе оценок и демографических данных операторов.
            Отклонения могут указывать на систематическую ошибку.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
