import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';

// Mock console to avoid cluttering test output
const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

describe('ErrorBoundary', () => {
  beforeEach(() => {
    consoleSpy.mockClear();
  });

  it('renders children when there are no errors', (): void => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Safe content')).toBeInTheDocument();
  });

  it('catches React errors and displays fallback UI', (): void => {
    const ThrowError = (): React.ReactNode => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('⚠️ Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
  });

  it('displays error details in development mode', (): void => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    const ThrowError = (): React.ReactNode => {
      throw new Error('Test error message');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Error Details')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it('displays Try Again button', (): void => {
    const ThrowError = (): React.ReactNode => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
  });

  it('recovers from error when Try Again is clicked', async (): Promise<void> => {
    const user = userEvent.setup();
    let shouldThrow = true;

    const ConditionalError = (): React.ReactNode => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>Recovered content</div>;
    };

    const { rerender } = render(
      <ErrorBoundary>
        <ConditionalError />
      </ErrorBoundary>
    );

    expect(screen.getByText('⚠️ Something went wrong')).toBeInTheDocument();

    shouldThrow = false;
    const tryAgainBtn = screen.getByRole('button', { name: 'Try Again' });
    await user.click(tryAgainBtn);

    rerender(
      <ErrorBoundary>
        <ConditionalError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Recovered content')).toBeInTheDocument();
  });

  it('logs errors to console in development', (): void => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    const ThrowError = (): React.ReactNode => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(consoleSpy).toHaveBeenCalled();

    process.env.NODE_ENV = originalEnv;
  });
});
