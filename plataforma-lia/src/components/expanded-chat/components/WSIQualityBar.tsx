'use client'

import React from 'react'
import { CheckCircle2, AlertCircle, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { type WSIQualityField } from '../hooks/useWSIQualityGates'

export interface WSIQualityBarProps {
  score: number
  fields: WSIQualityField[]
  summaryText: string
  scoreColor: 'green' | 'yellow' | 'red'
  canAdvance: boolean
  className?: string
}

const colorClasses = {
  green: {
    bg: 'bg-green-500',
    bgLight: 'bg-green-50',
    text: 'text-green-600',
    border: 'border-green-200',
  },
  yellow: {
    bg: 'bg-yellow-500',
    bgLight: 'bg-yellow-50',
    text: 'text-yellow-600',
    border: 'border-yellow-200',
  },
  red: {
    bg: 'bg-red-500',
    bgLight: 'bg-red-50',
    text: 'text-red-600',
    border: 'border-red-200',
  },
}

export function WSIQualityBar({
  score,
  fields,
  summaryText,
  scoreColor,
  canAdvance,
  className,
}: WSIQualityBarProps) {
  const colors = colorClasses[scoreColor]
  const metFields = fields.filter(f => f.isMet)
  const unmetFields = fields.filter(f => !f.isMet)

  return (
    <TooltipProvider>
      <div
        className={cn(
          'px-3 py-2 rounded-md border transition-all duration-300',
          colors.bgLight,
          colors.border,
          className
        )}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <Target className={cn('w-4 h-4', colors.text)} />
              <span 
                className={cn('text-xs font-semibold', colors.text)}
                style={{ fontFamily: '"Open Sans", sans-serif' }}
              >
                WSI Quality
              </span>
            </div>

            <div className="flex-1 max-w-[140px]">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all duration-500', colors.bg)}
                  style={{ width: `${score}%` }}
                />
              </div>
            </div>

            <span 
              className={cn('text-xs font-bold', colors.text)}
              style={{ fontFamily: '"Open Sans", sans-serif' }}
            >
              {score}%
            </span>
          </div>

          <div className="flex items-center gap-1">
            {fields.slice(0, 4).map((field) => (
              <Tooltip key={field.id}>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      'w-5 h-5 rounded-full flex items-center justify-center transition-all',
                      field.isMet 
                        ? 'bg-green-100 text-green-600' 
                        : 'bg-gray-100 text-gray-400'
                    )}
                  >
                    {field.isMet ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : (
                      <AlertCircle className="w-3 h-3" />
                    )}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  <p className="font-medium">{field.label}</p>
                  <p className={field.isMet ? 'text-green-600' : 'text-gray-500'}>
                    {field.current}/{field.required} {field.isMet ? '✓' : 'necessário'}
                  </p>
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        </div>

        <div className="mt-1.5 flex items-center justify-between gap-2">
          <p 
            className="text-micro text-gray-600 truncate"
            style={{ fontFamily: '"Open Sans", sans-serif' }}
          >
            {summaryText}
          </p>
          
          {!canAdvance && (
            <span 
              className="text-micro text-red-500 font-medium whitespace-nowrap"
              style={{ fontFamily: '"Open Sans", sans-serif' }}
            >
              Mínimo 70% para avançar
            </span>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}
