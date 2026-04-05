import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AuthCallbackPage, { AuthCallbackPageContent } from '../pages/AuthCallbackPage';
import { getHumanReadableErrorMessage } from '../utils/errorMessages';

describe('AuthCallbackPage', () => {
  let queryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  it('displays loading spinner', () => {
    render(<AuthCallbackPageContent isLoading={true} error={null} />);
    expect(screen.getByText('Signing you in...')).toBeInTheDocument();
  });

  it('shows spinner element', () => {
    const { container } = render(<AuthCallbackPageContent isLoading={true} error={null} />);
    const spinner = container.querySelector('.auth-callback-spinner');
    expect(spinner).toBeInTheDocument();
  });

  it('displays human readable error message for access_denied', () => {
    render(<AuthCallbackPageContent isLoading={false} error="access_denied" />);
    expect(screen.getByText('You denied access. Please try again.')).toBeInTheDocument();
  });

  it('displays human readable error message for invalid_grant', () => {
    render(<AuthCallbackPageContent isLoading={false} error="invalid_grant" />);
    expect(screen.getByText('Your session expired. Please try again.')).toBeInTheDocument();
  });

  it('shows retry link on error', () => {
    render(<AuthCallbackPageContent isLoading={false} error="invalid_grant" />);
    const retryLink = screen.getByText('Back to Login');
    expect(retryLink).toHaveAttribute('href', '/login');
  });

  it('displays human readable error message for missing code', () => {
    render(<AuthCallbackPageContent isLoading={false} error="Missing authorization code or state" />);
    expect(screen.getByText('Authentication failed. Please try again.')).toBeInTheDocument();
  });

  it('displays human readable error message for server_error', () => {
    render(<AuthCallbackPageContent isLoading={false} error="server_error" />);
    expect(screen.getByText('Server error. Please try again.')).toBeInTheDocument();
  });

  it('has accessible error heading', () => {
    render(<AuthCallbackPageContent isLoading={false} error="server_error" />);
    expect(screen.getByText('Authentication Failed')).toBeInTheDocument();
  });

  it('retry link is clickable', () => {
    render(<AuthCallbackPageContent isLoading={false} error="access_denied" />);
    const retryLink = screen.getByText('Back to Login');
    expect(retryLink).toBeVisible();
    expect(retryLink.tagName).toBe('A');
  });
});
