import apiClient from '@/shared/api/client';

export interface UpdateUserRequest {
  name?: string;
  role?: 'operator' | 'trainer' | 'admin';
  is_active?: boolean;
}

export const updateUser = async (userId: string, data: UpdateUserRequest): Promise<void> => {
  await apiClient.patch(`/api/v1/auth/users/${userId}`, data);
};
