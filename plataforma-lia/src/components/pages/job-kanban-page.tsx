"use client"

import React from "react"
import { useKanbanPageCore } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"
import { KanbanJobHeader } from "@/components/pages/job-kanban/KanbanJobHeader"
import { KanbanPageModals } from "@/components/pages/job-kanban/KanbanPageModals"
import { KanbanPageContent } from "@/components/pages/job-kanban/KanbanPageContent"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { VagaProgressBar } from "@/components/workflow-rail"

export function JobKanbanPage({ job, onBack }: { job?: Record<string, unknown>, onBack?: () => void }) {
  const state = useKanbanPageCore({ job, onBack })

  if (!state.isClient) {
    return (
      <div className="flex items-center justify-center h-screen bg-lia-bg-primary" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex flex-col items-center gap-4" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-lia-border-medium" role="status" aria-live="polite" aria-label="Carregando..."></div>
          <span className="text-sm text-lia-text-tertiary">Carregando...</span>
        </div>
      </div>
    )
  }

  return (
    <>
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .dragging {
          opacity: 0.5;
          cursor: grabbing !important;
        }

        .drop-zone-active {
          background-color: var(--wedo-cyan-bg-05);
          border-color: 'var(--wedo-cyan)';
        }
      `}</style>

    <ErrorBoundarySection>
    <div className="h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col overflow-hidden">
      <KanbanJobHeader
        onBack={onBack}
        router={state.router}
        currentJob={state.currentJob}
        jobEditForm={state.jobEditForm}
        setJobEditForm={state.setJobEditForm}
        setJobStatusModalMode={state.setJobStatusModalMode as any}
        setShowJobStatusModal={state.setShowJobStatusModal}
        setShowCloseVacancyModal={state.setShowCloseVacancyModal}
        setActiveTab={state.setActiveTab as any}
        computedSuggestions={state.computedSuggestions}
        setShowExpandedLIA={state.setShowExpandedLIA}
        setShowLiaSuggestionsPanel={state.setShowLiaSuggestionsPanel}
        allTableCandidates={state.allTableCandidates}
        selectedCandidates={state.selectedCandidates}
        setSelectedCandidates={state.setSelectedCandidates}
        setShowShareGestorModal={state.setShowShareGestorModal}
        handleShowReport={state.handleShowReport}
        activeTab={state.activeTab}
        setShowJobEditor={state.setShowJobEditor}
        pipelineInheritance={state.pipelineInheritance}
        setJobLocalOverrides={state.setJobLocalOverrides}
      />

      {/* Workflow Rail — Campaign progress bar */}
      <VagaProgressBar jobId={String(state.currentJob?.id || "")} onNavigateToStage={(stage) => state.setActiveTab?.(stage as any)} />

      {state.proactiveInsights.length > 0 && state.activeTab === 'management' && (
        <div className="px-4 py-2 space-y-1.5">
          {state.proactiveInsights.slice(0, 3).map(insight => (
            <div
              key={insight.id}
              className={`flex items-start gap-2 px-3 py-2 rounded-xl border text-xs ${
                insight.urgency === 'urgent' ? 'bg-status-error/10 border-status-error/30 text-status-error' :
                insight.urgency === 'high' ? 'bg-status-warning/10 border-status-warning/30 text-status-warning' :
                'bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary'
              }`}
            >
              <span className="font-medium flex-shrink-0">{insight.title}</span>
              <span className="flex-1">{insight.message}</span>
              <button
                onClick={() => state.dismissInsight(insight.id)}
                className="flex-shrink-0 opacity-50 hover:opacity-100"
                aria-label="Dispensar"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <KanbanPageContent state={state} />

      <KanbanPageModals {...state} />

    </div>
    </ErrorBoundarySection>
    </>
  )
}
