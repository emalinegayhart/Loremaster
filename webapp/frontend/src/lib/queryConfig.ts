import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from './apiclient';
import type { User, LoginResponse, RefreshTokenResponse } from '../types/auth';

const AUTH_KEYS = {
  user: ['auth', 'user'] as const,
  login: ['auth', 'login'] as const,
  logout: ['auth', 'logout'] as const,
};

export const useGetUser = () => {
  return useQuery({
    queryKey: AUTH_KEYS.user,
    queryFn: () => fetchApi<User>('/api/auth/user'),
    retry: false,
  });
};

export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      fetchApi<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
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
    mutationFn: () =>
      fetchApi<{ success: boolean }>('/api/auth/logout', {
        method: 'POST',
      }),
    onSuccess: () => {
      localStorage.removeItem('auth_token');
      queryClient.removeQueries({ queryKey: AUTH_KEYS.user });
      queryClient.clear();
    },
  });
};

export const useRefreshToken = () => {
  return useMutation({
    mutationFn: () =>
      fetchApi<RefreshTokenResponse>('/api/auth/refresh', {
        method: 'POST',
      }),
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.token);
    },
  });
};
