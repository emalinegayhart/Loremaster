import { Outlet } from '@tanstack/react-router';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { Header } from '../components/Header';

/**
 * Root layout component
 * Wraps all routes with common layout structure including ErrorBoundary for error handling,
 * Header for navigation and user info, and Outlet for child routes
 */
export const RootLayout = () => {
  return (
    <ErrorBoundary>
      <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900">
        <Header />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </ErrorBoundary>
  );
};
