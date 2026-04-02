'use client';

import React from "react"
import { cn } from '@/lib/utils';

interface LoadingProps {
  variant?: 'spinner' | 'dots' | 'skeleton' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  text?: string;
}

export const Loading = React.memo(function Loading({
  variant = 'spinner',
  size = 'md',
  className,
  text
}: LoadingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  if (variant === 'spinner') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <div
          className={cn(
 'rounded-full border-2 border-lia-border-subtle border-t-lia-border-medium animate-spin motion-reduce:animate-none',
            sizeClasses[size]
          )}
        />
        {text && (
          <span className={cn('text-lia-text-secondary', textSizeClasses[size])}>
            {text}
          </span>
        )}
      </div>
    );
  }

  if (variant === 'dots') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <div className="flex space-x-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={cn(
 'rounded-full bg-lia-text-secondary',
                size === 'sm' ? 'w-1 h-1' : size === 'md' ? 'w-2 h-2' : 'w-3 h-3'
              )}
              style={{animation: `dotsPulse 0.8s infinite ${i * 0.2}s`}}
            />
          ))}
        </div>
        {text && (
          <span className={cn('text-lia-text-secondary', textSizeClasses[size])}>
            {text}
          </span>
        )}
      </div>
    );
  }

  if (variant === 'skeleton') {
    return (
      <div className={cn('space-y-3', className)}>
        <div className="loading-skeleton h-4 rounded-md"></div>
        <div className="loading-skeleton h-4 rounded-md w-3/4"></div>
        <div className="loading-skeleton h-4 rounded-md w-1/2"></div>
      </div>
    );
  }

  if (variant === 'pulse') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <div
          className={cn(
 'rounded-full bg-lia-text-secondary animate-pulse motion-reduce:animate-none',
            sizeClasses[size]
          )}
        />
        {text && (
          <span className={cn('text-lia-text-secondary', textSizeClasses[size])}>
            {text}
          </span>
        )}
      </div>
    );
  }

  return null;
}

)
Loading.displayName = 'Loading'

export const LoadingCard = React.memo(function LoadingCard({ className }: { className?: string }) {
  return (
    <div className={cn('wedo-card p-4 space-y-3', className)}>
      <div className="loading-skeleton h-4 rounded-md w-3/4"></div>
      <div className="loading-skeleton h-3 rounded-md w-1/2"></div>
      <div className="space-y-2">
        <div className="loading-skeleton h-2 rounded-md"></div>
        <div className="loading-skeleton h-2 rounded-md w-5/6"></div>
      </div>
    </div>
  );
}

)
LoadingCard.displayName = 'LoadingCard'

export const LoadingList = React.memo(function LoadingList({ items = 3, className }: { items?: number; className?: string }) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-3 p-3 wedo-card">
          <div className="loading-skeleton w-10 h-10 rounded-full"></div>
          <div className="flex-1 space-y-2">
            <div className="loading-skeleton h-3 rounded-md w-1/2"></div>
            <div className="loading-skeleton h-2 rounded-md w-3/4"></div>
          </div>
        </div>
      ))}
    </div>
  );
}
)
LoadingList.displayName = 'LoadingList'
