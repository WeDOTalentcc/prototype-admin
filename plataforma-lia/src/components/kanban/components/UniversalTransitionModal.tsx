"use client"
// lia-context: setLiaModal managed by useUniversalTransitionModal hook
import NextImage from "next/image"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectTrigger, SelectValue } from '@/components/ui/select'
import { renderSubStatusOptions } from './rejection-categories'
import { useRejectionCategoryLabels } from './use-rejection-category-labels'
import {
  ArrowRight,
  Brain,
  User,
  Loader2,
  CalendarClock,
  ChevronDown,
  AlertTriangle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles, cardStyles } from '@/lib/design-tokens'
import { TransitionChatPanel } from './TransitionChatPanel'
import { BatchRejectionSection, ActionModeSection } from './TransitionActionSection'
import {
  useUniversalTransitionModal,
  type UniversalTransitionModalProps,
  type UniversalTransitionConfirmData,
} from './useUniversalTransitionModal'

export type { UniversalTransitionConfirmData }

export function UniversalTransitionModal(props: UniversalTransitionModalProps) {
  const {
    isOpen,
    onClose,
    candidates,
    onOpenSpecializedModal,
    availableStages,
    allowStageSelection,
    interviewAlert,
  } = props

  const rejectionCategoryLabels = useRejectionCategoryLabels()

  const {
    subStatus,
    action,
    setAction,
    isSubmitting,
    perCandidateSubStatus,
    manuallyEditedCandidates,
    showAllPerCandidate,
    setShowAllPerCandidate,
    policyWarnings,
    policyMetadata,
    selectedToStage,
    selectedToStageDisplayName,
    currentActionBehavior,
    currentSubStatusOptions,
    showStageSelector,
    setShowStageSelector,
    handleStageSelect,
    isSingle,
    candidate,
    fromStageDisplayName,
    behaviorConfig,
    isRejectedBatch,
    showChatPanel,
    isRejectedStage,
    isBulkPredicting,
    predictedSubStatuses,
    predictionReasonings,
    messages,
    isInterpreting,
    interpretResult,
    resetInterpret,
    handleGlobalSubStatusChange,
    handlePerCandidateSubStatusChange,
    handleSendChatMessage,
    handleConfirm,
    bulkExample,
    isLoadingBulkExample,
    handleOpenManualModal,
    prompt,
    setPrompt,
    hitlPending,
    sendApproval,
  } = useUniversalTransitionModal(props)

  const fromStage = props.fromStage
  const stageSelectable = allowStageSelection && availableStages && availableStages.length > 0
  const filteredAvailableStages = stageSelectable
    ? availableStages!.filter(s => s.id !== fromStage)
    : []

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        data-testid="universal-transition-modal"
        className={cn(
          "max-h-[85vh] overflow-hidden p-0 rounded-lg",
          showChatPanel
            ? "max-w-4xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
            : "max-w-lg bg-lia-bg-primary dark:bg-lia-bg-secondary"
        )}
      >
        <DialogHeader className="px-5 py-3 dark:border-lia-border-subtle">
          <DialogTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
            <ArrowRight className="w-4 h-4 text-lia-text-secondary" />
            Mover para: {selectedToStageDisplayName}
          </DialogTitle>
        </DialogHeader>

        {policyWarnings.length > 0 && (
          <div className="mx-6 mt-3 p-3 bg-status-warning/10 border border-status-warning/30 rounded-xl text-sm dark:bg-status-warning/20 dark:border-status-warning/30">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0 dark:text-status-warning" />
              <div>
                <p className="font-medium text-status-warning dark:text-status-warning">Atenção — Política da empresa</p>
                {policyWarnings.map((w, i) => (
                  <p key={i} className="mt-1 text-status-warning dark:text-status-warning">{w}</p>
                ))}
                {!!policyMetadata.requires_manager_approval && (
                  <p className="mt-1 text-status-warning dark:text-status-warning">
                    Aprovação do gestor será necessária antes de prosseguir.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {interviewAlert && (
          <div className="mx-4 mt-2 flex items-start gap-2 px-3 py-2 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-lg">
            <CalendarClock className="w-3.5 h-3.5 text-status-warning dark:text-status-warning flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-micro font-semibold text-status-warning dark:text-status-warning">
                Entrevista agendada
              </p>
              <p className="text-micro text-status-warning dark:text-status-warning">
                {interviewAlert.name} — {interviewAlert.date}
              </p>
            </div>
          </div>
        )}

        <div className={cn(
          "overflow-y-auto",
          showChatPanel ? "flex flex-col md:flex-row" : ""
        )}>
          <div className={cn(
            "px-4 py-3 space-y-2.5 overflow-y-auto",
            showChatPanel
              ? "md:w-[36%] md:max-h-[calc(85vh-120px)]"
              : "w-full"
          )}>
            <div className={`p-2.5 ${cardStyles.flat} space-y-2`}>
              {isSingle && candidate ? (
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full flex items-center justify-center flex-shrink-0">
                    {candidate.avatar ? (
                      <NextImage src={candidate.avatar} alt="" width={32} height={32} className="w-8 h-8 rounded-full object-cover" />
                    ) : (
                      <User className="w-3.5 h-3.5 text-lia-text-secondary" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-lia-text-primary truncate leading-tight">
                      {candidate.name}
                    </p>
                    {(candidate.role || candidate.currentTitle || candidate.currentCompany) && (
                      <p className="text-micro text-lia-text-secondary truncate leading-tight mt-0.5">
                        {candidate.role || candidate.currentTitle}{(candidate.role || candidate.currentTitle) && candidate.currentCompany ? ' • ' : ''}{candidate.currentCompany}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-micro font-semibold text-lia-text-secondary">{candidates.length}</span>
                  </div>
                  <p className="text-xs font-medium text-lia-text-primary" aria-live="polite" aria-atomic="true">
                    {candidates.length} candidatos selecionados
                  </p>
                </div>
              )}

              <div className="flex items-center justify-center gap-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium text-lia-text-secondary border border-lia-border-default dark:border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-elevated">
                  {fromStageDisplayName}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0" />
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => stageSelectable && setShowStageSelector(!showStageSelector)}
                    className={cn(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-semibold border bg-lia-bg-primary dark:bg-lia-bg-elevated",
                      stageSelectable
                        ? "text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-default cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-border-medium"
                        : "text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-default cursor-default"
                    )}
                  >
                    {selectedToStageDisplayName}
                    {stageSelectable && <ChevronDown className="w-3 h-3" />}
                  </button>
                  {showStageSelector && stageSelectable && (
                    <div className="absolute top-full left-0 mt-1 z-50 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-md max-h-48 overflow-y-auto min-w-[160px]">
                      {filteredAvailableStages.map((stage) => (
                        <button
                          key={stage.id}
                          type="button"
                          onClick={() => handleStageSelect(stage)}
                          className={cn(
                            "w-full text-left px-3 py-1.5 text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none",
                            stage.id === selectedToStage
                              ? "bg-lia-bg-tertiary dark:bg-lia-bg-elevated font-semibold text-lia-text-primary"
                              : "text-lia-text-primary"
                          )}
                        >
                          {stage.displayName}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <>
              <BatchRejectionSection
                candidates={candidates}
                isRejectedBatch={isRejectedBatch}
                currentSubStatusOptions={currentSubStatusOptions}
                isBulkPredicting={isBulkPredicting}
                predictedSubStatuses={predictedSubStatuses}
                predictionReasonings={predictionReasonings}
                perCandidateSubStatus={perCandidateSubStatus}
                manuallyEditedCandidates={manuallyEditedCandidates}
                subStatus={subStatus}
                showAllPerCandidate={showAllPerCandidate}
                setShowAllPerCandidate={setShowAllPerCandidate}
                handlePerCandidateSubStatusChange={handlePerCandidateSubStatusChange}
              />

              {isRejectedBatch && action === 'lia_auto' && (
                <div className="px-5 py-2">
                  <p className="text-micro font-medium text-lia-text-secondary mb-1">
                    Exemplo do feedback (candidato 1 de {candidates.length}) — cada candidato recebe um texto personalizado pela IA
                  </p>
                  {isLoadingBulkExample ? (
                    <p className="text-xs text-lia-text-tertiary">Gerando exemplo…</p>
                  ) : bulkExample ? (
                    <div className="text-xs text-lia-text-primary bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle p-3 whitespace-pre-wrap max-h-40 overflow-y-auto">
                      {bulkExample.body}
                    </div>
                  ) : null}
                </div>
              )}

              <ActionModeSection
                action={action}
                setAction={setAction}
                behaviorConfig={behaviorConfig}
                currentActionBehavior={currentActionBehavior}
                onOpenSpecializedModal={onOpenSpecializedModal}
                handleOpenManualModal={handleOpenManualModal}
              />
            </>
          </div>

          {showChatPanel && (
            <div className="md:w-[64%] border-t md:border-t-0 md:border-l border-lia-border-subtle dark:border-lia-border-subtle flex flex-col md:max-h-[calc(85vh-120px)] bg-lia-bg-primary dark:bg-lia-bg-secondary">
              <TransitionChatPanel
                messages={messages}
                isLoading={isInterpreting}
                onSendMessage={handleSendChatMessage}
                onClearChat={() => { resetInterpret(); setPrompt(''); }}
                actionBehavior={currentActionBehavior}
                extractedPreferences={action === 'lia_auto' ? interpretResult?.extracted_preferences : null}
                localHitlPending={hitlPending}
                onLocalSendApproval={sendApproval}
              />
            </div>
          )}
        </div>

        {currentSubStatusOptions.length > 0 && (
          <div className="flex items-center justify-end gap-2 w-full px-5 py-2.5 bg-lia-bg-secondary dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <span className="text-xs font-medium text-lia-text-secondary whitespace-nowrap">
              {isRejectedBatch ? 'Motivo padrão:' : isRejectedStage ? 'Motivo:' : 'Sub-status da etapa:'}
            </span>
            <Select value={subStatus} onValueChange={handleGlobalSubStatusChange}>
              <SelectTrigger className="w-[220px] h-8 rounded-xl text-xs bg-lia-bg-primary dark:bg-lia-bg-secondary">
                <SelectValue placeholder="Selecione..." />
              </SelectTrigger>
              <SelectContent position="popper" sideOffset={4} side="top">
                {renderSubStatusOptions(currentSubStatusOptions, 'text-xs', rejectionCategoryLabels)}
              </SelectContent>
            </Select>
            {interpretResult?.suggested_sub_status === subStatus && interpretResult?.ai_powered && (
              <span title="Sugerido pela IA">
                <Brain className="w-3 h-3 text-wedo-cyan flex-shrink-0" />
              </span>
            )}
          </div>
        )}

        <DialogFooter className="px-5 py-0 bg-lia-bg-secondary dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between w-full py-2.5 gap-3">
            <div className="flex items-center gap-2" />

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting}
                className="h-9 px-4 text-xs font-semibold rounded-xl transition-colors motion-reduce:transition-none duration-150 bg-lia-bg-primary text-lia-text-primary border border-lia-border-default hover:bg-lia-bg-secondary hover:border-lia-border-medium focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
              >
                Cancelar
              </Button>

              <Button
                onClick={handleConfirm}
                disabled={isSubmitting || (isRejectedStage && !subStatus)}
                className="h-9 px-4 text-xs font-semibold rounded-xl transition-colors motion-reduce:transition-none duration-150 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover active:bg-lia-bg-inverse focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none dark:hover:bg-lia-interactive-active"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                    Processando...
                  </>
                ) : (
                  <>
                    {action === 'lia_auto' ? (
                      <>
                        <Brain className="w-3.5 h-3.5 mr-1.5 text-wedo-cyan" />
                        Confirmar com IA
                      </>
                    ) : (
                      <>
                        <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
                        Confirmar
                      </>
                    )}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
