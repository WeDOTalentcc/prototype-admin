"use client"

import React, { useState } from "react"
import { HelpCircle, X, Brain } from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface AIDisclaimerProps {
  variant?: "inline" | "icon" | "compact"
  className?: string
}

export function AIDisclaimer({ variant = "icon", className = "" }: AIDisclaimerProps) {
  const [isOpen, setIsOpen] = useState(false)

  const disclaimerText = "Dados gerados por análise e inferência de IA. Podem necessitar de ajustes. Recomendamos revisar antes de prosseguir."
  const shortText = "Gerado por IA • Revise antes de confirmar"

  if (variant === "inline") {
    return (
      <div className={`flex items-start gap-2 p-2 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-md text-xs text-status-warning dark:text-status-warning ${className}`}>
        <Brain className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-wedo-cyan" />
        <span>{disclaimerText}</span>
      </div>
    )
  }

  if (variant === "compact") {
    return (
      <div className={`flex items-center gap-1.5 text-xs text-status-warning dark:text-status-warning ${className}`}>
        <Brain className="h-3 w-3 text-wedo-cyan" />
        <span>{shortText}</span>
      </div>
    )
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={`inline-flex items-center justify-center h-5 w-5 rounded-full text-status-warning hover:text-status-warning hover:bg-status-warning/15 dark:hover:bg-status-warning/30 transition-colors motion-reduce:transition-none ${className}`}
          aria-label="Informações sobre dados gerados por IA"
        >
          <HelpCircle className="h-4 w-4" />
        </button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-72 p-3 text-sm" 
        side="top" 
        align="end"
      >
        <div className="flex items-start gap-2">
          <Brain className="h-4 w-4 text-wedo-cyan mt-0.5 flex-shrink-0" />
          <div className="space-y-1">
            <p className="font-medium text-lia-text-primary">
              Dados gerados por IA
            </p>
            <p className="text-xs text-lia-text-secondary">
              Estas informações foram geradas a partir de análises e inferências. 
              Podem faltar precisão ou necessitar de ajustes.
            </p>
            <p className="text-xs text-status-warning dark:text-status-warning font-medium">
              Recomendamos revisar cada seção e fazer os ajustes necessários.
            </p>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

export default AIDisclaimer
