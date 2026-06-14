import { type InputHTMLAttributes, type TextareaHTMLAttributes, forwardRef, useId } from 'react';
import './Input.css';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = '', id: propId, ...props }, ref) => {
    const generatedId = useId();
    const id = propId || generatedId;

    return (
      <div className={`input-group ${error ? 'input-group--error' : ''} ${className}`}>
        {label && (
          <label htmlFor={id} className="input-group__label">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className="input-group__input"
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          {...props}
        />
        {error && (
          <p id={`${id}-error`} className="input-group__error" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${id}-hint`} className="input-group__hint">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className = '', id: propId, ...props }, ref) => {
    const generatedId = useId();
    const id = propId || generatedId;

    return (
      <div className={`input-group ${error ? 'input-group--error' : ''} ${className}`}>
        {label && (
          <label htmlFor={id} className="input-group__label">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          className="input-group__input input-group__textarea"
          aria-invalid={!!error}
          {...props}
        />
        {error && (
          <p className="input-group__error" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
