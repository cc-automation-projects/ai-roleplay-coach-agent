import { create } from 'zustand';

export interface TranscriptEntry {
  id: string;
  speaker: 'operator' | 'client';
  text: string;
  timestamp: string;
}

export interface SessionState {
  sessionId: string | null;
  scenarioId: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'interrupted' | 'failed';
  transcript: TranscriptEntry[];
  psychotype: string | null;
  ddaLevel: number;
  isTyping: boolean; // клиент печатает

  // Actions
  setSession: (sessionId: string, scenarioId: string, psychotype?: string) => void;
  addMessage: (speaker: 'operator' | 'client', text: string) => void;
  setTyping: (isTyping: boolean) => void;
  setStatus: (status: SessionState['status']) => void;
  reset: () => void;
}

export const sessionStore = create<SessionState>((set, get) => ({
  sessionId: null,
  scenarioId: null,
  status: 'pending',
  transcript: [],
  psychotype: null,
  ddaLevel: 0,
  isTyping: false,

  setSession: (sessionId, scenarioId, psychotype = null) =>
    set({
      sessionId,
      scenarioId,
      psychotype,
      status: 'in_progress',
      transcript: [],
      ddaLevel: 0,
    }),

  addMessage: (speaker, text) =>
    set((state) => ({
      transcript: [
        ...state.transcript,
        {
          id: crypto.randomUUID(),
          speaker,
          text,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  setTyping: (isTyping) => set({ isTyping }),

  setStatus: (status) => set({ status }),

  reset: () =>
    set({
      sessionId: null,
      scenarioId: null,
      status: 'pending',
      transcript: [],
      psychotype: null,
      ddaLevel: 0,
      isTyping: false,
    }),
}));
