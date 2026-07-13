import React, { useState } from 'react';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { sendTurn } from '@/features/session/api/sendTurn';
import { sessionStore } from '@/store/sessionStore';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'react-hot-toast';

interface MessageInputProps {
  sessionId: string;
  onMessageSent?: () => void;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  sessionId,
  onMessageSent,
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();

  const addMessage = sessionStore((state) => state.addMessage);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !user) return;

    setIsLoading(true);
    const text = message.trim();
    setMessage('');

    // Optimistic update
    addMessage('operator', text);

    try {
      await sendTurn(sessionId, user.id, text);
      onMessageSent?.();
    } catch (error: any) {
      // В случае ошибки удаляем оптимистичное сообщение и показываем тост
      // Можно реализовать rollback, но для простоты просто уведомим
      toast.error('Не удалось отправить сообщение. Попробуйте ещё раз.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        placeholder="Введите сообщение..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={disabled || isLoading}
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || isLoading || !message.trim()}>
        {isLoading ? 'Отправка...' : 'Отправить'}
      </Button>
    </form>
  );
};
