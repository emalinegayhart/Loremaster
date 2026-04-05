import React, { useEffect, useState } from 'react';
import './AuthCallbackPage.css';

export function AuthCallbackPageComponent({ initialError = null, initialLoading = true }) {
  const [error, setError] = useState(initialError);
  const [isLoading, setIsLoading] = useState(initialLoading);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const errorParam = params.get('error');
    
    const hasUrlParams = code || state || errorParam;
    
    if (!hasUrlParams) return;

    const handleCallback = async () => {
      try {
        if (errorParam) {
          setError(errorParam);
          setIsLoading(false);
          return;
        }

        if (!code || !state) {
          setError('Missing authorization code or state');
          setIsLoading(false);
          return;
        }

        await new Promise(resolve => setTimeout(resolve, 2000));

        window.location.href = '/editor';
      } catch (err) {
        setError(err.message || 'Authentication failed');
        setIsLoading(false);
      }
    };

    handleCallback();
  }, []);

  if (error) {
    return (
      <div className="auth-callback-container">
        <div className="auth-callback-card">
          <h2 className="auth-callback-heading">Authentication Failed</h2>
          <p className="auth-callback-error">{error}</p>
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
  return <AuthCallbackPageComponent />;
}
