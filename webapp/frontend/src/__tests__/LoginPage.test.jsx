import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoginPage from '../pages/LoginPage';

describe('LoginPage', () => {
  it('renders LoginPage component', () => {
    render(<LoginPage />);
    expect(screen.getByText('Loremaster')).toBeInTheDocument();
  });

  it('displays LoginModal within LoginPage', () => {
    render(<LoginPage />);
    expect(screen.getByRole('link')).toBeInTheDocument();
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
  });

  it('has centered layout container', () => {
    const { container } = render(<LoginPage />);
    const wrapper = container.querySelector('div');
    expect(wrapper.className).toContain('flex');
    expect(wrapper.className).toContain('items-center');
    expect(wrapper.className).toContain('justify-center');
  });

  it('has min-height of full screen', () => {
    const { container } = render(<LoginPage />);
    const wrapper = container.querySelector('div');
    expect(wrapper.className).toContain('min-h-screen');
  });

  it('has gradient background', () => {
    const { container } = render(<LoginPage />);
    const wrapper = container.querySelector('div');
    expect(wrapper.className).toContain('bg-gradient-to-br');
  });

  it('is responsive with padding', () => {
    const { container } = render(<LoginPage />);
    const wrapper = container.querySelector('div');
    expect(wrapper.className).toContain('p-4');
  });
});
