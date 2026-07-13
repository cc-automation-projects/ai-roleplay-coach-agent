import React, { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { BookOpen, FileText, RefreshCw } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const QuickActions: React.FC = () => {
  const navigate = useNavigate();
  const [scenarioId, setScenarioId] = useState('');

  const handleGeneratePlan = () => {
    if (!scenarioId.trim()) {
      toast.error('Введите ID сценария');
      return;
    }
    navigate({ to: `/trainer/learning-plan`, search: { scenarioId: scenarioId.trim() } });
  };

  const handleGenerateQuiz = () => {
    if (!scenarioId.trim()) {
      toast.error('Введите ID сценария');
      return;
    }
    navigate({ to: `/trainer/quiz/${scenarioId.trim()}` });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Быстрые действия куратора</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="scenarioId" className="text-xs">
            ID сценария
          </Label>
          <Input
            id="scenarioId"
            placeholder="Например: 123e4567..."
            value={scenarioId}
            onChange={(e) => setScenarioId(e.target.value)}
            className="mt-1"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleGeneratePlan}
            disabled={!scenarioId.trim()}
          >
            <FileText className="h-4 w-4 mr-1" />
            Учебный план
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateQuiz}
            disabled={!scenarioId.trim()}
          >
            <BookOpen className="h-4 w-4 mr-1" />
            Квиз
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
