import React, { useEffect, useRef } from 'react';
import { sessionStore } from '@/store/sessionStore';
import { cn } from '@/shared/lib/utils';
import { Avatar, AvatarFallback } from '@/shared/ui/avatar';

export const ChatWindow: React.FC = () => {
  const transcript = sessionStore((state) => state.transcript);
  const isTyping = sessionStore((state) => state.isTyping);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, isTyping]);

  const getInitials = (speaker: 'operator' | 'client') => {
    return speaker === 'operator' ? 'ОП' : 'КЛ';
  };

  const getAvatarColor = (speaker: 'operator' | 'client') => {
    return speaker === 'operator' ? 'bg-blue-500' : 'bg-green-500';
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/20 rounded-lg min-h-[400px] max-h-[600px]">
      {transcript.length === 0 && (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          Начните диалог с клиентом
        </div>
      )}
      {transcript.map((entry) => (
        <div
          key={entry.id}
          className={cn(
            'flex items-start gap-3',
            entry.speaker === 'operator' ? 'flex-row-reverse' : 'flex-row'
          )}
        >
          <Avatar className="h-8 w-8">
            <AvatarFallback className={getAvatarColor(entry.speaker)}>
              {getInitials(entry.speaker)}
            </AvatarFallback>
          </Avatar>
          <div
            className={cn(
              'rounded-lg px-4 py-2 max-w-[80%]',
              entry.speaker === 'operator'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground'
            )}
          >
            <div className="text-sm whitespace-pre-wrap break-words">{entry.text}</div>
            <div className="text-xs opacity-70 mt-1">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
      {isTyping && (
        <div className="flex items-start gap-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-green-500">КЛ</AvatarFallback>
          </Avatar>
          <div className="bg-secondary rounded-lg px-4 py-2">
            <div className="flex gap-1">
              <span className="animate-pulse">•</span>
              <span className="animate-pulse delay-100">•</span>
              <span className="animate-pulse delay-200">•</span>
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
};
