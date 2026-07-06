/**
 * Reusable confirmation modal — replaces browser confirm() and prompt() dialogs.
 * Supports both simple yes/no confirmations and text-input prompts.
 */

import React, { useState, useRef, useEffect } from 'react';
import './ConfirmModal.css';

export interface ConfirmModalProps {
  /** Whether the modal is visible */
  isOpen: boolean;
  /** Title shown at the top */
  title: string;
  /** Message body */
  message: string;
  /** Label for the confirm button (default: "Confirm") */
  confirmLabel?: string;
  /** Label for the cancel button (default: "Cancel") */
  cancelLabel?: string;
  /** Visual style of confirm button */
  variant?: 'primary' | 'danger';
  /** If set, shows a text input with this placeholder */
  promptPlaceholder?: string;
  /** Default value for the prompt input */
  promptDefault?: string;
  /** Called when user confirms. For prompts, receives the input value. */
  onConfirm: (value?: string) => void;
  /** Called when user cancels */
  onCancel: () => void;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'primary',
  promptPlaceholder,
  promptDefault = '',
  onConfirm,
  onCancel,
}) => {
  const [inputValue, setInputValue] = useState(promptDefault);
  const inputRef = useRef<HTMLInputElement>(null);
  const isPrompt = promptPlaceholder !== undefined;

  // Focus input when opening a prompt modal
  useEffect(() => {
    if (isOpen && isPrompt && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isOpen, isPrompt]);

  // Reset input when opening
  useEffect(() => {
    if (isOpen) {
      setInputValue(promptDefault);
    }
  }, [isOpen, promptDefault]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm(isPrompt ? inputValue : undefined);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleConfirm();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div
        className="confirm-dialog"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
      >
        <h3 id="confirm-title" className="confirm-title">{title}</h3>
        <p className="confirm-message">{message}</p>

        {isPrompt && (
          <input
            ref={inputRef}
            type="text"
            className="confirm-input"
            placeholder={promptPlaceholder}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
        )}

        <div className="confirm-actions">
          <button className="confirm-btn confirm-btn--cancel" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            className={`confirm-btn confirm-btn--${variant}`}
            onClick={handleConfirm}
            disabled={isPrompt && !inputValue.trim()}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
