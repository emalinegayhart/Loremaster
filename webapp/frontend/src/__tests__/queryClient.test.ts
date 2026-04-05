import { describe, it, expect } from 'vitest';
import { queryClient } from '../lib/queryClient';

describe('queryClient', () => {
  it('is initialized with correct defaults', () => {
    const defaultOptions = queryClient.getDefaultOptions();

    expect(defaultOptions.queries).toBeDefined();
    expect(defaultOptions.mutations).toBeDefined();
  });

  it('has 5 minute stale time', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.staleTime).toBe(5 * 60 * 1000);
  });

  it('has 10 minute cache time', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.gcTime).toBe(10 * 60 * 1000);
  });

  it('has retry set to 3 for queries', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.retry).toBe(3);
  });

  it('has retry set to 1 for mutations', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.mutations?.retry).toBe(1);
  });

  it('refetchOnWindowFocus is enabled', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.refetchOnWindowFocus).toBe(true);
  });

  it('refetchOnMount is enabled', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.refetchOnMount).toBe(true);
  });

  it('refetchOnReconnect is enabled', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    expect(defaultOptions.queries?.refetchOnReconnect).toBe(true);
  });

  it('has exponential backoff retry delay', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    const retryDelay = defaultOptions.queries?.retryDelay as (attemptIndex: number) => number;

    expect(retryDelay(0)).toBe(1000);
    expect(retryDelay(1)).toBe(2000);
    expect(retryDelay(2)).toBe(4000);
    expect(retryDelay(3)).toBe(8000);
  });

  it('caps retry delay at 30 seconds', () => {
    const defaultOptions = queryClient.getDefaultOptions();
    const retryDelay = defaultOptions.queries?.retryDelay as (attemptIndex: number) => number;

    expect(retryDelay(10)).toBe(30000);
  });
});
