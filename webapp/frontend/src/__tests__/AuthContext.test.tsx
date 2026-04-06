import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { AuthProvider, useAuthContext } from '../contexts/AuthContext';
import * as useAuthModule from '../hooks/useAuth';

// Mock useAuth hook
vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('provides auth state to children', (): void => {
    const mockUser = { id: '123', email: 'test@example.com', username: 'testuser' };
    const mockLogout = vi.fn();

    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      user: mockUser,
      isLoading: false,
      isError: false,
      logout: mockLogout,
    });

    const TestComponent = (): React.ReactNode => {
      const { user, isLoading, isError } = useAuthContext();
      return (
        <div>
          <div>User: {user?.username}</div>
          <div>Loading: {isLoading.toString()}</div>
          <div>Error: {isError.toString()}</div>
        </div>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByText('User: testuser')).toBeInTheDocument();
    expect(screen.getByText('Loading: false')).toBeInTheDocument();
    expect(screen.getByText('Error: false')).toBeInTheDocument();
  });

  it('throws error when useAuthContext called outside provider', (): void => {
    const TestComponent = (): React.ReactNode => {
      useAuthContext();
      return <div>Test</div>;
    };

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuthContext must be used within an AuthProvider');
  });

  it('provides logout function', (): void => {
    const mockLogout = vi.fn();

    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      user: undefined,
      isLoading: false,
      isError: false,
      logout: mockLogout,
    });

    const TestComponent = (): React.ReactNode => {
      const { logout } = useAuthContext();
      return (
        <button onClick={logout} data-testid="logout-btn">
          Logout
        </button>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const button = screen.getByTestId('logout-btn');
    expect(button).toBeInTheDocument();
  });

  it('handles loading state correctly', (): void => {
    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      user: undefined,
      isLoading: true,
      isError: false,
      logout: vi.fn(),
    });

    const TestComponent = (): React.ReactNode => {
      const { isLoading } = useAuthContext();
      return <div>{isLoading ? 'Loading...' : 'Ready'}</div>;
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles error state correctly', (): void => {
    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      user: undefined,
      isLoading: false,
      isError: true,
      logout: vi.fn(),
    });

    const TestComponent = (): React.ReactNode => {
      const { isError } = useAuthContext();
      return <div>{isError ? 'Error occurred' : 'No error'}</div>;
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });
});
