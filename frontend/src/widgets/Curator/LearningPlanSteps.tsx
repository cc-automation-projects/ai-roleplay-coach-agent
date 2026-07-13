import React from 'react';
import { PlanStep } from '@/entities/curator/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { CheckCircle2, Clock, BookOpen, Target } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

interface LearningPlanStepsProps {
  steps: PlanStep[];
  focusAreas: string[];
  className?: string;
}

export const LearningPlanSteps: React.FC<LearningPlanStepsProps> = ({
  steps,
  focusAreas,
  className,
}) => {
  const getStepIcon = (order: number, total: number) => {
    if (order === total) return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    return <BookOpen className="h-5 w-5 text-muted-foreground" />;
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Фокус-области */}
      {focusAreas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Target className="h-4 w-4" />
              Области для развития
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {focusAreas.map((area) => (
                <Badge key={area} variant="secondary">
                  {area}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Шаги плана */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">План действий</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {steps.map((step, index) => (
            <div
              key={step.order}
              className={cn(
                'flex items-start gap-4 p-3 rounded-lg border',
                index === steps.length - 1 ? 'border-green-200 bg-green-50 dark:bg-green-950/20' : ''
              )}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getStepIcon(step.order, steps.length)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm">Шаг {step.order}</span>
                  <span className="text-sm">{step.title}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">{step.description}</p>
                <div className="flex items-center gap-1 mt-1.5 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{step.estimated_minutes} мин</span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};
