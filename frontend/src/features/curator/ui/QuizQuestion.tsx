import React, { useState } from 'react';
import { QuizQuestion as QuizQuestionType } from '@/entities/curator/types';
import { cn } from '@/shared/lib/utils';
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group';
import { Label } from '@/shared/ui/label';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { CheckCircle2, XCircle, Lightbulb } from 'lucide-react';

interface QuizQuestionProps {
  question: QuizQuestionType;
  index: number;
  total: number;
  selectedOption: number | null;
  onSelect: (index: number) => void;
  showExplanation?: boolean;
  onNext?: () => void;
  onPrevious?: () => void;
  isLast?: boolean;
  disabled?: boolean;
}

export const QuizQuestion: React.FC<QuizQuestionProps> = ({
  question,
  index,
  total,
  selectedOption,
  onSelect,
  showExplanation = false,
  onNext,
  onPrevious,
  isLast = false,
  disabled = false,
}) => {
  const [showHint, setShowHint] = useState(false);

  const isCorrect = selectedOption !== null && selectedOption === question.correct_index;
  const isWrong = selectedOption !== null && selectedOption !== question.correct_index;

  const getOptionClassName = (optionIndex: number) => {
    if (!showExplanation || selectedOption === null) return '';
    if (optionIndex === question.correct_index) return 'border-green-500 bg-green-50 dark:bg-green-950/30';
    if (optionIndex === selectedOption && optionIndex !== question.correct_index) {
      return 'border-red-500 bg-red-50 dark:bg-red-950/30';
    }
    return '';
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Вопрос {index + 1} из {total}
            </span>
            {showExplanation && selectedOption !== null && (
              <span className={cn('font-medium', isCorrect ? 'text-green-600' : 'text-red-600')}>
                {isCorrect ? '✅ Правильно' : '❌ Неправильно'}
              </span>
            )}
          </div>
          <h3 className="text-lg font-medium mt-2">{question.question}</h3>
        </div>

        <RadioGroup
          value={selectedOption !== null ? String(selectedOption) : undefined}
          onValueChange={(value) => onSelect(Number(value))}
          disabled={disabled || showExplanation}
          className="space-y-2"
        >
          {question.options.map((option, optIndex) => (
            <div
              key={optIndex}
              className={cn(
                'flex items-center space-x-2 p-3 rounded-lg border transition-colors',
                getOptionClassName(optIndex),
                !disabled && !showExplanation && 'hover:bg-muted/50 cursor-pointer'
              )}
            >
              <RadioGroupItem value={String(optIndex)} id={`q${index}-opt${optIndex}`} />
              <Label htmlFor={`q${index}-opt${optIndex}`} className="flex-1 cursor-pointer text-sm">
                {option}
              </Label>
              {showExplanation && optIndex === question.correct_index && (
                <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
              )}
              {showExplanation && optIndex === selectedOption && optIndex !== question.correct_index && (
                <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
              )}
            </div>
          ))}
        </RadioGroup>

        {/* Кнопка подсказки */}
        {!showExplanation && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-3 text-xs"
            onClick={() => setShowHint(!showHint)}
          >
            <Lightbulb className="h-3 w-3 mr-1" />
            {showHint ? 'Скрыть подсказку' : 'Показать подсказку'}
          </Button>
        )}
        {showHint && !showExplanation && (
          <p className="text-sm text-muted-foreground mt-1 italic bg-muted p-2 rounded-md">
            💡 {question.explanation}
          </p>
        )}

        {/* Объяснение после ответа */}
        {showExplanation && selectedOption !== null && (
          <div className="mt-4 p-3 bg-muted rounded-md">
            <p className="text-sm">
              <span className="font-medium">Объяснение:</span> {question.explanation}
            </p>
          </div>
        )}

        {/* Навигация */}
        <div className="flex justify-between mt-4">
          <Button
            variant="outline"
            onClick={onPrevious}
            disabled={index === 0 || disabled}
          >
            ← Назад
          </Button>
          <Button
            onClick={onNext}
            disabled={selectedOption === null || disabled}
          >
            {isLast ? 'Завершить' : 'Далее →'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
