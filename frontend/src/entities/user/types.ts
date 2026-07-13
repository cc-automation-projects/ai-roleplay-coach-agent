// Типы, соответствующие бэкенд-моделям User и API-ответам

export type UserRole = 'operator' | 'trainer' | 'admin';

export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
  role: UserRole;
  xpTotal: number;
  level: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Ответы API
export interface AuthResponse {
  user_id: string;
  username: string;
  role: UserRole;
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface UserInfo {
  user_id: string;
  username: string;
  role: UserRole;
  email: string;
  is_active: boolean;
}
