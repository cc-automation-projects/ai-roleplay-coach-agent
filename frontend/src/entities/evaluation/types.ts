export interface Evaluation {
  id: string;
  session_id: string;
  user_id: string;
  overall_score: number;
  script_adherence: number;
  tone_score: number;
  empathy_score: number;
  objection_handling: number;
  completeness_score: number;
  praise_text: string;
  growth_text: string;
  closing_text: string;
  script_citations: string[];
  gaming_detected: boolean;
  gaming_notes: string;
  created_at: string;
}

export interface EvaluationWeights {
  script_adherence: number;
  tone_score: number;
  empathy_score: number;
  objection_handling: number;
  completeness_score: number;
}

export interface GradeInfo {
  letter: 'A' | 'B' | 'C' | 'D' | 'F';
  label: string;
  color: string;
}

export const getGradeInfo = (score: number): GradeInfo => {
  if (score >= 90) return { letter: 'A', label: 'Отлично', color: 'text-green-600' };
  if (score >= 80) return { letter: 'B', label: 'Хорошо', color: 'text-blue-600' };
  if (score >= 70) return { letter: 'C', label: 'Удовлетворительно', color: 'text-yellow-600' };
  if (score >= 60) return { letter: 'D', label: 'Слабо', color: 'text-orange-600' };
  return { letter: 'F', label: 'Неудовлетворительно', color: 'text-red-600' };
};
