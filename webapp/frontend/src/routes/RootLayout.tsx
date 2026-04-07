import { Outlet } from '@tanstack/react-router';

/**
 * Root layout component
 * Wraps all routes with common layout structure
 * TODO: Add Header component (PR-AUTH-9)
 * TODO: Add ErrorBoundary wrapper (PR-AUTH-9)
 */
export const RootLayout = () => {
  return (
    <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900">
      {/* TODO: <Header /> component will be added here (PR-AUTH-9) */}
      
      {/* Main content outlet */}
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
};
