import { type ReactNode } from 'react';
import './Auth.css';

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="auth-layout">
      <div className="auth-layout__left">
        <div className="auth-brand">
          <h1>NutriPlan</h1>
          <p>AI-powered practice OS for Indian nutritionists.</p>
        </div>
      </div>
      <div className="auth-layout__right">
        <div className="auth-container">
          {children}
        </div>
      </div>
    </div>
  );
}
