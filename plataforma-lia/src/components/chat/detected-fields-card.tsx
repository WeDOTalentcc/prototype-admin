"use client"

import React from "react"
import { CheckCircle2, Brain, Edit2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface DetectedField {
  label: string
  value: string
  confidence?: "high" | "medium" | "low"
}

interface DetectedFieldsCardProps {
  fields: DetectedField[]
  title?: string
  onEdit?: (fieldLabel: string) => void
  className?: string
}

export function DetectedFieldsCard({ fields, title = "Campos detectados automaticamente", onEdit, className }: DetectedFieldsCardProps) {
  if (fields.length === 0) return null

  const confidenceColor = (conf?: "high" | "medium" | "low") => {
    switch (conf) {
      case "high": return "text-lia-text-secondary"
      case "medium": return "text-lia-text-secondary"
      case "low": return "text-lia-text-tertiary"
      default: return "text-lia-text-secondary"
    }
  }

  return (
    <div className={cn(
      "rounded-md border border-wedo-cyan/20 bg-wedo-cyan/5 dark:bg-wedo-cyan/10 p-4 mt-3",
      className
    )}>
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide">
          {title}
        </span>
      </div>
      <div className="space-y-2">
        {fields.map((field, index) => (
          <div
            key={field.label}
            className="flex items-center justify-between py-1.5 px-2 rounded-xl bg-lia-bg-primary/60/40"
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <CheckCircle2 className={cn("w-3.5 h-3.5 flex-shrink-0", confidenceColor(field.confidence))} />
              <span className="text-xs text-lia-text-secondary flex-shrink-0">
                {field.label}:
              </span>
              <span className="text-xs font-medium text-lia-text-primary truncate">
                {field.value}
              </span>
            </div>
            {onEdit && (
              <button
                onClick={() => onEdit(field.label)}
                aria-label={`Editar campo ${field.label}`}
                className="p-1 text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none flex-shrink-0 focus:outline-none focus-visible:ring-1 focus-visible:ring-lia-border-default rounded-md"
              >
                <Edit2 className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>
      <p className="text-micro text-lia-text-tertiary mt-2 italic">
        Campos preenchidos pela IA com base na sua descrição. Edite se necessário.
      </p>
    </div>
  )
}
