import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useRouterState } from '@tanstack/react-router';
import { useQuery, useMutation } from '@tanstack/react-query';
import { sessionStore } from '@/store/sessionStore';
import { metricsStore } from '@/store/metricsStore';
import { useAuth } from '@/hooks/useAuth';

import { getSession } from '@/features/session/api/getSession';
import { evaluateSession } from '@/features/session/api/evaluateSession';
import { getXPStats } from '@/features/gamification/api/getXPStats';
import { getStreak } from '@/features/gamification/api/getStreak';
import { getUserBadges } from '@/features/gamification/api/getBadges';

import { SandwichFeedback } from '@/features/evaluation/ui/SandwichFeedback';
import { RadarChart } from '@/features/evaluation/ui/RadarChart';
import { ScoreBreakdown } from '@/features/evaluation/ui/ScoreBreakdown';
import { XPAnimation } from '@/features/gamification/ui/XPAnimation';
import { LevelUpModal } from '@/features/gamification/ui/LevelUpModal';
import { BadgeDisplay } from '@/features/gamification/ui/BadgeDisplay';

import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';
import { toast } from 'react-hot-toast';

import { getGradeInfo } from '@/entities/evaluation/types';
import { Badge } from '@/entities/gamification/types';

export const ResultsPage: React.FC = () => {
  const { id: sessionId } = useParams({ from: '/operator/session/$id/results' });
  const navigate = useNavigate();
  const { user } = useAuth();
  const routerState = useRouterState();

  // Получаем оценку из состояния роутера (если передана) или запрашиваем
  const [evaluationData, setEvaluationData] = useState(routerState.location.state?.evaluation || null);

  // Если оценки нет в состоянии – запрашиваем
  const { data: evaluation, isLoading: evalLoading } = useQuery({
    queryKey: ['evaluation', sessionId],
    queryFn: () => evaluateSession(sessionId),
    enabled: !evaluationData && !!sessionId,
    onSuccess: (data) => setEvaluationData(data),
    onError: () => toast.error('Не удалось загрузить оценку сессии'),
  });

  // Загрузка XP статистики
  const { data: xpStats, isLoading: xpLoading, refetch: refetchXP } = useQuery({
    queryKey: ['xpStats', user?.id],
    queryFn: () => getXPStats(user!.id),
    enabled: !!user && !!evaluationData,
  });

  // Загрузка бейджей пользователя
  const { data: userBadges, isLoading: badgesLoading } = useQuery({
    queryKey: ['userBadges', user?.id],
    queryFn: () => getUserBadges(user!.id),
    enabled: !!user,
  });

  // Загрузка стрика
  const { data: streakData } = useQuery({
    queryKey: ['streak', user?.id],
    queryFn: () => getStreak(user!.id),
    enabled: !!user,
  });

  const [showLevelUp, setShowLevelUp] = useState(false);
  const [oldLevel, setOldLevel] = useState(1);
  const [newLevel, setNewLevel] = useState(1);

  // Проверка повышения уровня
  useEffect(() => {
    if (xpStats && user?.level) {
      if (xpStats.level > user.level) {
        setOldLevel(user.level);
        setNewLevel(xpStats.level);
        setShowLevelUp(true);
        // Обновляем пользователя в сторе
        // Здесь можно обновить authStore
      }
    }
  }, [xpStats, user]);

  const finalEval = evaluationData || evaluation;

  if (evalLoading || xpLoading || badgesLoading) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-48 w-full mt-4" />
          </div>
          <div>
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-48 w-full mt-4" />
          </div>
        </div>
      </div>
    );
  }

  if (!finalEval) {
    return (
      <div className="p-6 max-w-6xl mx-auto text-center">
        <p className="text-muted-foreground">Оценка не найдена</p>
        <Button className="mt-4" onClick={() => navigate({ to: '/operator' })}>
          Вернуться к сценариям
        </Button>
      </div>
    );
  }

  const grade = getGradeInfo(finalEval.overall_score);

  // Данные для радара
  const radarData = [
    { dimension: 'script_adherence', value: finalEval.script_adherence },
    { dimension: 'tone_score', value: finalEval.tone_score },
    { dimension: 'empathy_score', value: finalEval.empathy_score },
    { dimension: 'objection_handling', value: finalEval.objection_handling },
    { dimension: 'completeness_score', value: finalEval.completeness_score },
  ];

  // Данные для разбора
  const scoreItems = [
    { label: 'Скрипт', value: finalEval.script_adherence, color: 'bg-indigo-500' },
    { label: 'Тон', value: finalEval.tone_score, color: 'bg-green-500' },
    { label: 'Эмпатия', value: finalEval.empathy_score, color: 'bg-blue-500' },
    { label: 'Возражения', value: finalEval.objection_handling, color: 'bg-amber-500' },
    { label: 'Полнота', value: finalEval.completeness_score, color: 'bg-pink-500' },
  ];

  // XP из оценки (примерно)
  const earnedXP = finalEval.overall_score >= 70 ? 100 : 0;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* Заголовок */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Результаты сессии</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-sm text-muted-foreground">
              Сессия завершена {new Date().toLocaleString()}
            </span>
            <span className={cn('font-bold text-lg', grade.color)}>
              {grade.letter} — {grade.label}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <XPAnimation amount={earnedXP} initial={xpStats?.xp_total || 0} />
          <Button variant="outline" onClick={() => navigate({ to: '/operator' })}>
            ← К сценариям
          </Button>
        </div>
      </div>

      {/* Основная сетка */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Левая колонка: Фидбек */}
        <div className="lg:col-span-2 space-y-6">
          <SandwichFeedback
            praiseText={finalEval.praise_text}
            growthText={finalEval.growth_text}
            closingText={finalEval.closing_text}
            scriptCitations={finalEval.script_citations}
            overallScore={finalEval.overall_score}
          />

          {/* Статистика геймификации */}
          {xpStats && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Ваш прогресс</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Уровень</p>
                  <p className="text-xl font-bold">{xpStats.level}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">XP всего</p>
                  <p className="text-xl font-bold">{xpStats.xp_total}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Стрик</p>
                  <p className="text-xl font-bold">{streakData?.streak || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Бейджи</p>
                  <p className="text-xl font-bold">{userBadges?.length || 0}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Правая колонка: Графики */}
        <div className="space-y-6">
          <RadarChart data={radarData} />
          <ScoreBreakdown scores={scoreItems} />

          {/* Бейджи, полученные за сессию */}
          {userBadges && userBadges.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Ваши бейджи</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2">
                  {userBadges.slice(0, 4).map((badge: Badge) => (
                    <BadgeDisplay
                      key={badge.id}
                      name={badge.name}
                      description={badge.description}
                      iconUrl={badge.icon_url}
                      isEarned
                    />
                  ))}
                </div>
                {userBadges.length > 4 && (
                  <p className="text-sm text-muted-foreground text-center mt-2">
                    + еще {userBadges.length - 4} бейджей
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Level Up Modal */}
      {user && (
        <LevelUpModal
          isOpen={showLevelUp}
          newLevel={newLevel}
          oldLevel={oldLevel}
          onClose={() => setShowLevelUp(false)}
        />
      )}
    </div>
  );
};
