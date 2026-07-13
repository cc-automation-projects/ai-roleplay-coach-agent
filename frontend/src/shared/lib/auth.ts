import { jwtDecode } from 'jwt-decode';

export interface TokenPayload {
  sub: string;
  username: string;
  role: string;
  exp: number;
}

export const decodeToken = (token: string): TokenPayload | null => {
  try {
    return jwtDecode<TokenPayload>(token);
  } catch {
    return null;
  }
};

export const isTokenExpired = (token: string): boolean => {
  const decoded = decodeToken(token);
  if (!decoded) return true;
  return decoded.exp * 1000 < Date.now();
};

export const getAuthHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`,
});
