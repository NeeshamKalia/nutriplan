import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ToastProvider, useToast } from '../../contexts/ToastContext';

/** Helper component to trigger toasts from tests. */
function ToastTrigger() {
  const toast = useToast();
  return (
    <div>
      <button onClick={() => toast.success('Done', 'Item saved')}>Success</button>
      <button onClick={() => toast.error('Oops', 'Something broke')}>Error</button>
      <button onClick={() => toast.warning('Warning', 'Check this')}>Warning</button>
      <button onClick={() => toast.info('FYI', 'Just so you know')}>Info</button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <ToastTrigger />
    </ToastProvider>
  );
}

describe('ToastContext', () => {
  it('renders success toast with title and message', () => {
    renderWithProvider();
    fireEvent.click(screen.getByText('Success'));
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('Item saved')).toBeInTheDocument();
  });

  it('renders error toast', () => {
    renderWithProvider();
    fireEvent.click(screen.getByText('Error'));
    expect(screen.getByText('Oops')).toBeInTheDocument();
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });

  it('renders warning toast', () => {
    renderWithProvider();
    fireEvent.click(screen.getByText('Warning'));
    expect(screen.getByText('Check this')).toBeInTheDocument();
  });

  it('renders info toast', () => {
    renderWithProvider();
    fireEvent.click(screen.getByText('Info'));
    expect(screen.getByText('Just so you know')).toBeInTheDocument();
  });

  it('dismisses toast when close button is clicked', () => {
    vi.useFakeTimers();
    renderWithProvider();
    fireEvent.click(screen.getByText('Success'));
    expect(screen.getByText('Done')).toBeInTheDocument();

    const closeBtn = screen.getByLabelText('Dismiss notification');
    fireEvent.click(closeBtn);

    // Advance past the exit animation timeout (200ms) in removeToast
    act(() => { vi.advanceTimersByTime(250); });
    expect(screen.queryByText('Done')).not.toBeInTheDocument();
    vi.useRealTimers();
  });

  it('can show multiple toasts at once', () => {
    renderWithProvider();
    fireEvent.click(screen.getByText('Success'));
    fireEvent.click(screen.getByText('Error'));
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('Oops')).toBeInTheDocument();
  });

  it('throws when used outside provider', () => {
    // Suppress console.error for expected error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<ToastTrigger />)).toThrow(
      'useToast must be used within a ToastProvider'
    );
    spy.mockRestore();
  });
});
