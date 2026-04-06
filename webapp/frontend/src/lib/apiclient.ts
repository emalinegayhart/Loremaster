import { apiConfig } from './env';
import type { ApiError } from '../types/auth';

export const throwIfError = <T>(response: T | ApiError): T => {
  if (response && typeof response === 'object' && 'status' in response && 'detail' in response) {
    throw response as ApiError;
  }
  return response as T;
};

const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

const removeAuthToken = (): void => {
  localStorage.removeItem('auth_token');
};

let refreshPromise: Promise<boolean> | null = null;

const refreshAuthToken = async (): Promise<boolean> => {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${apiConfig.baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        const data = await response.json();
        setAuthToken(data.token);
        return true;
      }

      removeAuthToken();
      return false;
    } catch (error) {
      removeAuthToken();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

interface FetchOptions extends RequestInit {}

export const fetchApi = async <T = unknown>(
  url: string,
  options: FetchOptions = {}
): Promise<T | ApiError> => {
  const fullUrl = url.startsWith('http') ? url : `${apiConfig.baseUrl}${url}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const token = getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(fullUrl, {
    ...options,
    headers,
  });

  if (response.status === 401 && token) {
    const refreshed = await refreshAuthToken();
    if (refreshed) {
      return fetchApi<T>(url, options);
    }
  }

  if (!response.ok) {
    const error: ApiError = {
      detail: response.statusText,
      status: response.status,
    };

    try {
      const json = await response.json();
      error.detail = json.detail || json.message || error.detail;
    } catch {
      // Silent catch
    }

    return error;
  }

  const text = await response.text();
  if (!text) return null as T;

  try {
    return JSON.parse(text);
  } catch {
    return text as T;
  }
};
