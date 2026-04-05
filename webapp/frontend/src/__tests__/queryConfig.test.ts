import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useGetUser, useLogin, useLogout, useRefreshToken } from '../lib/queryConfig';
import { queryClient } from '../lib/queryClient';

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('Auth Hooks', () => {
  beforeEach(() => {
    queryClient.clear();
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('useGetUser', () => {
    it('has correct query key', () => {
      const { result } = renderHook(() => useGetUser(), { wrapper });
      expect(result.current.queryKey).toEqual(['auth', 'user']);
    });

    it('has retry disabled', () => {
      const { result } = renderHook(() => useGetUser(), { wrapper });
      expect(result.current.retry).toBe(false);
    });
  });

  describe('useLogin', () => {
    it('stores token on successful login', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () =>
            Promise.resolve(
              JSON.stringify({
                token: 'test-token',
                user: { id: '1', email: 'test@example.com', username: 'test', created_at: new Date().toISOString() },
              })
            ),
        } as Response)
      );

      const { result } = renderHook(() => useLogin(), { wrapper });

      result.current.mutate({ email: 'test@example.com', password: 'password' });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(localStorage.getItem('auth_token')).toBe('test-token');
    });

    it('invalidates user query on successful login', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () =>
            Promise.resolve(
              JSON.stringify({
                token: 'test-token',
                user: { id: '1', email: 'test@example.com', username: 'test', created_at: new Date().toISOString() },
              })
            ),
        } as Response)
      );

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useLogin(), { wrapper });

      result.current.mutate({ email: 'test@example.com', password: 'password' });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });
  });

  describe('useLogout', () => {
    it('removes token on logout', async () => {
      localStorage.setItem('auth_token', 'test-token');

      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(JSON.stringify({ success: true })),
        } as Response)
      );

      const { result } = renderHook(() => useLogout(), { wrapper });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(localStorage.getItem('auth_token')).toBeNull();
    });

    it('clears all queries on logout', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(JSON.stringify({ success: true })),
        } as Response)
      );

      const clearSpy = vi.spyOn(queryClient, 'clear');
      const { result } = renderHook(() => useLogout(), { wrapper });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(clearSpy).toHaveBeenCalled();
    });
  });

  describe('useRefreshToken', () => {
    it('stores new token on refresh', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          text: () => Promise.resolve(JSON.stringify({ token: 'new-token' })),
        } as Response)
      );

      const { result } = renderHook(() => useRefreshToken(), { wrapper });

      result.current.mutate();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(localStorage.getItem('auth_token')).toBe('new-token');
    });
  });
});
