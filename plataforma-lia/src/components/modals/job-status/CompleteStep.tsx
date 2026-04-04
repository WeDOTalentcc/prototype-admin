"use client"

import React from "react"
import { CheckCircle } from "lucide-react"

interface CompleteStepProps {
  successMessage: string
}

export function CompleteStep({ successMessage }: CompleteStepProps) {
  return (
    <div className="py-8 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-status-success/15 flex items-center justify-center mx-auto">
        <CheckCircle className="w-8 h-8 text-status-success" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-lia-text-primary">Processo Concluído!</h3>
        <p className="text-xs text-lia-text-secondary mt-1">
          {successMessage}
        </p>
      </div>
    </div>
  )
}
