'use client'

import * as React from 'react'
import { useCallback } from 'react'
import { ChevronLeft, ChevronRight, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface PipelineStage {
  id: string
  name: string
  displayName?: string
  count: number
  color?: string
}

export interface PipelineStagesCarouselProps {
  stages: PipelineStage[]
  selectedStages?: string[]
  onStageClick?: (stageId: string) => void
  className?: string
}

const STAGE_COLORS: Record<string, string> = {
  sourcing: 'var(--lia-border-subtle)',
  screening: 'var(--lia-border-subtle)',
  long_list: 'var(--lia-border-default)',
  short_list: 'var(--lia-border-default)',
  interview_hr: 'var(--lia-border-medium)',
  interview_technical: 'var(--lia-border-medium)',
  interview_manager: 'var(--lia-text-secondary)',
  interview_manager2: 'var(--lia-text-secondary)',
  interview_final: 'var(--lia-text-secondary)',
  technical_test: 'var(--lia-border-medium)',
  english_test: 'var(--lia-border-medium)',
  references: 'var(--lia-text-secondary)',
  offer: 'var(--lia-text-primary)',
  hired: 'var(--status-success)',
  rejected: 'var(--lia-border-subtle)',
  offer_declined: 'var(--lia-border-subtle)',
}

export function PipelineStagesCarousel({
  stages,
  selectedStages = [],
  onStageClick,
  className,
}: PipelineStagesCarouselProps) {
  const scrollContainerRef = React.useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = React.useState(false)
  const [canScrollRight, setCanScrollRight] = React.useState(false)

  const checkScrollButtons = React.useCallback(() => {
    const container = scrollContainerRef.current
    if (!container) return

    const { scrollLeft, scrollWidth, clientWidth } = container
    setCanScrollLeft(scrollLeft > 5)
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 5)
  }, [])

  React.useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    checkScrollButtons()
    container.addEventListener('scroll', checkScrollButtons, { passive: true })
    window.addEventListener('resize', checkScrollButtons)

    const timer = setTimeout(checkScrollButtons, 200)

    return () => {
      container.removeEventListener('scroll', checkScrollButtons)
      window.removeEventListener('resize', checkScrollButtons)
      clearTimeout(timer)
    }
  }, [checkScrollButtons, stages])

  const scroll = (direction: 'left' | 'right') => {
    const container = scrollContainerRef.current
    if (!container) return

    const cardWidth = 160
    const scrollAmount = direction === 'left' ? -cardWidth * 2 : cardWidth * 2
    container.scrollBy({ left: scrollAmount, behavior: 'smooth' })
  }

  const getStageColor = (stageId: string): string => {
    return STAGE_COLORS[stageId] || 'var(--lia-border-medium)'
  }

  return (
    <div className={cn('relative', className)}>
      {canScrollLeft && (
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-30 w-8 h-8 flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-default rounded-full hover:bg-lia-interactive-hover transition-[width,height]"
          aria-label="Scroll esquerda"
        >
          <ChevronLeft className="w-5 h-5 text-lia-text-secondary" />
        </button>
      )}

      {canScrollLeft && (
        <div className="absolute left-8 top-0 bottom-0 w-8 bg-gradient-to-r from-lia-bg-primary to-transparent z-20 pointer-events-none" />
      )}

      <div
        ref={scrollContainerRef}
        className="overflow-x-auto [scrollbar-width:none] scroll-smooth px-2"
        style={{msOverflowStyle: 'none'}}
      >
        <div className="flex items-center gap-2 py-1 min-w-max">
          {stages.map((stage, index) => {
            const displayName = stage.displayName || stage.name
            const isSelected = selectedStages.includes(stage.id) || selectedStages.includes(stage.name) || selectedStages.includes(displayName)
            const stageColor = stage.color || getStageColor(stage.id)

            return (
              <React.Fragment key={stage.id}>
                <button
                  onClick={() => onStageClick?.(stage.id)}
                  className={cn(
 'relative flex-shrink-0 group transition-colors duration-200',
                    'focus:outline-none focus:ring-2 focus:ring-lia-border-medium focus:ring-offset-2',
                    isSelected ? 'scale-[1.02]' : 'hover:scale-[1.01]'
                  )}
                  title={displayName}
                >
                  <div
                    className={cn(
 'rounded-md px-3 py-2 min-w-[130px]',
                      'border-2 transition-colors duration-200',
                      'bg-lia-bg-primary dark:bg-lia-bg-secondary',
                      isSelected
                        ? 'border-lia-text-primary'
                        : 'border-lia-border-subtle hover:border-lia-border-default'
                    )}
                  >
                    <div className="text-micro font-medium text-lia-text-tertiary mb-0.5 whitespace-nowrap">
                      {displayName}
                    </div>

                    <div className="flex items-baseline gap-1">
                      <span
                        className={cn(
 'text-xl font-semibold leading-none',
                          isSelected
                            ? 'text-lia-text-primary'
                            : 'text-lia-text-primary'
                        )}
                      >
                        {stage.count}
                      </span>
                      <span className="text-micro font-medium text-lia-text-tertiary">
                        candidatos
                      </span>
                    </div>

                    <div className="mt-1.5 h-1 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated overflow-hidden">
                      <div
                        className="h-full rounded-full transition-[width,height] duration-300"
                        style={{backgroundColor: stageColor,
                          width: isSelected ? '100%' : '60%'}}
                      />
                    </div>
                  </div>

                  {isSelected && (
                    <div className="absolute -top-1 -right-1">
                      <div className="w-5 h-5 bg-lia-text-primary rounded-full flex items-center justify-center">
                        <CheckCircle className="w-3 h-3 text-white" />
                      </div>
                    </div>
                  )}
                </button>

                {index < stages.length - 1 && (
                  <div className="flex-shrink-0 flex items-center">
                    <ChevronRight className="w-4 h-4 text-lia-text-muted" />
                  </div>
                )}
              </React.Fragment>
            )
          })}
        </div>
      </div>

      {canScrollRight && (
        <div className="absolute right-8 top-0 bottom-0 w-8 bg-gradient-to-l from-lia-bg-primary to-transparent z-20 pointer-events-none" />
      )}

      {canScrollRight && (
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-30 w-8 h-8 flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-default rounded-full hover:bg-lia-interactive-hover transition-[width,height]"
          aria-label="Scroll direita"
        >
          <ChevronRight className="w-5 h-5 text-lia-text-secondary" />
        </button>
      )}
    </div>
  )
}

export default PipelineStagesCarousel
