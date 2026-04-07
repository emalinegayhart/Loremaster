const getApiBaseUrl = (): string => {
  const url = import.meta.env.VITE_API_BASE_URL;
  
  if (!url && import.meta.env.DEV) {
    console.warn('VITE_API_BASE_URL not set, using default: http://localhost:8080');
    return 'http://localhost:8080';
  }
  
  if (!url) {
    throw new Error('VITE_API_BASE_URL environment variable is required in production');
  }
  
  return url;
};

export const API_BASE_URL = getApiBaseUrl();
