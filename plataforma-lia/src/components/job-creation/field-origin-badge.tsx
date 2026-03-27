"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Brain, Building2, PenLine, Lightbulb } from "lucide-react"

export type FieldOrigin = 'detected' | 'default' | 'manual' | 'suggested' | 'benchmark'
// Keep FieldSource for backward compatibility
export type FieldSource = 'inferred' | 'company_default' | 'benchmark' | 'manual'

export interface FieldOriginBadgeProps {
  origin?: FieldOrigin
  source?: FieldSource
  confidence?: number
  showConfidence?: boolean
  showLabel?: boolean
  size?: 'sm' | 'md'
  className?: string
}

const ORIGIN_CONFIG: Record<FieldOrigin, {
  label: string
  icon: React.ElementType
  className: string
  description: string
}> = {
  detected: {
    label: 'Detectado',
    icon: Brain,
    className: 'bg-wedo-cyan/15 text-wedo-cyan-dark border-wedo-cyan/30 hover:bg-wedo-cyan/20 dark:bg-wedo-cyan/20 dark:text-wedo-cyan dark:border-wedo-cyan/40',
    description: 'Extraído automaticamente do texto'
  },
  default: {
    label: 'Default',
    icon: Building2,
    className: 'bg-wedo-green/15 text-wedo-green border-wedo-green/30 hover:bg-wedo-green/20 dark:bg-wedo-green/20 dark:text-wedo-green dark:border-wedo-green/40',
    description: 'Configuração padrão da empresa'
  },
  manual: {
    label: 'Manual',
    icon: PenLine,
    className: 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700',
    description: 'Editado manualmente'
  },
  suggested: {
    label: 'Sugerido',
    icon: Lightbulb,
    className: 'bg-wedo-orange/15 text-wedo-orange border-wedo-orange/30 hover:bg-wedo-orange/20 dark:bg-wedo-orange/20 dark:text-wedo-orange dark:border-wedo-orange/40',
    description: 'Sugestão baseada em vagas similares'
  },
  benchmark: {
    label: 'Benchmark',
    icon: Lightbulb,
    className: 'bg-wedo-purple/15 text-wedo-purple border-wedo-purple/30 hover:bg-wedo-purple/20 dark:bg-wedo-purple/20 dark:text-wedo-purple dark:border-wedo-purple/40',
    description: 'Baseado em dados de mercado'
  }
}

// Map old FieldSource values to new FieldOrigin values for backward compatibility
const SOURCE_TO_ORIGIN: Record<FieldSource, FieldOrigin> = {
  'inferred': 'detected',
  'company_default': 'default',
  'benchmark': 'benchmark',
  'manual': 'manual'
}

export function FieldOriginBadge({ 
  origin,
  source,
  confidence, 
  showConfidence = false,
  showLabel = true,
  size = 'sm',
  className 
}: FieldOriginBadgeProps) {
  // Resolve which origin to use (new prop takes precedence)
  let resolvedOrigin: FieldOrigin = 'detected'
  
  if (origin) {
    resolvedOrigin = origin
  } else if (source) {
    resolvedOrigin = SOURCE_TO_ORIGIN[source] || 'detected'
  }
  
  const config = ORIGIN_CONFIG[resolvedOrigin]
  const Icon = config.icon
  
  return (
    <Badge 
      variant="outline"
      className={cn(
        'gap-1 font-normal',
        size === 'sm' ? 'text-xs px-1.5 py-0' : 'text-sm px-2 py-0.5',
        config.className,
        className
      )}
      title={config.description}
    >
      <Icon className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
      {showLabel && (
        <>
          {config.label}
          {showConfidence && confidence !== undefined && (
            <span className="opacity-70">({Math.round(confidence * 100)}%)</span>
          )}
        </>
      )}
    </Badge>
  )
}

export function getSourceLabel(source: FieldSource): string {
  const origin = SOURCE_TO_ORIGIN[source] || 'detected'
  return ORIGIN_CONFIG[origin]?.label || source
}

export function getSourceEmoji(source: FieldSource): string {
  return '✨' // Generic sparkle emoji for backward compatibility
}

export default FieldOriginBadge
