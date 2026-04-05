import React from 'react';
import GoldButton from './GoldButton';
import './LoginModal.css';

export default function LoginModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="login-modal-backdrop" onClick={handleBackdropClick}>
      <div className="login-modal">
        <button className="login-modal-close" onClick={onClose} aria-label="Close login">
          ×
        </button>
        <GoldButton href="/api/auth/login" aria-label="Sign in with Google">
          Sign in with Google
        </GoldButton>
      </div>
    </div>
  );
}
