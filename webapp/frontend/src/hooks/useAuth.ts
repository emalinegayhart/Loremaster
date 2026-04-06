import { useGetUser, useLogout } from '../lib/queryConfig';
import type { User } from '../types/auth';

export interface UseAuthReturn {
  user: User | undefined;
  isLoading: boolean;
  isError: boolean;
  logout: () => Promise<void>;
}

export const useAuth = (): UseAuthReturn => {
  const { data: user, isLoading, isError } = useGetUser();
  const logoutMutation = useLogout();

  const logout = async (): Promise<void> => {
    await logoutMutation.mutateAsync();
  };

  return {
    user,
    isLoading,
    isError,
    logout,
  };
};
