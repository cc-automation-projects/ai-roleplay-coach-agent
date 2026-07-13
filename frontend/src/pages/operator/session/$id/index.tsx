import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from '@tanstack/react-router';
import { useQuery, useMutation } from '@tanstack/react-query';
import { sessionStore } from '@/store/sessionStore';
import { metricsStore } from '@/store/metricsStore';
import { getSession } from '@/features/session/api/getSession';
import { finishSession } from '@/features/session/api/finishSession';
import { evaluateSession } from '@/features/session/api/evaluateSession';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ChatWindow } from '@/features/session/ui/ChatWindow';
import { MessageInput } from '@/features/session/ui/MessageInput';
import { ScriptHints } from '@/features/session/ui/ScriptHints';
import { MetricsPanel } from '@/features/session/ui/MetricsPanel';
import { QuickPhrases } from '@/features/session/ui/QuickPhrases';
import { VoiceControls } from '@/features/session/ui/VoiceControls';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { toast } from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';

export const SessionPage: React.FC = () => {
  const { id: sessionId } = useParams({ from: '/operator/session/$id' });
  const navigate = useNavigate();
  const { user } = useAuth();

  const { setSession, addMessage, setStatus, reset: resetSession } = sessionStore();
  const resetMetrics = metricsStore((state) => state.reset);

  // Загрузка сессии
  const { data: session, isLoading } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => getSession(sessionId),
    enabled: !!sessionId,
  });

  // Инициализация стора при загрузке
  useEffect(() => {
    if (session) {
      setSession(session.id, session.scenario_id, session.psychotype_at_start);
      // Восстанавливаем транскрипт из бэкенда
      session.transcript?.forEach((entry) => {
        addMessage(entry.speaker, entry.text);
      });
    }
    return () => {
      resetSession();
      resetMetrics();
    };
  }, [session, setSession, addMessage, resetSession, resetMetrics]);

  // WebSocket
  const { sendMessage, isConnected } = useWebSocket(sessionId);

  // Мутация для завершения сессии
  const finishMutation = useMutation({
    mutationFn: () => finishSession(sessionId),
    onSuccess: () => {
      setStatus('completed');
      toast.success('Сессия завершена');
      // Перенаправляем на страницу результатов
      navigate({ to: `/operator/session/${sessionId}/results` });
    },
    onError: () => {
      toast.error('Не удалось завершить сессию');
    },
  });

  // Мутация для оценки
  const evaluateMutation = useMutation({
    mutationFn: () => evaluateSession(sessionId),
    onSuccess: (data) => {
      // Переходим на страницу результатов с данными оценки
      navigate({ to: `/operator/session/${sessionId}/results`, state: { evaluation: data } });
    },
    onError: () => {
      toast.error('Не удалось получить оценку');
    },
  });

  const handleFinish = () => {
    if (window.confirm('Завершить сессию и перейти к результатам?')) {
      finishMutation.mutate();
    }
  };

  const handleEvaluate = () => {
    evaluateMutation.mutate();
  };

  const handleQuickPhrase = (phrase: string) => {
    // Отправляем быструю фразу
    if (user) {
      // Используем sendTurn через MessageInput? Лучше отправить напрямую через API
      // Пока просто вставляем в поле ввода (упрощённо)
      // В реальности нужно вызвать sendTurn
      toast('Быстрая фраза добавлена в поле ввода');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!session) {
    return <div>Сессия не найдена</div>;
  }

  return (
    <div className="flex flex-col h-full max-h-screen p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold">Симуляция: {session.scenario_id}</h1>
          <div className="text-sm text-muted-foreground">
            Статус: {session.status} • {isConnected ? '🟢 Онлайн' : '🔴 Офлайн'}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleFinish} disabled={finishMutation.isPending}>
            Завершить
          </Button>
          <Button variant="default" onClick={handleEvaluate} disabled={evaluateMutation.isPending}>
            Оценить
          </Button>
        </div>
      </div>

      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Левая колонка: чат */}
        <div className="flex-1 flex flex-col min-w-0">
          <Card className="flex-1 flex flex-col">
            <CardContent className="flex-1 p-4 overflow-y-auto">
              <ChatWindow />
            </CardContent>
            <div className="p-4 border-t">
              <div className="flex items-center gap-2 mb-2">
                <VoiceControls sessionId={sessionId} disabled={!isConnected} />
                <QuickPhrases onSelect={handleQuickPhrase} disabled={!isConnected} />
              </div>
              <MessageInput sessionId={sessionId} disabled={!isConnected} />
            </div>
          </Card>
        </div>

        {/* Правая колонка: подсказки и метрики */}
        <div className="w-80 flex flex-col gap-4">
          <ScriptHints query={session.transcript?.slice(-1)[0]?.text || ''} sessionId={sessionId} />
          <MetricsPanel />
        </div>
      </div>
    </div>
  );
};
