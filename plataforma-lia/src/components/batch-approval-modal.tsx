"use client"

import { Button } from "@/components/ui/button"
import {
  X, Users, ArrowRight, Zap,
} from "lucide-react"
import {
  useBatchApproval,
  type BatchApprovalModalProps,
  type BatchApprovalCandidate,
  type BatchApprovalAction,
} from "@/hooks/candidates/use-batch-approval"
import { BatchSelectionStep } from "./batch-selection-step"
import { BatchActionStep, BatchReviewStep } from "./batch-action-step"
import { BatchProcessingStep, BatchCompleteStep } from "./batch-results-step"

export type { BatchApprovalCandidate, BatchApprovalAction, BatchApprovalModalProps }

export function BatchApprovalModal({
  isOpen,
  onClose,
  candidates,
  onApprovalComplete
}: BatchApprovalModalProps) {
  const {
    selectedCandidates,
    batchAction,
    setBatchAction,
    currentStep,
    setCurrentStep,
    filterCriteria,
    setFilterCriteria,
    searchTerm,
    setSearchTerm,
    processing,
    results,
    filteredCandidates,
    selectedCount,
    toggleCandidateSelection,
    selectAll,
    deselectAll,
    processBatchApproval,
  } = useBatchApproval({ candidates, onApprovalComplete })

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-lia-overlay/70 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-xl flex items-center justify-center">
              <Users className="w-5 h-5 text-lia-text-secondary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-lia-text-primary">
                Aprovação em Lote
              </h2>
              <p className="text-sm text-lia-text-secondary">
                Processe múltiplos candidatos simultaneamente
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full">
              <span className="text-sm font-medium text-lia-text-primary">
                Etapa {['selection', 'action', 'review', 'processing', 'complete'].indexOf(currentStep) + 1} de 5
              </span>
            </div>

            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated h-1">
          <div
            className="bg-lia-btn-primary-bg h-1 transition-colors motion-reduce:transition-none duration-500"
            style={{width: `${(['selection', 'action', 'review', 'processing', 'complete'].indexOf(currentStep) + 1) * 20}%`}}
          />
        </div>

        <div className="flex-1 overflow-hidden">
          {currentStep === 'selection' && (
            <BatchSelectionStep
              filteredCandidates={filteredCandidates}
              selectedCandidates={selectedCandidates}
              selectedCount={selectedCount}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              filterCriteria={filterCriteria}
              setFilterCriteria={setFilterCriteria}
              toggleCandidateSelection={toggleCandidateSelection}
              selectAll={selectAll}
              deselectAll={deselectAll}
            />
          )}

          {currentStep === 'action' && (
            <BatchActionStep
              selectedCount={selectedCount}
              batchAction={batchAction}
              setBatchAction={setBatchAction}
            />
          )}

          {currentStep === 'review' && (
            <BatchReviewStep
              selectedCount={selectedCount}
              batchAction={batchAction}
              selectedCandidates={selectedCandidates}
              candidates={candidates}
            />
          )}

          {currentStep === 'processing' && (
            <BatchProcessingStep selectedCount={selectedCount} />
          )}

          {currentStep === 'complete' && results && (
            <BatchCompleteStep
              results={results}
              onApprovalComplete={onApprovalComplete as (results: Record<string, unknown>) => void}
              onClose={onClose}
            />
          )}
        </div>

        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-6">
          <div className="flex items-center justify-between">
            <div>
              {currentStep !== 'complete' && (
                <p className="text-sm text-lia-text-secondary">
                  {selectedCount} candidato{selectedCount !== 1 ? 's' : ''} selecionado{selectedCount !== 1 ? 's' : ''}
                </p>
              )}
            </div>

            <div className="flex gap-3">
              {currentStep === 'selection' && (
                <Button
                  onClick={() => setCurrentStep('action')}
                  disabled={selectedCount === 0}
                  className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                >
                  Continuar
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              )}

              {currentStep === 'action' && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentStep('selection')}
                  >
                    Voltar
                  </Button>
                  <Button
                    onClick={() => setCurrentStep('review')}
                    disabled={!batchAction.type || (batchAction.type === 'move' && !batchAction.targetStage)}
                    className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  >
                    Revisar
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </>
              )}

              {currentStep === 'review' && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentStep('action')}
                  >
                    Voltar
                  </Button>
                  <Button
                    onClick={processBatchApproval}
                    disabled={processing}
                    className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  >
                    {processing ? 'Processando...' : 'Confirmar e Processar'}
                    <Zap className="w-4 h-4 ml-2" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
