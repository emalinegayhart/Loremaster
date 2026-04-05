export const getApiBaseUrl = (): string => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL;
  
  if (!baseUrl) {
    throw new Error('Missing required environment variable: VITE_API_BASE_URL');
  }
  
  return baseUrl;
};

export const apiConfig = {
  baseUrl: getApiBaseUrl(),
} as const;
