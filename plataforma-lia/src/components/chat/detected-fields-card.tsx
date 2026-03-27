"use client"

import React from "react"
import { CheckCircle2, Sparkles, Edit2 } from "lucide-react"
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
      case "high": return "text-cyan-500 dark:text-cyan-400"
      case "medium": return "text-gray-500 dark:text-gray-400"
      case "low": return "text-gray-400 dark:text-gray-500"
      default: return "text-cyan-500 dark:text-cyan-400"
    }
  }

  return (
    <div className={cn(
      "rounded-md border border-cyan-500/20 bg-cyan-500/5 dark:bg-cyan-500/10 p-4 mt-3",
      className
    )}>
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-cyan-500" />
        <span className="text-xs font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide">
          {title}
        </span>
      </div>
      <div className="space-y-2">
        {fields.map((field, index) => (
          <div
            key={index}
            className="flex items-center justify-between py-1.5 px-2 rounded bg-white/60 dark:bg-gray-800/40"
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <CheckCircle2 className={cn("w-3.5 h-3.5 flex-shrink-0", confidenceColor(field.confidence))} />
              <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                {field.label}:
              </span>
              <span className="text-xs font-medium text-gray-900 dark:text-gray-100 truncate">
                {field.value}
              </span>
            </div>
            {onEdit && (
              <button
                onClick={() => onEdit(field.label)}
                aria-label={`Editar campo ${field.label}`}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors flex-shrink-0 focus:outline-none focus-visible:ring-1 focus-visible:ring-gray-400 rounded"
              >
                <Edit2 className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>
      <p className="text-micro text-gray-400 dark:text-gray-500 mt-2 italic">
        Campos preenchidos pela LIA com base na sua descrição. Edite se necessário.
      </p>
    </div>
  )
}
