"use client"

import React from "react"
import { Chip, type ChipVariant } from "@/components/ui/chip"
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
  variant: ChipVariant
  muted?: boolean
  description: string
}> = {
  detected: {
    label: 'Detectado',
    icon: Brain,
    variant: 'info',
    description: 'Extraído automaticamente do texto'
  },
  default: {
    label: 'Default',
    icon: Building2,
    variant: 'success',
    description: 'Configuração padrão da empresa'
  },
  manual: {
    label: 'Manual',
    icon: PenLine,
    variant: 'neutral',
    muted: true,
    description: 'Editado manualmente'
  },
  suggested: {
    label: 'Sugerido',
    icon: Lightbulb,
    variant: 'warning',
    description: 'Sugestão baseada em vagas similares'
  },
  benchmark: {
    label: 'Benchmark',
    icon: Lightbulb,
    variant: 'info',
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
  let resolvedOrigin: FieldOrigin = 'detected'

  if (origin) {
    resolvedOrigin = origin
  } else if (source) {
    resolvedOrigin = SOURCE_TO_ORIGIN[source] || 'detected'
  }

  const config = ORIGIN_CONFIG[resolvedOrigin]
  const Icon = config.icon

  return (
    <Chip
      density={size === 'sm' ? 'compact' : 'comfortable'}
      variant={config.variant}
      muted={config.muted}
      className={cn('font-normal', className)}
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
    </Chip>
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
