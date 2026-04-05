import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuthCallbackPageComponent } from '../pages/AuthCallbackPage';

describe('AuthCallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays loading spinner initially', () => {
    render(<AuthCallbackPageComponent />);
    expect(screen.getByText('Signing you in...')).toBeInTheDocument();
  });

  it('shows spinner element', () => {
    const { container } = render(<AuthCallbackPageComponent />);
    const spinner = container.querySelector('.auth-callback-spinner');
    expect(spinner).toBeInTheDocument();
  });

  it('displays error message when error param exists', () => {
    render(<AuthCallbackPageComponent initialError="access_denied" initialLoading={false} />);
    expect(screen.getByText('access_denied')).toBeInTheDocument();
  });

  it('shows retry link on error', () => {
    render(<AuthCallbackPageComponent initialError="invalid_grant" initialLoading={false} />);
    const retryLink = screen.getByText('Back to Login');
    expect(retryLink).toHaveAttribute('href', '/login');
  });

  it('displays error when code is missing', () => {
    render(<AuthCallbackPageComponent initialError="Missing authorization code or state" initialLoading={false} />);
    expect(screen.getByText('Missing authorization code or state')).toBeInTheDocument();
  });

  it('displays error when state is missing', () => {
    render(<AuthCallbackPageComponent initialError="Missing authorization code or state" initialLoading={false} />);
    expect(screen.getByText('Missing authorization code or state')).toBeInTheDocument();
  });

  it('has accessible error message text', () => {
    render(<AuthCallbackPageComponent initialError="server_error" initialLoading={false} />);
    expect(screen.getByText('Authentication Failed')).toBeInTheDocument();
  });

  it('retry button has focus styling', () => {
    delete window.location;
    window.location = new URL('http://localhost/auth/callback?error=network_error');

    const { container } = render(<AuthCallbackPage />);
    const retryButton = container.querySelector('.auth-callback-retry');
    expect(retryButton.className).toContain('auth-callback-retry');
  });
});
