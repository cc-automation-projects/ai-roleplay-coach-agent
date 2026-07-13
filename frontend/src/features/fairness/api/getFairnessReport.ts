import apiClient from '@/shared/api/client';
import { FairnessReport } from '@/features/fairness/types';

export const getFairnessReport = async (): Promise<FairnessReport> => {
  // Эндпоинт пока не реализован, возвращаем заглушку
  // В будущем: GET /api/v1/fairness/report
  return {
    id: 'fairness-001',
    generated_at: new Date().toISOString(),
    metrics: [
      {
        group: 'Пол (женщины)',
        metric: 'Средняя оценка',
        value: 78.5,
        expected_range: { min: 75, max: 85 },
        status: 'ok',
      },
      {
        group: 'Пол (мужчины)',
        metric: 'Средняя оценка',
        value: 76.2,
        expected_range: { min: 75, max: 85 },
        status: 'ok',
      },
      {
        group: 'Акцент (южный)',
        metric: 'Средняя оценка',
        value: 68.0,
        expected_range: { min: 72, max: 82 },
        status: 'alert',
      },
      {
        group: 'Акцент (северный)',
        metric: 'Средняя оценка',
        value: 79.0,
        expected_range: { min: 72, max: 82 },
        status: 'ok',
      },
      {
        group: 'Тембр (низкий)',
        metric: 'Средняя оценка',
        value: 74.0,
        expected_range: { min: 70, max: 80 },
        status: 'ok',
      },
      {
        group: 'Тембр (высокий)',
        metric: 'Средняя оценка',
        value: 72.0,
        expected_range: { min: 70, max: 80 },
        status: 'ok',
      },
    ],
    summary: {
      total_alert: 1,
      total_warning: 0,
      status: 'warning',
    },
  };
};
