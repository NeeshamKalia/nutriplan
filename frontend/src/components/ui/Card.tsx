import { type ReactNode, type HTMLAttributes } from 'react';
import './Card.css';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export function Card({ children, padding = 'md', hover = false, className = '', ...props }: CardProps) {
  return (
    <div
      className={`card card--pad-${padding} ${hover ? 'card--hover' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
