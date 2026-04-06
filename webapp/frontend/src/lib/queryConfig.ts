import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi, throwIfError } from './apiclient';
import type { User, LoginResponse, RefreshTokenResponse } from '../types/auth';

const AUTH_KEYS = {
  user: ['auth', 'user'] as const,
  login: ['auth', 'login'] as const,
  logout: ['auth', 'logout'] as const,
};

export const useGetUser = () => {
  return useQuery({
    queryKey: AUTH_KEYS.user,
    queryFn: async () => {
      const response = await fetchApi<User>('/api/auth/user');
      return throwIfError(response);
    },
    retry: false,
  });
};

export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await fetchApi<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      return throwIfError(response);
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token);
      queryClient.setQueryData(AUTH_KEYS.user, data.user);
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.user });
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await fetchApi<{ success: boolean }>('/api/auth/logout', {
        method: 'POST',
      });
      return throwIfError(response);
    },
    onSuccess: () => {
      localStorage.removeItem('auth_token');
      queryClient.removeQueries({ queryKey: AUTH_KEYS.user });
      queryClient.clear();
    },
  });
};

export const useRefreshToken = () => {
  return useMutation({
    mutationFn: async () => {
      const response = await fetchApi<RefreshTokenResponse>('/api/auth/refresh', {
        method: 'POST',
      });
      return throwIfError(response);
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token);
    },
  });
};
