import React from 'react';
import { Progress } from '@/shared/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { cn } from '@/shared/lib/utils';

interface ScoreItem {
  label: string;
  value: number;
  color: string;
}

interface ScoreBreakdownProps {
  scores: ScoreItem[];
  className?: string;
}

export const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({ scores, className }) => {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Разбор по измерениям</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {scores.map((item) => (
          <div key={item.label} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">{item.label}</span>
              <span className="font-medium">{Math.round(item.value)}%</span>
            </div>
            <Progress
              value={item.value}
              className="h-2"
              indicatorClassName={cn('transition-all duration-500', item.color)}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
