import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResourceSidebar from '../components/ResourceSidebar';

describe('ResourceSidebar', () => {
  it('renders Learn 2 Prompt button', () => {
    render(<ResourceSidebar onLearnPromptClick={vi.fn()} />);
    expect(screen.getByText('Learn 2 Prompt')).toBeInTheDocument();
  });

  it('renders resource links', () => {
    render(<ResourceSidebar onLearnPromptClick={vi.fn()} />);
    expect(screen.getByText('Raidbots')).toBeInTheDocument();
    expect(screen.getByText('Icy Veins')).toBeInTheDocument();
    expect(screen.getByText('Wowhead')).toBeInTheDocument();
  });

  it('renders GitHub link', () => {
    render(<ResourceSidebar onLearnPromptClick={vi.fn()} />);
    const githubLink = screen.getByRole('link', { name: /github/i });
    expect(githubLink).toBeInTheDocument();
    expect(githubLink).toHaveAttribute('href', 'https://github.com/emalinegayhart/loremaster');
  });

  it('calls onLearnPromptClick when button is clicked', () => {
    const onLearnPromptClick = vi.fn();
    render(<ResourceSidebar onLearnPromptClick={onLearnPromptClick} />);
    const button = screen.getByRole('button', { name: 'Learn to Prompt' });
    button.click();
    expect(onLearnPromptClick).toHaveBeenCalledTimes(1);
  });

  it('Learn 2 Prompt button has aria-label', () => {
    render(<ResourceSidebar onLearnPromptClick={vi.fn()} />);
    const button = screen.getByRole('button', { name: 'Learn to Prompt' });
    expect(button).toHaveAttribute('aria-label', 'Learn to Prompt');
  });

  it('resource links have target="_blank"', () => {
    render(<ResourceSidebar onLearnPromptClick={vi.fn()} />);
    const raidbotsLink = screen.getByText('Raidbots').closest('a');
    expect(raidbotsLink).toHaveAttribute('target', '_blank');
    expect(raidbotsLink).toHaveAttribute('rel', 'noreferrer');
  });

  it('all resource links have data-tooltip', () => {
    render(<ResourceSidebar onLearnPromptClick={vi.fn()} />);
    const raidbotsLink = screen.getByText('Raidbots').closest('a');
    expect(raidbotsLink).toHaveAttribute('data-tooltip');
  });
});
