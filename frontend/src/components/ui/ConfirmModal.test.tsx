import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmModal } from './ConfirmModal';

describe('ConfirmModal', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Delete Item',
    message: 'Are you sure?',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it('renders nothing when closed', () => {
    render(<ConfirmModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders title and message when open', () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = vi.fn();
    render(<ConfirmModal {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn();
    render(<ConfirmModal {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when overlay is clicked', () => {
    const onCancel = vi.fn();
    render(<ConfirmModal {...defaultProps} onCancel={onCancel} />);
    // The overlay is the element with class confirm-overlay
    const overlay = document.querySelector('.confirm-overlay')!;
    fireEvent.click(overlay);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('uses custom button labels', () => {
    render(
      <ConfirmModal
        {...defaultProps}
        confirmLabel="Delete"
        cancelLabel="Keep"
      />
    );
    expect(screen.getByText('Delete')).toBeInTheDocument();
    expect(screen.getByText('Keep')).toBeInTheDocument();
  });

  it('applies danger variant class to confirm button', () => {
    render(<ConfirmModal {...defaultProps} variant="danger" confirmLabel="Delete" />);
    const btn = screen.getByText('Delete');
    expect(btn).toHaveClass('confirm-btn--danger');
  });

  // Prompt mode tests
  it('renders text input in prompt mode', () => {
    render(
      <ConfirmModal
        {...defaultProps}
        promptPlaceholder="Enter name"
        promptDefault="My Protocol"
      />
    );
    const input = screen.getByPlaceholderText('Enter name') as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.value).toBe('My Protocol');
  });

  it('passes input value to onConfirm in prompt mode', () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmModal
        {...defaultProps}
        onConfirm={onConfirm}
        promptPlaceholder="Enter name"
        promptDefault="Test"
      />
    );
    fireEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalledWith('Test');
  });

  it('disables confirm when prompt input is empty', () => {
    render(
      <ConfirmModal
        {...defaultProps}
        promptPlaceholder="Enter name"
        promptDefault=""
      />
    );
    expect(screen.getByText('Confirm')).toBeDisabled();
  });

  it('calls onConfirm with undefined in non-prompt mode', () => {
    const onConfirm = vi.fn();
    render(<ConfirmModal {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalledWith(undefined);
  });
});
