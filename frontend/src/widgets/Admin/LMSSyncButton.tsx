import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { syncLMS } from '@/features/curator/api/syncLMS';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { toast } from 'react-hot-toast';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

export const LMSSyncButton: React.FC = () => {
  const [planId, setPlanId] = useState('');
  const [syncResult, setSyncResult] = useState<{ status: string; lms_course_id: string; lms_url: string } | null>(null);

  const syncMutation = useMutation({
    mutationFn: (id: string) => syncLMS(id),
    onSuccess: (data) => {
      setSyncResult(data);
      toast.success('Синхронизация с LMS выполнена успешно');
    },
    onError: () => {
      toast.error('Ошибка синхронизации с LMS');
      setSyncResult(null);
    },
  });

  const handleSync = () => {
    if (!planId.trim()) {
      toast.error('Введите ID учебного плана');
      return;
    }
    syncMutation.mutate(planId.trim());
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Синхронизация с LMS</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="planId" className="text-xs">
            ID учебного плана
          </Label>
          <div className="flex gap-2 mt-1">
            <Input
              id="planId"
              placeholder="Введите ID плана..."
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              disabled={syncMutation.isPending}
            />
            <Button onClick={handleSync} disabled={syncMutation.isPending || !planId.trim()}>
              {syncMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Синхронизировать'
              )}
            </Button>
          </div>
        </div>

        {syncResult && (
          <div
            className={cn(
              'p-3 rounded-md text-sm',
              syncResult.status === 'synced'
                ? 'bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800'
                : 'bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800'
            )}
          >
            <div className="flex items-start gap-2">
              {syncResult.status === 'synced' ? (
                <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className="font-medium">
                  {syncResult.status === 'synced' ? 'Синхронизация успешна' : 'Статус неизвестен'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Курс: {syncResult.lms_course_id}
                </p>
                <a
                  href={syncResult.lms_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline"
                >
                  Открыть в LMS →
                </a>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
