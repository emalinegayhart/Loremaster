import { useNavigate } from '@tanstack/react-router';

/**
 * 404 Not Found page
 * Catch-all for undefined routes
 */
export const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-center min-h-screen bg-white dark:bg-gray-900">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4">404</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">Page not found</p>
        <button
          onClick={() => navigate({ to: '/' })}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
        >
          Go Home
        </button>
      </div>
    </div>
  );
};
