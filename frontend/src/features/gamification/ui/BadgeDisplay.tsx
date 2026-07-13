import React from 'react';
import { Badge as BadgeIcon } from 'lucide-react';
import { Card, CardContent } from '@/shared/ui/card';
import { cn } from '@/shared/lib/utils';
import { Badge as UIBadge } from '@/shared/ui/badge';

interface BadgeDisplayProps {
  name: string;
  description: string;
  iconUrl?: string;
  isEarned?: boolean;
  className?: string;
}

export const BadgeDisplay: React.FC<BadgeDisplayProps> = ({
  name,
  description,
  iconUrl,
  isEarned = false,
  className,
}) => {
  return (
    <Card
      className={cn(
        'p-4 text-center transition-all',
        isEarned ? 'border-primary' : 'opacity-50 grayscale',
        className
      )}
    >
      <CardContent className="p-2">
        <div className="flex flex-col items-center gap-2">
          {iconUrl ? (
            <img src={iconUrl} alt={name} className="h-12 w-12 object-contain" />
          ) : (
            <BadgeIcon className={cn('h-12 w-12', isEarned ? 'text-primary' : 'text-muted-foreground')} />
          )}
          <span className="font-medium text-sm">{name}</span>
          <span className="text-xs text-muted-foreground">{description}</span>
          {isEarned && (
            <UIBadge variant="outline" className="text-xs border-green-500 text-green-600">
              Получен
            </UIBadge>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
