import React, { useState } from 'react';
import { cn } from '@/shared/lib/utils';
import { Card, CardContent } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { ScrollArea } from '@/shared/ui/scroll-area';
import { ChevronDown, ChevronUp, Lightbulb, ThumbsUp, MessageCircle } from 'lucide-react';

interface SandwichFeedbackProps {
  praiseText: string;
  growthText: string;
  closingText: string;
  scriptCitations?: string[];
  overallScore: number;
  className?: string;
}

export const SandwichFeedback: React.FC<SandwichFeedbackProps> = ({
  praiseText,
  growthText,
  closingText,
  scriptCitations = [],
  overallScore,
  className,
}) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    praise: true,
    growth: true,
    closing: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const Section: React.FC<{
    title: string;
    icon: React.ReactNode;
    color: string;
    sectionKey: string;
    children: React.ReactNode;
  }> = ({ title, icon, color, sectionKey, children }) => {
    const isExpanded = expandedSections[sectionKey] ?? true;

    return (
      <Card className="mb-3 overflow-hidden">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className={cn('p-1.5 rounded-full', color)}>{icon}</div>
            <span className="font-medium">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {isExpanded && (
          <CardContent className="pt-0 pb-4 px-4">
            <div className="prose prose-sm max-w-none text-foreground/90 leading-relaxed">
              {children}
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Заголовок с общей оценкой */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Результаты сессии</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Общая оценка:</span>
          <Badge className={cn('text-lg px-4 py-1', getScoreColor(overallScore))}>
            {Math.round(overallScore)}%
          </Badge>
        </div>
      </div>

      {/* Сэндвич-фидбек */}
      <Section
        title="✅ Что было хорошо"
        icon={<ThumbsUp className="h-4 w-4 text-white" />}
        color="bg-green-500"
        sectionKey="praise"
      >
        <p>{praiseText}</p>
      </Section>

      <Section
        title="🟡 Что можно улучшить"
        icon={<Lightbulb className="h-4 w-4 text-white" />}
        color="bg-yellow-500"
        sectionKey="growth"
      >
        <p className="whitespace-pre-wrap">{growthText}</p>
        {scriptCitations.length > 0 && (
          <div className="mt-3 p-3 bg-muted/50 rounded-md border-l-4 border-primary">
            <p className="text-sm font-medium text-muted-foreground mb-1">📖 По скрипту:</p>
            {scriptCitations.map((citation, index) => (
              <blockquote key={index} className="text-sm italic pl-2 border-l-2 border-primary/30">
                {citation}
              </blockquote>
            ))}
          </div>
        )}
      </Section>

      <Section
        title="🔵 Мотивация"
        icon={<MessageCircle className="h-4 w-4 text-white" />}
        color="bg-blue-500"
        sectionKey="closing"
      >
        <p>{closingText}</p>
      </Section>
    </div>
  );
};
