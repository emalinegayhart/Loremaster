import { useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useGetUser } from '../lib/queryConfig';

/**
 * Auth callback page
 * Handles OAuth callback from Google
 * Backend sets auth cookie, this page verifies auth and redirects to /editor
 */
export const AuthCallbackPage = () => {
  const navigate = useNavigate();
  const { data: user, isLoading, isError } = useGetUser();

  useEffect(() => {
    // If user is loaded, redirect to editor
    if (!isLoading && user) {
      navigate({ to: '/editor' });
    }
  }, [user, isLoading, navigate]);

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white dark:bg-gray-900">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
            Authentication Failed
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            There was an error during authentication. Please try again.
          </p>
          <a
            href="/login"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            Back to Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-white dark:bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Signing you in...</p>
      </div>
    </div>
  );
};
