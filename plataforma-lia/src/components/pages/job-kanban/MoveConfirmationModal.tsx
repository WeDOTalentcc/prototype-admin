"use client"

import React, { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Brain, ArrowRight, Check } from "lucide-react"
import { LIAIcon } from "@/components/ui/lia-icon"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import type { MoveAction, LIASuggestion, KanbanStage } from "./types"

interface MoveConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (substatus?: string, reason?: string) => void
  pendingMove: MoveAction | null
  stages: KanbanStage[]
  liaSuggestions: LIASuggestion[]
}

export function MoveConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  pendingMove,
  stages,
  liaSuggestions,
}: MoveConfirmationModalProps) {
  const [selectedSubstatus, setSelectedSubstatus] = useState<string>("")
  const [reason, setReason] = useState("")

  const fromStage = stages.find((s) => s.id === pendingMove?.fromStageId)
  const toStage = stages.find((s) => s.id === pendingMove?.toStageId)

  const substatusSuggestions = liaSuggestions.filter((s) => s.type === "substatus")

  const handleConfirm = () => {
    onConfirm(selectedSubstatus || undefined, reason || undefined)
    setSelectedSubstatus("")
    setReason("")
  }

  const handleClose = () => {
    setSelectedSubstatus("")
    setReason("")
    onClose()
  }

  if (!pendingMove || !fromStage || !toStage) return null

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-white dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle max-w-md rounded-md">
        <DialogHeader className="border-b border-lia-border-subtle dark:border-lia-border-subtle pb-4">
          <DialogTitle className="text-lia-text-primary flex items-center gap-2">
            Confirmar Movimentação
          </DialogTitle>
          <DialogDescription className="text-lia-text-secondary">
            Mover candidato para uma nova etapa do processo
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center justify-center gap-3 py-3">
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{backgroundColor: fromStage.color}}
              />
              <span className="text-lia-text-secondary">{fromStage.name}</span>
            </div>
            
            <ArrowRight className="h-4 w-4 text-lia-text-disabled" />
            
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{backgroundColor: toStage.color}}
              />
              <span className="text-lia-text-primary font-medium">{toStage.name}</span>
            </div>
          </div>

          {substatusSuggestions.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
                <LIAIcon className="h-4 w-4 text-lia-text-secondary" />
                <span>LIA sugere:</span>
              </div>
              
              <RadioGroup 
                value={selectedSubstatus} 
                onValueChange={setSelectedSubstatus}
                className="space-y-2"
                data-testid="substatus-suggestion"
              >
                {substatusSuggestions.map((suggestion, index) => (
                  <div 
                    key={`substatus-${index}`}
 className="flex items-center space-x-2 p-2 rounded-md border border-lia-border-subtle hover:border-lia-border-default dark:hover:border-lia-border-default transition-colors motion-reduce:transition-none bg-white dark:bg-lia-bg-secondary"
                  >
                    <RadioGroupItem 
                      value={suggestion.content} 
                      id={`substatus-${index}`}
                      className="border-lia-border-default dark:border-lia-border-default text-lia-text-secondary"
                    />
                    <Label 
                      htmlFor={`substatus-${index}`}
                      className="flex-1 cursor-pointer text-lia-text-primary"
                    >
                      {suggestion.content}
                    </Label>
                    <Badge 
                      variant="outline" 
 className="border-lia-border-default dark:border-lia-border-default text-lia-text-primary text-xs"
                    >
                      {Math.round(suggestion.confidence * 100)}%
                    </Badge>
                  </div>
                ))}
              </RadioGroup>
            </div>
          )}

          {toStage.substatuses && toStage.substatuses.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm text-lia-text-secondary">Sub-status disponíveis:</Label>
              <RadioGroup 
                value={selectedSubstatus} 
                onValueChange={setSelectedSubstatus}
                className="grid grid-cols-2 gap-2"
              >
                {toStage.substatuses.map((substatus) => (
                  <div 
                    key={substatus.id}
                    className="flex items-center space-x-2 p-2 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary"
                  >
                    <RadioGroupItem 
                      value={substatus.label} 
                      id={`sub-${substatus.id}`}
                      className="border-lia-border-default dark:border-lia-border-default"
                    />
                    <Label 
                      htmlFor={`sub-${substatus.id}`}
                      className="cursor-pointer text-sm text-lia-text-secondary"
                    >
                      {substatus.label}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="reason" className="text-sm text-lia-text-secondary">
              Motivo (opcional)
            </Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Ex: Entrevista marcada para próxima terça..."
              className="bg-gray-50 dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary placeholder:text-lia-text-tertiary dark:placeholder:text-lia-text-tertiary min-h-20"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            variant="ghost"
            onClick={handleClose}
            className="text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200 text-white"
          >
            <Check className="h-4 w-4 mr-2" />
            Confirmar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
