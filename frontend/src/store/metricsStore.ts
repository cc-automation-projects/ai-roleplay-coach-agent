import { create } from 'zustand';

export interface MetricsState {
  empathy: number | null;
  tone: number | null;
  scriptAdherence: number | null;
  objectionHandling: number | null;
  completeness: number | null;
  gamingDetected: boolean | null;

  // Actions
  updateMetrics: (data: Partial<Omit<MetricsState, 'updateMetrics'>>) => void;
  reset: () => void;
}

export const metricsStore = create<MetricsState>((set) => ({
  empathy: null,
  tone: null,
  scriptAdherence: null,
  objectionHandling: null,
  completeness: null,
  gamingDetected: null,

  updateMetrics: (data) =>
    set((state) => ({
      ...state,
      ...data,
    })),

  reset: () =>
    set({
      empathy: null,
      tone: null,
      scriptAdherence: null,
      objectionHandling: null,
      completeness: null,
      gamingDetected: null,
    }),
}));
