"use client"

import React from 'react'
import { MapPin, X } from 'lucide-react'
import { Button } from './button'

interface ContextPillProps {
  icon?: React.ReactNode
  primaryText: string
  secondaryText?: string
  onDismiss?: () => void
  className?: string
}

export function ContextPill({
  icon = <MapPin className="w-3.5 h-3.5" />,
  primaryText,
  secondaryText,
  onDismiss,
  className = ''
}: ContextPillProps) {
  return (
    <div 
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border transition-[width,height] duration-200 bg-lia-bg-primary border-lia-border-default lia-text-strong ${className}`}
    >
      <span className="text-lia-text-secondary dark:text-lia-text-tertiary flex-shrink-0">
        {icon}
      </span>
      
      <span className="font-medium">
        {primaryText}
      </span>
      
      {secondaryText && (
        <>
          <span className="text-lia-text-disabled">•</span>
          <span className="text-lia-text-tertiary dark:text-lia-text-tertiary">
            {secondaryText}
          </span>
        </>
      )}
      
      {onDismiss && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="h-5 w-5 p-0 ml-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <X className="w-3 h-3" />
        </Button>
      )}
    </div>
  )
}
