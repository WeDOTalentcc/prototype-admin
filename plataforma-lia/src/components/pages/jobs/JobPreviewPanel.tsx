"use client"

import { Button } from "@/components/ui/button"
import { ChevronRight, ClipboardList } from "lucide-react"
import { useJobPreviewState } from "./job-preview/useJobPreviewState"
import { JobPreviewHeader } from "./job-preview/sections/JobPreviewHeader"
import { JobPreviewAnalytics } from "./job-preview/sections/JobPreviewAnalytics"
import { JobPreviewLiaMetrics } from "./job-preview/sections/JobPreviewLiaMetrics"
import { JobScreeningSection } from "./job-preview/sections/JobScreeningSection"
import { JobPipelineSection } from "./job-preview/sections/JobPipelineSection"
import { type JobPreviewPanelProps } from "./job-preview/job-preview.types"

export type { JobPreviewPanelProps }

export function JobPreviewPanel({
  showJobPreview,
  previewJob,
  activePreviewTab,
  onTabChange,
  previewWidth,
  onResize,
  onResizeStart,
  onResizeEnd,
  onClose,
  onJobClick,
  screeningConfig,
  isLoadingScreeningConfig,
  jobMetrics,
  isLoadingJobMetrics,
}: JobPreviewPanelProps) {
  const {
    expandedBlocks,
    collapsedPreviewSections,
    togglePreviewSection,
    toggleBlock,
  } = useJobPreviewState()

  if (!showJobPreview || !previewJob) return null
  const _previewJob = previewJob!

  return (
    <div 
      className="flex-shrink-0 bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg overflow-hidden animate-slide-in flex flex-col h-full max-h-[calc(100vh-180px)] relative group"
      style={{width: `${previewWidth}px`,
        minWidth: '320px',
        maxWidth: '700px'}}
    >
      <div
        className="absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize bg-lia-border-medium/30 hover:bg-lia-border-medium transition-colors motion-reduce:transition-none group-hover:opacity-100 opacity-0 z-10"
        onMouseDown={(e) => {
          e.preventDefault()
          onResizeStart()
          const startX = e.clientX
          const startWidth = previewWidth

          const handleMouseMove = (e: MouseEvent) => {
            const deltaX = startX - e.clientX
            const newWidth = Math.max(320, Math.min(700, startWidth + deltaX))
            onResize(newWidth)
          }

          const handleMouseUp = () => {
            onResizeEnd()
            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)
          }

          document.addEventListener('mousemove', handleMouseMove)
          document.addEventListener('mouseup', handleMouseUp)
        }}
      />

      <JobPreviewHeader
        previewJob={_previewJob}
        onClose={onClose}
        onJobClick={onJobClick}
      />

      <div className="">
        <div className="flex items-center px-3">
          <button
            onClick={() => onTabChange('screening')}
            className={`px-2 py-2 text-micro font-medium border-b transition-colors motion-reduce:transition-none ${
              activePreviewTab === 'screening'
                ? 'border-lia-text-primary text-lia-text-secondary font-semibold'
                : 'border-transparent text-lia-text-tertiary hover:text-lia-text-secondary'
            }`}
          >
            <div className="flex items-center gap-1">
              <ClipboardList className="w-2.5 h-2.5" />
              Detalhes da Vaga
            </div>
          </button>
        </div>
      </div>

      <div className="overflow-y-auto flex-1 p-4">
        {activePreviewTab === 'pipeline' && (
          <JobPreviewAnalytics
            previewJob={_previewJob}
            jobMetrics={jobMetrics}
            isLoadingJobMetrics={isLoadingJobMetrics}
          />
        )}

        {false && (
          <JobPreviewLiaMetrics previewJob={_previewJob} />
        )}

        {activePreviewTab === 'screening' && (
          <JobScreeningSection
            previewJob={_previewJob}
            screeningConfig={screeningConfig}
            isLoadingScreeningConfig={isLoadingScreeningConfig}
            collapsedPreviewSections={collapsedPreviewSections}
            expandedBlocks={expandedBlocks}
            onToggleSection={togglePreviewSection}
            onToggleBlock={toggleBlock}
          />
        )}

        {activePreviewTab === 'pipeline' && (
          <JobPipelineSection
            previewJob={_previewJob}
            jobMetrics={jobMetrics}
            isLoadingJobMetrics={isLoadingJobMetrics}
          />
        )}

        <div className="mt-4 pt-3 border-t border-lia-border-subtle space-y-2">
          <Button
            className="w-full text-xs h-8 gap-2"
            onClick={() => onJobClick(_previewJob)}
          >
            <ChevronRight className="w-4 h-4" />
            Abrir Kanban de Candidatos
          </Button>
        </div>
      </div>
    </div>
  )
}
