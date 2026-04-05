import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AuthCallbackPage, { AuthCallbackPageContent } from '../pages/AuthCallbackPage';

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

  it('displays error message when error exists', () => {
    render(<AuthCallbackPageContent isLoading={false} error="access_denied" />);
    expect(screen.getByText('access_denied')).toBeInTheDocument();
  });

  it('shows retry link on error', () => {
    render(<AuthCallbackPageContent isLoading={false} error="invalid_grant" />);
    const retryLink = screen.getByText('Back to Login');
    expect(retryLink).toHaveAttribute('href', '/login');
  });

  it('displays error message for missing code', () => {
    render(<AuthCallbackPageContent isLoading={false} error="Missing authorization code or state" />);
    expect(screen.getByText('Missing authorization code or state')).toBeInTheDocument();
  });

  it('displays error message for missing state', () => {
    render(<AuthCallbackPageContent isLoading={false} error="Missing authorization code or state" />);
    expect(screen.getByText('Missing authorization code or state')).toBeInTheDocument();
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
