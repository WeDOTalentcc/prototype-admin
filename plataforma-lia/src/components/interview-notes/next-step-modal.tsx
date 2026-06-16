"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { CheckCircle, XCircle, Clock, Mail, Calendar, Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

export type Decision = {
  type: "approve" | "reject" | "pending"
  nextStage?: string
  feedback?: {
    action: "send_now" | "schedule" | "none"
    scheduledDate?: string
  }
}

interface NextStepModalProps {
  isOpen: boolean
  onClose: () => void
  candidateName: string
  jobTitle: string
  suggestedNextStage?: string
  availableStages: string[]
  onConfirm: (decision: Decision) => void
}

type DecisionType = "approve" | "reject" | "pending"
type FeedbackAction = "send_now" | "schedule" | "none"

export function NextStepModal({
  isOpen,
  onClose,
  candidateName,
  jobTitle,
  suggestedNextStage,
  availableStages,
  onConfirm,
}: NextStepModalProps) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [decisionType, setDecisionType] = useState<DecisionType | null>(null)
  const [selectedStage, setSelectedStage] = useState<string>("")
  const [feedbackAction, setFeedbackAction] = useState<FeedbackAction>("none")
  const [scheduledDate, setScheduledDate] = useState<string>("")

  useEffect(() => {
    if (isOpen) {
      setDecisionType(null)
      setSelectedStage(suggestedNextStage || "")
      setFeedbackAction("none")
      setScheduledDate("")
    }
  }, [isOpen, suggestedNextStage])

  const handleConfirm = () => {
    if (!decisionType) return

    const decision: Decision = {
      type: decisionType,
    }

    if (decisionType === "approve" && selectedStage) {
      decision.nextStage = selectedStage
    }

    if (decisionType === "reject") {
      decision.feedback = {
        action: feedbackAction,
        ...(feedbackAction === "schedule" && scheduledDate
          ? { scheduledDate }
          : {}),
      }
    }

    onConfirm(decision)
    onClose()
  }

  const isConfirmDisabled = () => {
    if (!decisionType) return true
    if (decisionType === "approve" && !selectedStage) return true
    if (
      decisionType === "reject" &&
      feedbackAction === "schedule" &&
      !scheduledDate
    )
      return true
    return false
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md rounded-md">
        <DialogHeader>
          <DialogTitle className="text-sm font-semibold text-lia-text-primary">
            Próxima Etapa
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-secondary">
            <span className="font-medium text-lia-text-primary">{candidateName}</span>
            <span className="mx-1.5">•</span>
            <span>{jobTitle}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div className="space-y-3">
            <Label className="text-xs font-medium text-lia-text-primary">
              Qual é a sua decisão?
            </Label>
            <RadioGroup
              value={decisionType || ""}
              onValueChange={(value) => setDecisionType(value as DecisionType)}
              className="grid gap-2"
            >
              <label
                className={cn(
 "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                  decisionType === "approve"
                    ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 ring-1 ring-lia-btn-primary-bg/20"
                    : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary"
                )}
              >
                <RadioGroupItem value="approve" id="approve" className="sr-only" />
                <div
                  className={cn(
 "flex h-8 w-8 items-center justify-center rounded-full",
                    decisionType === "approve"
                      ? "bg-lia-interactive-active text-lia-text-primary"
                      : "bg-lia-bg-tertiary text-lia-text-secondary"
                  )}
                >
                  <CheckCircle className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-lia-text-primary">Aprovar</p>
                  <p className="text-xs text-lia-text-secondary">
                    Avançar para próxima etapa
                  </p>
                </div>
              </label>

              <label
                className={cn(
 "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                  decisionType === "reject"
                    ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 ring-1 ring-lia-btn-primary-bg/20"
                    : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary"
                )}
              >
                <RadioGroupItem value="reject" id="reject" className="sr-only" />
                <div
                  className={cn(
 "flex h-8 w-8 items-center justify-center rounded-full",
                    decisionType === "reject"
                      ? "bg-lia-interactive-active text-lia-text-primary"
                      : "bg-lia-bg-tertiary text-lia-text-secondary"
                  )}
                >
                  <XCircle className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-lia-text-primary">Reprovar</p>
                  <p className="text-xs text-lia-text-secondary">
                    Encerrar participação no processo
                  </p>
                </div>
              </label>

              <label
                className={cn(
 "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                  decisionType === "pending"
                    ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 ring-1 ring-lia-btn-primary-bg/20"
                    : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary"
                )}
              >
                <RadioGroupItem value="pending" id="pending" className="sr-only" />
                <div
                  className={cn(
 "flex h-8 w-8 items-center justify-center rounded-full",
                    decisionType === "pending"
                      ? "bg-lia-interactive-active text-lia-text-primary"
                      : "bg-lia-bg-tertiary text-lia-text-secondary"
                  )}
                >
                  <Clock className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-lia-text-primary">Pendente</p>
                  <p className="text-xs text-lia-text-secondary">Decidir depois</p>
                </div>
              </label>
            </RadioGroup>
          </div>

          {decisionType === "approve" && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
              <Label className="text-xs font-medium text-lia-text-primary">
                Próxima etapa
              </Label>
              <Select value={selectedStage} onValueChange={setSelectedStage}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Selecione a próxima etapa" />
                </SelectTrigger>
                <SelectContent>
                  {availableStages.map((stage) => (
                    <SelectItem key={stage} value={stage}>
                      <div className="flex items-center gap-2">
                        <span>{stage}</span>
                        {suggestedNextStage === stage && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary px-1.5 py-0.5 text-micro font-medium text-lia-text-secondary">
                            <Brain className="h-3 w-3 text-wedo-cyan" />
                            Sugestão LIA
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {suggestedNextStage && selectedStage !== suggestedNextStage && (
                <p className="text-xs text-lia-text-secondary flex items-center gap-1">
                  <Brain className="h-3 w-3 text-wedo-cyan" />
                  {`${personaName} sugeriu:`} <span className="font-medium">{suggestedNextStage}</span>
                </p>
              )}
            </div>
          )}

          {decisionType === "reject" && (
            <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
              <Label className="text-xs font-medium text-lia-text-primary">
                Enviar feedback ao candidato?
              </Label>
              <RadioGroup
                value={feedbackAction}
                onValueChange={(value) =>
                  setFeedbackAction(value as FeedbackAction)
                }
                className="grid gap-2"
              >
                <label
                  className={cn(
 "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                    feedbackAction === "send_now"
                      ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 ring-1 ring-lia-btn-primary-bg/20"
                      : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary"
                  )}
                >
                  <RadioGroupItem
                    value="send_now"
                    id="send_now"
                    className="sr-only"
                  />
                  <div
                    className={cn(
 "flex h-7 w-7 items-center justify-center rounded-full",
                      feedbackAction === "send_now"
                        ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
                        : "bg-lia-bg-tertiary text-lia-text-secondary"
                    )}
                  >
                    <Mail className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary">
                      Enviar agora
                    </p>
                  </div>
                </label>

                <label
                  className={cn(
 "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                    feedbackAction === "schedule"
                      ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 ring-1 ring-lia-btn-primary-bg/20"
                      : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary"
                  )}
                >
                  <RadioGroupItem
                    value="schedule"
                    id="schedule"
                    className="sr-only"
                  />
                  <div
                    className={cn(
 "flex h-7 w-7 items-center justify-center rounded-full",
                      feedbackAction === "schedule"
                        ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
                        : "bg-lia-bg-tertiary text-lia-text-secondary"
                    )}
                  >
                    <Calendar className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary">
                      Agendar para depois
                    </p>
                  </div>
                </label>

                <label
                  className={cn(
 "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors",
                    feedbackAction === "none"
                      ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 ring-1 ring-lia-btn-primary-bg/20"
                      : "border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary"
                  )}
                >
                  <RadioGroupItem value="none" id="none" className="sr-only" />
                  <div
                    className={cn(
 "flex h-7 w-7 items-center justify-center rounded-full",
                      feedbackAction === "none"
                        ? "bg-lia-interactive-active text-lia-text-secondary"
                        : "bg-lia-bg-tertiary text-lia-text-secondary"
                    )}
                  >
                    <XCircle className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary">
                      Não enviar
                    </p>
                  </div>
                </label>
              </RadioGroup>

              {feedbackAction === "schedule" && (
                <div className="pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
                  <Label
                    htmlFor="scheduled-date"
                    className="text-xs font-medium text-lia-text-primary"
                  >
                    Data de envio
                  </Label>
                  <Input
                    id="scheduled-date"
                    type="datetime-local"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    className="mt-1.5"
                    min={new Date().toISOString().slice(0, 16)}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle pt-4">
          <Button 
            variant="outline" 
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isConfirmDisabled()}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            Confirmar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
