import React from 'react';
import { cn } from '@/shared/lib/utils';
import { Checkbox } from '@/shared/ui/checkbox'; // из shadcn
import { Label } from '@/shared/ui/label';

interface ConsentCheckboxProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label?: string;
  className?: string;
}

const ConsentCheckbox: React.FC<ConsentCheckboxProps> = ({
  checked,
  onCheckedChange,
  label = 'Я даю согласие на обработку моих персональных данных в соответствии с 152-ФЗ, включая запись голосовых слепков в защищённом контуре.',
  className,
}) => {
  return (
    <div className={cn('flex items-start space-x-2', className)}>
      <Checkbox
        id="consent"
        checked={checked}
        onCheckedChange={onCheckedChange}
        className="mt-1"
      />
      <Label htmlFor="consent" className="text-sm text-muted-foreground leading-relaxed">
        {label}
      </Label>
    </div>
  );
};

export { ConsentCheckbox };
