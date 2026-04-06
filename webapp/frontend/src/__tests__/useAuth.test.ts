import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useAuth } from '../hooks/useAuth';
import * as queryConfig from '../lib/queryConfig';

// Mock the queryConfig hooks
vi.mock('../lib/queryConfig', () => ({
  useGetUser: vi.fn(),
  useLogout: vi.fn(),
}));

describe('useAuth', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient();
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  it('returns user data when loaded', async (): Promise<void> => {
    const mockUser = { id: '123', email: 'test@example.com', username: 'testuser' };

    vi.mocked(queryConfig.useGetUser).mockReturnValue({
      data: mockUser,
      isLoading: false,
      isError: false,
    } as any);

    vi.mocked(queryConfig.useLogout).mockReturnValue({
      mutateAsync: vi.fn(),
    } as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('returns isLoading when fetching user', (): void => {
    vi.mocked(queryConfig.useGetUser).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any);

    vi.mocked(queryConfig.useLogout).mockReturnValue({
      mutateAsync: vi.fn(),
    } as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBeUndefined();
  });

  it('returns isError when fetch fails', (): void => {
    vi.mocked(queryConfig.useGetUser).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as any);

    vi.mocked(queryConfig.useLogout).mockReturnValue({
      mutateAsync: vi.fn(),
    } as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isError).toBe(true);
  });

  it('logout function calls mutateAsync', async (): Promise<void> => {
    const mockLogout = vi.fn().mockResolvedValue(undefined);

    vi.mocked(queryConfig.useGetUser).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as any);

    vi.mocked(queryConfig.useLogout).mockReturnValue({
      mutateAsync: mockLogout,
    } as any);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await result.current.logout();

    expect(mockLogout).toHaveBeenCalled();
  });
});
