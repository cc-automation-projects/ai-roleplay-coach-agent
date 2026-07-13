import React from 'react';
import { QuizResult } from '@/entities/curator/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Progress } from '@/shared/ui/progress';
import { Badge } from '@/shared/ui/badge';
import { CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

interface QuizResultsProps {
  result: QuizResult;
  questions: { question: string; options: string[]; correct_index: number }[];
  className?: string;
}

export const QuizResults: React.FC<QuizResultsProps> = ({
  result,
  questions,
  className,
}) => {
  const percentage = Math.round((result.correct / result.total) * 100);
  const isPassing = percentage >= 70;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Сводка */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Результаты квиза</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6 flex-wrap">
            <div>
              <p className="text-sm text-muted-foreground">Правильных ответов</p>
              <p className="text-2xl font-bold">
                {result.correct} / {result.total}
              </p>
            </div>
            <div className="flex-1 min-w-[100px]">
              <Progress value={percentage} className="h-3" />
              <div className="flex justify-between text-sm mt-1">
                <span>{percentage}%</span>
                <Badge variant={isPassing ? 'default' : 'destructive'}>
                  {isPassing ? '✅ Зачтено' : '❌ Не зачтено'}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Детали по вопросам */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Разбор вопросов</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {questions.map((q, idx) => {
            const answer = result.answers.find((a) => a.questionIndex === idx);
            const isCorrect = answer?.selectedIndex === q.correct_index;
            const selectedText = answer !== undefined ? q.options[answer.selectedIndex] : 'Не отвечено';

            return (
              <div key={idx} className="border-b pb-3 last:border-b-0 last:pb-0">
                <div className="flex items-start gap-2">
                  {isCorrect ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-medium">{q.question}</p>
                    <div className="text-sm mt-1">
                      <span className="text-muted-foreground">Ваш ответ: </span>
                      <span className={isCorrect ? 'text-green-600' : 'text-red-600'}>
                        {selectedText}
                      </span>
                      {!isCorrect && (
                        <>
                          <span className="text-muted-foreground ml-2">Правильный ответ: </span>
                          <span className="text-green-600">{q.options[q.correct_index]}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
};
