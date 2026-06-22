import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('renders title and default icon', () => {
    render(<EmptyState title="No items found" />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
    expect(screen.getByText('📋')).toBeInTheDocument();
  });

  it('renders custom icon', () => {
    render(<EmptyState title="No users" icon="👤" />);
    expect(screen.getByText('👤')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(<EmptyState title="Title" description="Some description text" />);
    expect(screen.getByText('Some description text')).toBeInTheDocument();
  });

  it('renders action button and calls onAction when provided', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="Title"
        actionLabel="Create Item"
        onAction={handleAction}
      />
    );
    
    const button = screen.getByRole('button', { name: /create item/i });
    expect(button).toBeInTheDocument();
    
    fireEvent.click(button);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('renders children', () => {
    render(
      <EmptyState title="Title">
        <div data-testid="custom-child">Child Content</div>
      </EmptyState>
    );
    expect(screen.getByTestId('custom-child')).toBeInTheDocument();
    expect(screen.getByText('Child Content')).toBeInTheDocument();
  });
});
