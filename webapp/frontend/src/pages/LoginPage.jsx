import React from 'react';
import LoginModal from '../components/LoginModal';

export default function LoginPage() {
  """Page wrapper for login flow with centered layout."""

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <LoginModal />
      </div>
    </div>
  );
}
