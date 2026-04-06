import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginModal from '../components/LoginModal';

describe('LoginModal', () => {
  it('does not render when isOpen is false', (): void => {
    const { container } = render(<LoginModal isOpen={false} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders when isOpen is true', (): void => {
    render(<LoginModal isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
  });

  it('displays "Sign in with Google" text', (): void => {
    render(<LoginModal isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
  });

  it('button link href points to /api/auth/google', (): void => {
    render(<LoginModal isOpen={true} onClose={vi.fn()} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/api/auth/google');
  });

  it('has accessible aria-label on button', (): void => {
    render(<LoginModal isOpen={true} onClose={vi.fn()} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('aria-label', 'Sign in with Google');
  });

  it('has close button with aria-label', (): void => {
    render(<LoginModal isOpen={true} onClose={vi.fn()} />);
    const closeBtn = screen.getByRole('button', { name: 'Close login' });
    expect(closeBtn).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async (): Promise<void> => {
    const onClose = vi.fn();
    render(<LoginModal isOpen={true} onClose={onClose} />);
    const closeBtn = screen.getByRole('button', { name: 'Close login' });
    await userEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when backdrop is clicked', async (): Promise<void> => {
    const onClose = vi.fn();
    const { container } = render(<LoginModal isOpen={true} onClose={onClose} />);
    const backdrop = container.querySelector('.login-modal-backdrop');
    await userEvent.click(backdrop);
    expect(onClose).toHaveBeenCalled();
  });
});
