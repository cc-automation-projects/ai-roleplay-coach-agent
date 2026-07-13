import React from 'react';
import {
  Radar,
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';

interface RadarChartProps {
  data: {
    dimension: string;
    value: number;
    fullMark?: number;
  }[];
  title?: string;
  className?: string;
}

const DIMENSION_LABELS: Record<string, string> = {
  script_adherence: 'Скрипт',
  tone_score: 'Тон',
  empathy_score: 'Эмпатия',
  objection_handling: 'Возражения',
  completeness_score: 'Полнота',
  overall_score: 'Общий',
};

const DIMENSION_COLORS: Record<string, string> = {
  script_adherence: '#6366f1', // indigo
  tone_score: '#22c55e', // green
  empathy_score: '#3b82f6', // blue
  objection_handling: '#f59e0b', // amber
  completeness_score: '#ec4899', // pink
  overall_score: '#8b5cf6', // purple
};

export const RadarChart: React.FC<RadarChartProps> = ({ data, title, className }) => {
  const formattedData = data.map((item) => ({
    ...item,
    subject: DIMENSION_LABELS[item.dimension] || item.dimension,
    fullMark: 100,
  }));

  // Определяем цвет для первой серии данных
  const mainDimension = data[0]?.dimension || 'overall_score';
  const strokeColor = DIMENSION_COLORS[mainDimension] || '#6366f1';

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title || 'Радар навыков'}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <RechartsRadar cx="50%" cy="50%" outerRadius="80%" data={formattedData}>
            <PolarGrid />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
              tickCount={5}
            />
            <Tooltip
              content={({ payload }) => {
                if (!payload || payload.length === 0) return null;
                const item = payload[0].payload;
                return (
                  <div className="bg-background border rounded-md p-2 shadow-sm">
                    <p className="text-sm font-medium">{item.subject}</p>
                    <p className="text-sm text-muted-foreground">{Math.round(item.value)}%</p>
                  </div>
                );
              }}
            />
            <Radar
              name="Оценка"
              dataKey="value"
              stroke={strokeColor}
              fill={strokeColor}
              fillOpacity={0.3}
            />
          </RechartsRadar>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
