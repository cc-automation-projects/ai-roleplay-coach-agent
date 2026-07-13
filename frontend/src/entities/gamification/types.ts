export interface XPTransaction {
  id: string;
  user_id: string;
  amount: number;
  reason: string;
  reference_id: string | null;
  created_at: string;
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon_url: string;
  criteria: string;
  xp_reward: number;
  is_hidden: boolean;
  created_at: string;
}

export interface UserBadge extends Badge {
  awarded_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name: string;
  xp_total: number;
  level: number;
}

export interface GamificationStats {
  xp_total: number;
  level: number;
  xp_in_level: number;
  xp_for_next_level: number;
  progress_pct: number;
  recent_txns: XPTransaction[];
  badges: Badge[];
}
