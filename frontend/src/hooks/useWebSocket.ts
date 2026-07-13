import { useEffect, useRef } from 'react';
import { WebSocketClient } from '@/shared/lib/ws-client';
import { sessionStore } from '@/store/sessionStore';
import { metricsStore } from '@/store/metricsStore';

export const useWebSocket = (sessionId: string | null) => {
  const wsRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    if (!sessionId) {
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
      }
      return;
    }

    const wsUrl = `${import.meta.env.VITE_WS_URL}/ws/session/${sessionId}`;
    const ws = new WebSocketClient(wsUrl);
    wsRef.current = ws;

    // Подписка на сообщения
    const unsubscribe = ws.onMessage((message) => {
      switch (message.type) {
        case 'client_message': {
          const { data } = message;
          sessionStore.getState().addMessage(
            data.speaker === 'client' ? 'client' : 'operator',
            data.text
          );
          break;
        }
        case 'client_typing': {
          sessionStore.getState().setTyping(message.data.isTyping);
          break;
        }
        case 'coach_metrics': {
          metricsStore.getState().updateMetrics({
            empathy: message.data.empathy,
            tone: message.data.tone,
            scriptAdherence: message.data.scriptAdherence,
            objectionHandling: message.data.objectionHandling,
            completeness: message.data.completeness,
          });
          break;
        }
        case 'session_ended': {
          sessionStore.getState().setStatus('completed');
          // Можно также уведомить пользователя
          break;
        }
        case 'error': {
          console.error('WebSocket error:', message.data.message);
          break;
        }
        default:
          console.warn('Unknown WebSocket message type:', message);
      }
    });

    ws.connect();

    return () => {
      unsubscribe();
      ws.disconnect();
      wsRef.current = null;
    };
  }, [sessionId]);

  const sendMessage = (data: unknown) => {
    if (wsRef.current?.isConnected) {
      wsRef.current.send(data);
    } else {
      console.warn('WebSocket not connected');
    }
  };

  return { sendMessage, isConnected: wsRef.current?.isConnected ?? false };
};
