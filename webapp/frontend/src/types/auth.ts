export interface User {
  id: string;
  email: string;
  username: string;
  profile_picture_url?: string;
  created_at: string;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isError: boolean;
  logout: () => void;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isError: boolean;
  error: string | null;
}

export interface LoginResponse {
  user: User;
  token: string;
}

export interface RefreshTokenResponse {
  token: string;
}

export interface AuthCallbackResponse {
  success: boolean;
  user?: User;
  message?: string;
}

export interface ApiError {
  detail: string;
  status: number;
}
