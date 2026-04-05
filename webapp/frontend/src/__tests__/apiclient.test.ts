import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fetchApi } from '../lib/apiclient';

describe('fetchApi', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('makes GET request correctly', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({ data: 'test' })),
      } as Response)
    );

    const result = await fetchApi('/api/test');
    expect(result).toEqual({ data: 'test' });
  });

  it('makes POST request with body', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({ success: true })),
      } as Response)
    );

    await fetchApi('/api/test', {
      method: 'POST',
      body: JSON.stringify({ key: 'value' }),
    });

    const call = (global.fetch as any).mock.calls[0];
    expect(call[1].method).toBe('POST');
  });

  it('adds Authorization header with auth token', async () => {
    localStorage.setItem('auth_token', 'test-token');

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve('{}'),
      } as Response)
    );

    await fetchApi('/api/test');

    const call = (global.fetch as any).mock.calls[0];
    expect(call[1].headers.Authorization).toBe('Bearer test-token');
  });

  it('handles 401 and triggers refresh', async () => {
    localStorage.setItem('auth_token', 'old-token');

    let callCount = 0;
    global.fetch = vi.fn(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          text: () => Promise.resolve('{"detail": "Token expired"}'),
          json: () => Promise.resolve({ detail: 'Token expired' }),
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve('{"success": true}'),
      } as Response);
    });

    const result = await fetchApi('/api/test');
    expect(result).toEqual({ success: true });
  });

  it('removes token on failed refresh', async () => {
    localStorage.setItem('auth_token', 'expired-token');

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: () => Promise.resolve('{"detail": "Unauthorized"}'),
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      } as Response)
    );

    try {
      await fetchApi('/api/test');
    } catch (error) {
      // Expected to throw
    }

    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('constructs full URL from relative path', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve('{}'),
      } as Response)
    );

    await fetchApi('/api/test');

    const call = (global.fetch as any).mock.calls[0];
    expect(call[0]).toContain('/api/test');
  });

  it('throws on error response', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: () => Promise.resolve('{"detail": "Server error"}'),
        json: () => Promise.resolve({ detail: 'Server error' }),
      } as Response)
    );

    await expect(fetchApi('/api/test')).rejects.toThrow();
  });

  it('parses JSON response', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({ name: 'test', id: 123 })),
      } as Response)
    );

    const result = await fetchApi('/api/test');
    expect(result).toEqual({ name: 'test', id: 123 });
  });

  it('handles empty response body', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        text: () => Promise.resolve(''),
      } as Response)
    );

    const result = await fetchApi('/api/test');
    expect(result).toBeNull();
  });
});
