import React from 'react';
import { API_BASE_URL } from '../lib/env';
import GoldButton from './GoldButton';
import './LoginModal.css';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps): React.ReactNode {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>): void => {
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
        <GoldButton href={`${API_BASE_URL}/api/auth/google`} aria-label="Sign in with Google">
          Sign in with Google
        </GoldButton>
      </div>
    </div>
  );
}
