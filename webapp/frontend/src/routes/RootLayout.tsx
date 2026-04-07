import { Outlet } from '@tanstack/react-router';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { Header } from '../components/Header';

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
