export interface FairnessMetric {
  group: string;
  metric: string;
  value: number;
  expected_range?: { min: number; max: number };
  status: 'ok' | 'warning' | 'alert';
}

export interface FairnessReport {
  id: string;
  generated_at: string;
  metrics: FairnessMetric[];
  summary: {
    total_alert: number;
    total_warning: number;
    status: 'ok' | 'warning' | 'alert';
  };
}
