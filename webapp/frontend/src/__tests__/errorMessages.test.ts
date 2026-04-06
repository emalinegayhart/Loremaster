import { describe, it, expect } from 'vitest';
import { getHumanReadableErrorMessage, errorMessageMap } from '../utils/errorMessages';

describe('errorMessages', () => {
  it('maps access_denied to human readable message', (): void => {
    const message: string = getHumanReadableErrorMessage('access_denied');
    expect(message).toBe('You denied access. Please try again.');
  });

  it('maps invalid_grant to human readable message', (): void => {
    const message: string = getHumanReadableErrorMessage('invalid_grant');
    expect(message).toBe('Your session expired. Please try again.');
  });

  it('maps server_error to human readable message', (): void => {
    const message: string = getHumanReadableErrorMessage('server_error');
    expect(message).toBe('Server error. Please try again.');
  });

  it('maps temporarily_unavailable to human readable message', (): void => {
    const message: string = getHumanReadableErrorMessage('temporarily_unavailable');
    expect(message).toBe('Service temporarily unavailable. Please try again.');
  });

  it('handles unknown error codes with generic message', (): void => {
    const message: string = getHumanReadableErrorMessage('unknown_error_code');
    expect(message).toContain('Authentication error: unknown_error_code');
  });

  it('all mapped errors are human readable', (): void => {
    Object.entries(errorMessageMap).forEach(([code, message]): void => {
      expect(message).toBeTruthy();
      expect(message.length).toBeGreaterThan(0);
      expect(message).toContain('Please try again');
    });
  });
});
