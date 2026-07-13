import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';

interface ScriptHintsProps {
  query: string;
  sessionId: string;
}

// Этот эндпоинт пока не реализован в бэкенде, поэтому делаем заглушку
const fetchHints = async (query: string) => {
  // В реальности будет GET /api/v1/rag/hints?query=...
  // Пока возвращаем фиктивные данные
  return [
    { id: '1', text: 'При жалобе на биллинг сначала извинитесь и подтвердите проблему.' },
    { id: '2', text: 'Проверьте историю в CRM по номеру телефона.' },
    { id: '3', text: 'Предложите клиенту альтернативный способ оплаты.' },
  ];
};

export const ScriptHints: React.FC<ScriptHintsProps> = ({ query }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['hints', query],
    queryFn: () => fetchHints(query),
    enabled: query.length > 2,
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Подсказки по скрипту</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Подсказки по скрипту</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Нет подсказок для текущего контекста</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Подсказки по скрипту</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.map((hint) => (
          <div key={hint.id} className="text-sm bg-muted p-2 rounded-md border-l-2 border-primary">
            {hint.text}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
