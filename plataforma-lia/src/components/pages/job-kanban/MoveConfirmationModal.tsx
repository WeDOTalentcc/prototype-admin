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
      <DialogContent className="bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 max-w-md rounded-md">
        <DialogHeader className="border-b border-gray-200 dark:border-gray-700 pb-4">
          <DialogTitle className="text-gray-900 dark:text-gray-50 flex items-center gap-2">
            Confirmar Movimentação
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-400">
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
              <span className="text-gray-700 dark:text-gray-300">{fromStage.name}</span>
            </div>
            
            <ArrowRight className="h-4 w-4 text-gray-400 dark:text-gray-500" />
            
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{backgroundColor: toStage.color}}
              />
              <span className="text-gray-900 dark:text-gray-50 font-medium">{toStage.name}</span>
            </div>
          </div>

          {substatusSuggestions.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <LIAIcon className="h-4 w-4 text-gray-700 dark:text-gray-300" />
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
                    key={index}
 className="flex items-center space-x-2 p-2 rounded-md border border-gray-200 hover:border-gray-300 dark:hover:border-gray-300 transition-colors bg-white dark:bg-gray-800"
                  >
                    <RadioGroupItem 
                      value={suggestion.content} 
                      id={`substatus-${index}`}
                      className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
                    />
                    <Label 
                      htmlFor={`substatus-${index}`}
                      className="flex-1 cursor-pointer text-gray-800 dark:text-gray-200"
                    >
                      {suggestion.content}
                    </Label>
                    <Badge 
                      variant="outline" 
 className="border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-300 text-xs"
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
              <Label className="text-sm text-gray-700 dark:text-gray-300">Sub-status disponíveis:</Label>
              <RadioGroup 
                value={selectedSubstatus} 
                onValueChange={setSelectedSubstatus}
                className="grid grid-cols-2 gap-2"
              >
                {toStage.substatuses.map((substatus) => (
                  <div 
                    key={substatus.id}
                    className="flex items-center space-x-2 p-2 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
                  >
                    <RadioGroupItem 
                      value={substatus.label} 
                      id={`sub-${substatus.id}`}
                      className="border-gray-300 dark:border-gray-600"
                    />
                    <Label 
                      htmlFor={`sub-${substatus.id}`}
                      className="cursor-pointer text-sm text-gray-700 dark:text-gray-300"
                    >
                      {substatus.label}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="reason" className="text-sm text-gray-700 dark:text-gray-300">
              Motivo (opcional)
            </Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Ex: Entrevista marcada para próxima terça..."
              className="bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-50 placeholder:text-gray-500 dark:placeholder:text-gray-500 min-h-20"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            variant="ghost"
            onClick={handleClose}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-50"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200 text-white dark:text-gray-900"
          >
            <Check className="h-4 w-4 mr-2" />
            Confirmar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
