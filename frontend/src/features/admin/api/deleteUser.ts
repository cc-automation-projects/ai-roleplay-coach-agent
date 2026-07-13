import apiClient from '@/shared/api/client';

export const deleteUser = async (userId: string): Promise<void> => {
  await apiClient.delete(`/api/v1/auth/users/${userId}`);
};
