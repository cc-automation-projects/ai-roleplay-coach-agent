import React from 'react';
import { metricsStore } from '@/store/metricsStore';
import { Progress } from '@/shared/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { cn } from '@/shared/lib/utils';

interface MetricItemProps {
  label: string;
  value: number | null;
  color: string;
  max?: number;
}

const MetricItem: React.FC<MetricItemProps> = ({ label, value, color, max = 100 }) => {
  const displayValue = value !== null ? Math.round(value) : 0;
  const isActive = value !== null;

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className={cn('font-medium', isActive ? '' : 'text-muted-foreground')}>
          {isActive ? `${displayValue}%` : '—'}
        </span>
      </div>
      <Progress
        value={isActive ? displayValue : 0}
        className={cn('h-2', !isActive && 'opacity-30')}
        indicatorClassName={cn(color, isActive ? 'opacity-100' : 'opacity-30')}
      />
    </div>
  );
};

export const MetricsPanel: React.FC = () => {
  const metrics = metricsStore((state) => ({
    empathy: state.empathy,
    tone: state.tone,
    scriptAdherence: state.scriptAdherence,
    objectionHandling: state.objectionHandling,
    completeness: state.completeness,
  }));

  const hasMetrics = Object.values(metrics).some((v) => v !== null);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          Live-метрики
          {!hasMetrics && (
            <span className="text-xs text-muted-foreground font-normal">Ожидание данных...</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <MetricItem label="Эмпатия" value={metrics.empathy} color="bg-blue-500" />
        <MetricItem label="Тон" value={metrics.tone} color="bg-green-500" />
        <MetricItem label="Скрипт" value={metrics.scriptAdherence} color="bg-purple-500" />
        <MetricItem label="Возражения" value={metrics.objectionHandling} color="bg-orange-500" />
        <MetricItem label="Полнота" value={metrics.completeness} color="bg-pink-500" />
      </CardContent>
    </Card>
  );
};
