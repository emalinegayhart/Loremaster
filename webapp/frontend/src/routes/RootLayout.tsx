import { Outlet } from '@tanstack/react-router';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { Header } from '../components/Header';
import { useAuth } from '../hooks/useAuth';

export const RootLayout = () => {
  const { user } = useAuth();

  return (
    <ErrorBoundary>
      <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900">
        {user && <Header />}
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </ErrorBoundary>
  );
};
