'use client';

import { ReactNode } from 'react';

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

export function PageTransition({ children, className = "" }: PageTransitionProps) {
  return (
    <div
      className={`page-transition ${className}`}
      style={{ animation: 'slideInUp 0.4s ease-out' }}
    >
      {children}
    </div>
  );
}

export function SlidePageTransition({ children, className = "" }: PageTransitionProps) {
  return (
    <div
      className={`page-transition ${className}`}
      style={{ animation: 'slideInRight 0.3s ease-out' }}
    >
      {children}
    </div>
  );
}

export function FadePageTransition({ children, className = "" }: PageTransitionProps) {
  return (
    <div
      className={`page-transition ${className}`}
      style={{ animation: 'fadeIn 0.25s ease-in-out' }}
    >
      {children}
    </div>
  );
}

export function AnimatedPageWrapper({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
