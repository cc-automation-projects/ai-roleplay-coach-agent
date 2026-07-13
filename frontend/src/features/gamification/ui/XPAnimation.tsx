import React, { useEffect, useState } from 'react';
import { cn } from '@/shared/lib/utils';

interface XPAnimationProps {
  amount: number;
  initial?: number;
  onComplete?: () => void;
  className?: string;
}

export const XPAnimation: React.FC<XPAnimationProps> = ({
  amount,
  initial = 0,
  onComplete,
  className,
}) => {
  const [displayValue, setDisplayValue] = useState(initial);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (amount === 0) return;

    setIsAnimating(true);
    const target = initial + amount;
    const duration = 800;
    const startTime = Date.now();
    const startValue = initial;

    const update = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startValue + (target - startValue) * eased);

      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        setDisplayValue(target);
        setIsAnimating(false);
        onComplete?.();
      }
    };

    requestAnimationFrame(update);
  }, [amount, initial, onComplete]);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-2xl font-bold">{displayValue}</span>
      <span className="text-sm text-muted-foreground">XP</span>
      {isAnimating && (
        <span className="text-green-500 text-sm font-medium animate-pulse">+{amount}</span>
      )}
    </div>
  );
};
