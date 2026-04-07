import LoginModal from '../components/LoginModal';

/**
 * Login page component
 * Displays the login modal for user authentication
 * Protected by publicGuard - redirects to /editor if already authenticated
 */
export const LoginPage = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-white dark:bg-gray-900">
      <LoginModal />
    </div>
  );
};
