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
     
    >
      {children}
    </div>
  );
}

export function SlidePageTransition({ children, className = "" }: PageTransitionProps) {
  return (
    <div
      className={`page-transition ${className}`}
     
    >
      {children}
    </div>
  );
}

export function FadePageTransition({ children, className = "" }: PageTransitionProps) {
  return (
    <div
      className={`page-transition ${className}`}
     
    >
      {children}
    </div>
  );
}

export function AnimatedPageWrapper({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
