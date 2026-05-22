"use client"

import React from "react"
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  ArrowRight,
  Send,
  X,
  Loader2,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
import { cn } from "@/lib/utils"
import {
  useStageTransitionModal,
  type StageTransitionActionsModalProps,
  type TransitionActionType,
} from "./useStageTransitionModal"
import { StageTransitionLeftPanel } from "./stage-transition-left-panel"
import { StageTransitionRightPanel } from "./stage-transition-right-panel"

export type { TransitionActionType }

export function StageTransitionActionsModal(props: StageTransitionActionsModalProps) {
  const {
    isOpen,
    onClose,
    candidate,
    job,
    currentStage,
    newStage,
    wsiData,
  } = props

  const {
    selectedAction,
    setSelectedAction,
    channel,
    setChannel,
    selectedTemplateId,
    subject,
    setSubject,
    message,
    isLoading,
    isRegenerating,
    isMessageEdited,
    showPulse,
    suggestedActions,
    isLoadingTemplates,
    filteredTemplates,
    selectedActionData,
    needsMessageComposition,
    headerColor,
    handleTemplateSelect,
    handleMessageChange,
    handleConfirm,
    regenerateMessage,
  } = useStageTransitionModal(props)

  // WT-2022 P0.STAGES: pipeline da empresa via hook
  const { legacyStages } = useRecruitmentStages()
  const newStageData = legacyStages.find(s => s.name === newStage)

  if (!isOpen || !candidate) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 bg-lia-bg-secondary/50">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center",
              headerColor === 'red' ? 'bg-status-error/15' : 'bg-lia-bg-tertiary'
            )}>
              <ArrowRight className={cn(
                "w-4 h-4",
                headerColor === 'red' ? 'text-status-error' : 'text-lia-text-secondary'
              )} />
            </div>
            <div>
              <h3 className={cn(textStyles.title, "")}>
                Mover Candidato
              </h3>
              <p className={textStyles.description}>
                Escolha uma ação de comunicação para acompanhar a mudança de estágio
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none" aria-label="Fechar" data-dismiss="true">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <StageTransitionLeftPanel
            candidate={candidate}
            job={job}
            currentStage={currentStage}
            newStage={newStage}
            wsiData={wsiData}
            headerColor={headerColor}
            suggestedActions={suggestedActions}
            selectedAction={selectedAction}
            setSelectedAction={setSelectedAction}
            channel={channel}
            setChannel={setChannel}
            needsMessageComposition={needsMessageComposition}
            filteredTemplates={filteredTemplates}
            selectedTemplateId={selectedTemplateId}
            handleTemplateSelect={handleTemplateSelect}
          />

          <StageTransitionRightPanel
            needsMessageComposition={needsMessageComposition}
            channel={channel}
            selectedAction={selectedAction}
            isLoadingTemplates={isLoadingTemplates}
            isRegenerating={isRegenerating}
            isMessageEdited={isMessageEdited}
            showPulse={showPulse}
            subject={subject}
            setSubject={setSubject}
            message={message}
            handleMessageChange={handleMessageChange}
            regenerateMessage={regenerateMessage}
          />
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-lia-bg-primary">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={isLoading}
            className="h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!selectedAction || isLoading}
            className={cn(
              "gap-2 h-9 px-4 text-xs font-medium",
              selectedActionData?.color === 'red'
                ? "bg-status-error hover:bg-status-error text-white"
                : "bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                Processando...
              </>
            ) : (
              <>
                {selectedAction === 'apenas_mover' ? (
                  <>
                    <ArrowRight className="w-3.5 h-3.5" />
                    Mover
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    Confirmar e Enviar
                  </>
                )}
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default StageTransitionActionsModal
