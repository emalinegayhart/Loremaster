import { useNavigate } from '@tanstack/react-router';
import { useAuth } from '../hooks/useAuth';

export const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate({ to: '/login' });
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="h-16 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center justify-between px-4 md:px-6">
      {/* Logo/Brand */}
      <button
        onClick={() => navigate({ to: '/' })}
        className="text-xl font-bold text-gray-900 dark:text-white hover:opacity-80 transition-opacity"
        aria-label="Loremaster Home"
      >
        Loremaster
      </button>

      {/* Logout Button - Only shows if logged in */}
      {user && (
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-medium transition-colors"
          aria-label="Logout"
        >
          Logout
        </button>
      )}
    </header>
  );
};
