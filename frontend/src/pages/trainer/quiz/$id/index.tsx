import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { generateQuiz } from '@/features/curator/api/generateQuiz';
import { QuizQuestion } from '@/features/curator/ui/QuizQuestion';
import { QuizResults } from '@/features/curator/ui/QuizResults';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';
import { toast } from 'react-hot-toast';

export const QuizPage: React.FC = () => {
  const { id: scenarioId } = useParams({ from: '/trainer/quiz/$id' });
  const navigate = useNavigate();

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<{ questionIndex: number; selectedIndex: number }[]>([]);
  const [showResults, setShowResults] = useState(false);

  const { data: quiz, isLoading, refetch } = useQuery({
    queryKey: ['quiz', scenarioId],
    queryFn: () => generateQuiz(scenarioId, 5),
    enabled: !!scenarioId,
    onError: () => toast.error('Не удалось загрузить квиз'),
  });

  useEffect(() => {
    if (quiz) {
      setAnswers([]);
      setCurrentQuestion(0);
      setShowResults(false);
    }
  }, [quiz]);

  const handleSelectOption = (questionIndex: number, optionIndex: number) => {
    setAnswers((prev) => {
      const existing = prev.findIndex((a) => a.questionIndex === questionIndex);
      if (existing >= 0) {
        const newAnswers = [...prev];
        newAnswers[existing] = { questionIndex, selectedIndex: optionIndex };
        return newAnswers;
      }
      return [...prev, { questionIndex, selectedIndex: optionIndex }];
    });
  };

  const handleNext = () => {
    if (currentQuestion < (quiz?.questions.length || 0) - 1) {
      setCurrentQuestion((prev) => prev + 1);
    } else {
      setShowResults(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const handleRestart = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!quiz || quiz.questions.length === 0) {
    return (
      <div className="p-6 max-w-3xl mx-auto text-center">
        <p className="text-muted-foreground">Квиз не найден или не содержит вопросов</p>
        <Button className="mt-4" onClick={() => navigate({ to: '/trainer' })}>
          ← К дашборду
        </Button>
      </div>
    );
  }

  if (showResults) {
    const result = {
      correct: answers.filter(
        (a) =>
          quiz.questions[a.questionIndex] &&
          a.selectedIndex === quiz.questions[a.questionIndex].correct_index
      ).length,
      total: quiz.questions.length,
      answers,
    };

    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">{quiz.title}</h1>
          <Button variant="outline" onClick={() => navigate({ to: '/trainer' })}>
            ← К дашборду
          </Button>
        </div>
        <QuizResults result={result} questions={quiz.questions} />
        <div className="flex gap-2 mt-4">
          <Button variant="outline" onClick={handleRestart}>
            Пройти заново
          </Button>
        </div>
      </div>
    );
  }

  const question = quiz.questions[currentQuestion];
  const selected = answers.find((a) => a.questionIndex === currentQuestion)?.selectedIndex ?? null;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold">{quiz.title}</h1>
          <p className="text-sm text-muted-foreground">
            Вопрос {currentQuestion + 1} из {quiz.questions.length}
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate({ to: '/trainer' })}>
          Выход
        </Button>
      </div>

      <QuizQuestion
        question={question}
        index={currentQuestion}
        total={quiz.questions.length}
        selectedOption={selected}
        onSelect={(optionIndex) => handleSelectOption(currentQuestion, optionIndex)}
        showExplanation={false}
        onNext={handleNext}
        onPrevious={handlePrevious}
        isLast={currentQuestion === quiz.questions.length - 1}
      />
    </div>
  );
};
