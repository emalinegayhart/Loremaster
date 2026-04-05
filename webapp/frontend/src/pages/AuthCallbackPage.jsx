import React from 'react';
import { useAuthCallback } from '../hooks/useAuthCallback';
import { getHumanReadableErrorMessage } from '../utils/errorMessages';
import './AuthCallbackPage.css';

export function AuthCallbackPageContent({ isLoading, error }) {
  if (error) {
    const humanReadableMessage = getHumanReadableErrorMessage(error);
    return (
      <div className="auth-callback-container">
        <div className="auth-callback-card">
          <h2 className="auth-callback-heading">Authentication Failed</h2>
          <p className="auth-callback-error">{humanReadableMessage}</p>
          <a href="/login" className="auth-callback-retry">
            Back to Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-callback-container">
      <div className="auth-callback-card">
        <div className="auth-callback-spinner"></div>
        <h2 className="auth-callback-heading">Signing you in...</h2>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  const { isLoading, error } = useAuthCallback();
  return <AuthCallbackPageContent isLoading={isLoading} error={error} />;
}
