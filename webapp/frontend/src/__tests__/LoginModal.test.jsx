import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoginModal from '../components/LoginModal';

describe('LoginModal', () => {
  it('renders LoginModal component', () => {
    render(<LoginModal />);
    expect(screen.getByRole('link')).toBeInTheDocument();
  });

  it('displays "Sign in with Google" text', () => {
    render(<LoginModal />);
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
  });

  it('button link href points to /api/auth/google', () => {
    render(<LoginModal />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/api/auth/google');
  });

  it('has accessible aria-label', () => {
    render(<LoginModal />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('aria-label', 'Sign in with Google');
  });

  it('has focus ring for keyboard navigation', () => {
    render(<LoginModal />);
    const link = screen.getByRole('link');
    expect(link.className).toContain('focus:ring');
  });

  it('displays branding text', () => {
    render(<LoginModal />);
    expect(screen.getByText('Loremaster')).toBeInTheDocument();
    expect(screen.getByText('World of Warcraft Lore Chat')).toBeInTheDocument();
  });

  it('contains Google logo SVG', () => {
    render(<LoginModal />);
    const svg = screen.getByRole('link').querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
