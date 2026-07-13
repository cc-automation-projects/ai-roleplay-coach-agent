import React from 'react';
import { Button } from '@/shared/ui/button';

interface QuickPhrasesProps {
  onSelect: (phrase: string) => void;
  disabled?: boolean;
}

const PHRASES = [
  'Я понимаю вас.',
  'Извините за неудобства.',
  'Давайте проверим это вместе.',
  'Позвольте уточнить детали.',
  'Спасибо за ваше терпение.',
];

export const QuickPhrases: React.FC<QuickPhrasesProps> = ({ onSelect, disabled }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {PHRASES.map((phrase) => (
        <Button
          key={phrase}
          variant="outline"
          size="sm"
          className="text-xs h-7 px-2"
          onClick={() => onSelect(phrase)}
          disabled={disabled}
        >
          {phrase}
        </Button>
      ))}
    </div>
  );
};
