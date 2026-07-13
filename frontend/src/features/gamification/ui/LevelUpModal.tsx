import React, { useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/shared/ui/dialog';
import { Button } from '@/shared/ui/button';
import { Trophy, Sparkles } from 'lucide-react';

interface LevelUpModalProps {
  isOpen: boolean;
  newLevel: number;
  oldLevel: number;
  onClose: () => void;
}

export const LevelUpModal: React.FC<LevelUpModalProps> = ({
  isOpen,
  newLevel,
  oldLevel,
  onClose,
}) => {
  useEffect(() => {
    if (isOpen) {
      // Воспроизвести звук или эффект
    }
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md text-center">
        <DialogHeader>
          <div className="flex justify-center">
            <div className="relative">
              <Trophy className="h-16 w-16 text-yellow-500" />
              <Sparkles className="h-6 w-6 text-yellow-400 absolute -top-2 -right-2 animate-pulse" />
            </div>
          </div>
          <DialogTitle className="text-2xl mt-2">🎉 Повышение уровня!</DialogTitle>
          <DialogDescription>
            Вы достигли <strong>уровня {newLevel}</strong>!
            <br />
            <span className="text-sm text-muted-foreground">
              {oldLevel} → {newLevel}
            </span>
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-center gap-2 mt-2">
          <Button onClick={onClose}>Отлично!</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
