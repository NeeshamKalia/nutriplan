import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

export function LoadingSpinner({ size = 'md', label }: LoadingSpinnerProps) {
  return (
    <div className="spinner-container">
      <div className={`spinner spinner--${size}`} role="status">
        <span className="visually-hidden">{label || 'Loading...'}</span>
      </div>
      {label && <p className="spinner-label">{label}</p>}
    </div>
  );
}
