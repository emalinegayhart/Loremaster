import React from 'react';
import GoldButton from './GoldButton';
import './LoginModal.css';

export default function LoginModal() {
  return (
    <div className="login-modal">
      <GoldButton href="/api/auth/google" aria-label="Sign in with Google">
        Sign in with Google
      </GoldButton>
    </div>
  );
}
