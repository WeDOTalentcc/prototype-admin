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
          <DialogTitle className="text-[14px] font-semibold text-gray-950 dark:text-gray-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>
            Próxima Etapa
          </DialogTitle>
          <DialogDescription className="text-xs text-gray-600 dark:text-gray-400">
            <span className="font-medium text-gray-800">{candidateName}</span>
            <span className="mx-1.5">•</span>
            <span>{jobTitle}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div className="space-y-3">
            <Label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">
              Qual é a sua decisão?
            </Label>
            <RadioGroup
              value={decisionType || ""}
              onValueChange={(value) => setDecisionType(value as DecisionType)}
              className="grid gap-2"
            >
              <label
                className={cn(
                  "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-all",
                  decisionType === "approve"
                    ? "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50 ring-1 ring-gray-900/20"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                )}
              >
                <RadioGroupItem value="approve" id="approve" className="sr-only" />
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full",
                    decisionType === "approve"
                      ? "bg-gray-200 text-gray-800 dark:text-gray-200"
                      : "bg-gray-100 text-gray-500"
                  )}
                >
                  <CheckCircle className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-950 dark:text-gray-50">Aprovar</p>
                  <p className="text-xs text-gray-500">
                    Avançar para próxima etapa
                  </p>
                </div>
              </label>

              <label
                className={cn(
                  "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-all",
                  decisionType === "reject"
                    ? "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50 ring-1 ring-gray-900/20"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                )}
              >
                <RadioGroupItem value="reject" id="reject" className="sr-only" />
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full",
                    decisionType === "reject"
                      ? "bg-gray-200 text-gray-800 dark:text-gray-200"
                      : "bg-gray-100 text-gray-500"
                  )}
                >
                  <XCircle className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-950 dark:text-gray-50">Reprovar</p>
                  <p className="text-xs text-gray-500">
                    Encerrar participação no processo
                  </p>
                </div>
              </label>

              <label
                className={cn(
                  "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-all",
                  decisionType === "pending"
                    ? "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50 ring-1 ring-gray-900/20"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                )}
              >
                <RadioGroupItem value="pending" id="pending" className="sr-only" />
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full",
                    decisionType === "pending"
                      ? "bg-gray-200 text-gray-800 dark:text-gray-200"
                      : "bg-gray-100 text-gray-500"
                  )}
                >
                  <Clock className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-950 dark:text-gray-50">Pendente</p>
                  <p className="text-xs text-gray-500">Decidir depois</p>
                </div>
              </label>
            </RadioGroup>
          </div>

          {decisionType === "approve" && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
              <Label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">
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
                          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:text-gray-400">
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
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Brain className="h-3 w-3 text-wedo-cyan" />
                  A LIA sugeriu: <span className="font-medium">{suggestedNextStage}</span>
                </p>
              )}
            </div>
          )}

          {decisionType === "reject" && (
            <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
              <Label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">
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
                    "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-all",
                    feedbackAction === "send_now"
                      ? "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50 ring-1 ring-gray-900/20"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
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
                        ? "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                        : "bg-gray-100 text-gray-500"
                    )}
                  >
                    <Mail className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                      Enviar agora
                    </p>
                  </div>
                </label>

                <label
                  className={cn(
                    "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-all",
                    feedbackAction === "schedule"
                      ? "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50 ring-1 ring-gray-900/20"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
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
                        ? "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                        : "bg-gray-100 text-gray-500"
                    )}
                  >
                    <Calendar className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                      Agendar para depois
                    </p>
                  </div>
                </label>

                <label
                  className={cn(
                    "flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-all",
                    feedbackAction === "none"
                      ? "border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50 ring-1 ring-gray-900/20"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  )}
                >
                  <RadioGroupItem value="none" id="none" className="sr-only" />
                  <div
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-full",
                      feedbackAction === "none"
                        ? "bg-gray-200 text-gray-600"
                        : "bg-gray-100 text-gray-500"
                    )}
                  >
                    <XCircle className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                      Não enviar
                    </p>
                  </div>
                </label>
              </RadioGroup>

              {feedbackAction === "schedule" && (
                <div className="pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
                  <Label
                    htmlFor="scheduled-date"
                    className="text-[11px] font-medium text-gray-800 dark:text-gray-200"
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

        <DialogFooter className="gap-2 sm:gap-0 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700 pt-4">
          <Button 
            variant="outline" 
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isConfirmDisabled()}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            Confirmar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
