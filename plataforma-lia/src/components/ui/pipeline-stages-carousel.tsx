'use client'

import * as React from 'react'
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
  sourcing: '#A8CED5',
  screening: '#BFA8D5',
  long_list: '#C5D9ED',
  short_list: '#B8C5D0',
  interview_hr: '#A8D5B7',
  interview_technical: '#B8E0D2',
  interview_manager: '#F5E6B3',
  interview_manager2: '#F5D6A8',
  interview_final: '#D5BFA8',
  technical_test: '#E8B8B8',
  english_test: '#E5C5C5',
  references: '#E8E4E0',
  offer: '#F5D6A8',
  hired: '#A8D5B7',
  rejected: '#E5E7EB',
  offer_declined: '#B8C5D0',
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
    container.addEventListener('scroll', checkScrollButtons)
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
    return STAGE_COLORS[stageId] || '#6B7280'
  }

  return (
    <div className={cn('relative', className)}>
      {canScrollLeft && (
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-30 w-8 h-8 flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
          aria-label="Scroll esquerda"
        >
          <ChevronLeft className="w-5 h-5 text-gray-700 dark:text-gray-200" />
        </button>
      )}

      {canScrollLeft && (
        <div className="absolute left-8 top-0 bottom-0 w-8 bg-gradient-to-r from-white dark:from-gray-900 to-transparent z-20 pointer-events-none" />
      )}

      <div
        ref={scrollContainerRef}
        className="overflow-x-auto scrollbar-hide scroll-smooth px-2"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        <div className="flex items-center gap-2 py-1" style={{ minWidth: 'max-content' }}>
          {stages.map((stage, index) => {
            const displayName = stage.displayName || stage.name
            const isSelected = selectedStages.includes(stage.id) || selectedStages.includes(stage.name) || selectedStages.includes(displayName)
            const stageColor = stage.color || getStageColor(stage.id)

            return (
              <React.Fragment key={stage.id}>
                <button
                  onClick={() => onStageClick?.(stage.id)}
                  className={cn(
                    'relative flex-shrink-0 group transition-all duration-200',
                    'focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2',
                    isSelected ? 'scale-[1.02]' : 'hover:scale-[1.01]'
                  )}
                  title={displayName}
                >
                  <div
                    className={cn(
                      'rounded-md px-3 py-2 min-w-[130px]',
                      'border-2 transition-all duration-200',
                      'bg-white dark:bg-gray-800',
                      isSelected
                        ? 'border-gray-900 dark:border-gray-100'
                        : 'border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600'
                    )}
                  >
                    <div className="text-micro font-medium text-gray-500 dark:text-gray-400 mb-0.5 whitespace-nowrap">
                      {displayName}
                    </div>

                    <div className="flex items-baseline gap-1">
                      <span
                        className={cn(
                          'text-xl font-bold leading-none',
                          isSelected
                            ? 'text-gray-900 dark:text-gray-100'
                            : 'text-gray-800 dark:text-gray-200'
                        )}
                      >
                        {stage.count}
                      </span>
                      <span className="text-micro font-medium text-gray-400 dark:text-gray-500">
                        candidatos
                      </span>
                    </div>

                    <div className="mt-1.5 h-1 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          backgroundColor: stageColor,
                          width: isSelected ? '100%' : '60%',
                        }}
                      />
                    </div>
                  </div>

                  {isSelected && (
                    <div className="absolute -top-1 -right-1">
                      <div className="w-5 h-5 bg-gray-900 dark:bg-gray-100 rounded-full flex items-center justify-center">
                        <CheckCircle className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    </div>
                  )}
                </button>

                {index < stages.length - 1 && (
                  <div className="flex-shrink-0 flex items-center">
                    <ChevronRight className="w-4 h-4 text-gray-300 dark:text-gray-600" />
                  </div>
                )}
              </React.Fragment>
            )
          })}
        </div>
      </div>

      {canScrollRight && (
        <div className="absolute right-8 top-0 bottom-0 w-8 bg-gradient-to-l from-white dark:from-gray-900 to-transparent z-20 pointer-events-none" />
      )}

      {canScrollRight && (
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-30 w-8 h-8 flex items-center justify-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
          aria-label="Scroll direita"
        >
          <ChevronRight className="w-5 h-5 text-gray-700 dark:text-gray-200" />
        </button>
      )}
    </div>
  )
}

export default PipelineStagesCarousel
