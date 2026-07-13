export interface PlanStep {
  order: number;
  title: string;
  description: string;
  estimated_minutes: number;
}

export interface LearningPlan {
  id: string;
  user_id: string;
  scenario_id: string | null;
  focus_areas: string[];
  steps: PlanStep[];
  difficulty_label: string;
  created_at: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface MicroQuiz {
  id: string;
  scenario_id: string | null;
  title: string;
  questions: QuizQuestion[];
  created_at: string;
}

export interface LmsSyncResult {
  status: 'synced' | 'pending' | 'failed';
  lms_course_id: string;
  lms_url: string;
  user_id: string;
  focus_areas: string[];
  step_count: number;
}

export interface QuizAnswer {
  questionIndex: number;
  selectedIndex: number;
}

export interface QuizResult {
  correct: number;
  total: number;
  answers: QuizAnswer[];
}
