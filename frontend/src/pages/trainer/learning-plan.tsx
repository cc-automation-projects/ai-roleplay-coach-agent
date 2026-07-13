import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { getLearningPlan } from '@/features/curator/api/getLearningPlan';
import { LearningPlanSteps } from '@/widgets/Curator/LearningPlanSteps';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Skeleton } from '@/shared/ui/skeleton';
import { toast } from 'react-hot-toast';

export const LearningPlanPage: React.FC = () => {
  const [scenarioId, setScenarioId] = useState('');
  const [fetchId, setFetchId] = useState<string | null>(null);
  const navigate = useNavigate();

  const { data: plan, isLoading, refetch } = useQuery({
    queryKey: ['learningPlan', fetchId],
    queryFn: () => getLearningPlan(fetchId!),
    enabled: !!fetchId,
    onError: () => toast.error('Не удалось загрузить учебный план'),
  });

  const handleGenerate = () => {
    if (!scenarioId.trim()) {
      toast.error('Введите ID сценария');
      return;
    }
    setFetchId(scenarioId.trim());
    refetch();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Учебный план</h1>
        <Button variant="outline" onClick={() => navigate({ to: '/trainer' })}>
          ← К дашборду
        </Button>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Сгенерировать план</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <div className="flex-1">
              <Label htmlFor="scenarioId" className="sr-only">
                ID сценария
              </Label>
              <Input
                id="scenarioId"
                placeholder="Введите ID сценария..."
                value={scenarioId}
                onChange={(e) => setScenarioId(e.target.value)}
              />
            </div>
            <Button onClick={handleGenerate} disabled={isLoading}>
              {isLoading ? 'Загрузка...' : 'Сгенерировать'}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            План будет построен на основе слабых мест оператора в данном сценарии.
          </p>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : plan ? (
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <span>План для пользователя: {plan.user_id.slice(0, 8)}</span>
            <span>•</span>
            <span>Сложность: {plan.difficulty_label}</span>
            <span>•</span>
            <span>Создан: {new Date(plan.created_at).toLocaleDateString()}</span>
          </div>
          <LearningPlanSteps steps={plan.steps} focusAreas={plan.focus_areas} />
        </div>
      ) : (
        <div className="text-center text-muted-foreground py-12">
          <p>Введите ID сценария, чтобы сгенерировать план.</p>
        </div>
      )}
    </div>
  );
};
