import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo } from 'react';
import { fetchApi } from '../lib/apiclient';

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

      return fetchApi('/api/auth/callback', {
        method: 'POST',
        body: JSON.stringify({ code: urlParams.code, state: urlParams.state }),
      });
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
