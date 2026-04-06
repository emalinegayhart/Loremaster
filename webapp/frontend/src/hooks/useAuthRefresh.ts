import { useRefreshToken } from '../lib/queryConfig';

export interface UseAuthRefreshReturn {
  refresh: () => Promise<string | undefined>;
  isLoading: boolean;
}

export const useAuthRefresh = (): UseAuthRefreshReturn => {
  const refreshMutation = useRefreshToken();

  const refresh = async (): Promise<string | undefined> => {
    try {
      const result = await refreshMutation.mutateAsync();
      return result.token;
    } catch {
      return undefined;
    }
  };

  return {
    refresh,
    isLoading: refreshMutation.isPending,
  };
};
