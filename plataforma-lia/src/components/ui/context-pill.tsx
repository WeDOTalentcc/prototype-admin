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
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border transition-all duration-200 ${className}`}
      style={{
        backgroundColor: 'rgb(255 255 255)',
        borderColor: 'rgb(209 213 219)',
        color: 'rgb(31 41 55)'
      }}
    >
      <span className="text-gray-600 dark:text-gray-400 flex-shrink-0">
        {icon}
      </span>
      
      <span className="font-medium">
        {primaryText}
      </span>
      
      {secondaryText && (
        <>
          <span className="text-gray-400 dark:text-gray-500">•</span>
          <span className="text-gray-500 dark:text-gray-400">
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
