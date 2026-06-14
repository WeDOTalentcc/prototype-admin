"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Check, ChevronRight } from "lucide-react"
import type { FlowStep } from "./types"

interface StepIndicatorProps {
  currentStep: FlowStep
  isPauseMode: boolean
  notifyApplicants: boolean
}

export function StepIndicator({ currentStep, isPauseMode, notifyApplicants }: StepIndicatorProps) {
  if (!isPauseMode || !notifyApplicants) return null

  const steps = [
    { id: 'pause', label: 'Pausar', done: currentStep !== 'options' },
    { id: 'message', label: 'Comunicar', done: currentStep === 'confirmation' || currentStep === 'complete' },
    { id: 'done', label: 'Concluído', done: currentStep === 'complete' },
  ]

  return (
    <div data-testid="step-indicator" className="flex items-center justify-center gap-1 mb-4 pb-3">
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "w-5 h-5 rounded-full flex items-center justify-center text-micro font-medium",
              step.done
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                : currentStep === 'options' && index === 0
                  ? "bg-lia-bg-tertiary text-lia-text-primary border border-lia-btn-primary-bg"
                  : currentStep === 'communication' && index === 1
                    ? "bg-lia-bg-tertiary text-lia-text-primary border border-lia-btn-primary-bg"
                    : currentStep === 'confirmation' && index === 1
                      ? "bg-lia-bg-tertiary text-lia-text-primary border border-lia-btn-primary-bg"
                      : "bg-lia-bg-tertiary text-lia-text-tertiary"
            )}>
              {step.done ? <Check className="w-3 h-3" /> : index + 1}
            </div>
            <span className={cn(
              "text-xs font-medium",
              step.done ? "text-lia-text-primary" : "text-lia-text-secondary"
            )}>
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <ChevronRight className="w-3.5 h-3.5 text-lia-text-muted mx-1" />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}
