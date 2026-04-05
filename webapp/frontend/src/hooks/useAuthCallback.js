import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';

export function useAuthCallback() {
  const urlParams = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return {
      code: params.get('code'),
      state: params.get('state'),
      errorParam: params.get('error'),
    };
  }, []);

  const query = useQuery({
    queryKey: ['authCallback', urlParams.code, urlParams.state],
    queryFn: async () => {
      if (urlParams.errorParam) {
        throw new Error(urlParams.errorParam);
      }

      if (!urlParams.code || !urlParams.state) {
        throw new Error('Missing authorization code or state');
      }

      const response = await fetch('/api/auth/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: urlParams.code, state: urlParams.state }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Authentication failed');
      }

      return response.json();
    },
    enabled: !urlParams.errorParam && (!!urlParams.code || !!urlParams.state),
    retry: false,
  });

  useEffect(() => {
    if (query.isSuccess) {
      window.location.href = '/editor';
    }
  }, [query.isSuccess]);

  return {
    isLoading: query.isLoading,
    error: query.error?.message || null,
    isSuccess: query.isSuccess,
  };
}
