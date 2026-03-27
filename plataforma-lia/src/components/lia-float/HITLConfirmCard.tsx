"use client"

/**
 * HITLConfirmCard — Card de aprovação humana (HITL) exibido dentro do LiaChatPanel.
 *
 * Aparece quando o agente solicita confirmação antes de executar uma ação real
 * (mover candidato, agendar entrevista, enviar mensagem, etc.).
 *
 * Props:
 *   action      — identificador da ação (ex: "move_candidate", "schedule_interview")
 *   description — descrição legível para o recrutador confirmar
 *   onConfirm   — callback ao confirmar
 *   onCancel    — callback ao cancelar
 *
 * Compatível com Vue/Nuxt: sem React-only patterns.
 */

import React, { useState } from "react"
import { CheckCircle, XCircle, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface HITLConfirmCardProps {
  action: string
  domain?: string
  description: string
  onConfirm: (autoConfirm: boolean) => void
  onCancel: () => void
}

export function HITLConfirmCard({
  action,
  domain,
  description,
  onConfirm,
  onCancel,
}: HITLConfirmCardProps) {
  const [autoConfirm, setAutoConfirm] = useState(false)

  return (
    <div
      className={cn(
        "rounded-md border border-amber-200 dark:border-amber-800",
        "bg-amber-50 dark:bg-amber-950/30",
        "p-3 space-y-2.5"
      )}
      role="alertdialog"
      aria-label="Confirmação de ação"
    >
      {/* Header */}
      <div className="flex items-start gap-2">
        <AlertCircle
          className="w-4 h-4 text-amber-500 dark:text-amber-400 flex-shrink-0 mt-0.5"
          strokeWidth={2}
        />
        <p
          className="text-sm-ui font-semibold text-amber-800 dark:text-amber-300 leading-snug"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          Confirmação necessária
        </p>
      </div>

      {/* Descrição da ação */}
      <p
        className="text-sm-ui text-gray-700 dark:text-gray-300 leading-relaxed pl-6"
       
      >
        {description}
      </p>

      {/* Auto-confirm checkbox */}
      <label
        className="flex items-center gap-2 pl-6 cursor-pointer select-none"
        htmlFor={`auto-confirm-${action}`}
      >
        <input
          id={`auto-confirm-${action}`}
          type="checkbox"
          checked={autoConfirm}
          onChange={(e) => setAutoConfirm(e.target.checked)}
          className="w-3.5 h-3.5 rounded accent-gray-900 cursor-pointer"
          aria-label="Confirmar automaticamente esta ação no futuro"
        />
        <span
          className="text-xs text-gray-500 dark:text-gray-400"
         
        >
          Confirmar automaticamente esta ação no futuro
        </span>
      </label>

      {/* Botões */}
      <div className="flex items-center gap-2 pl-6">
        <button
          onClick={() => onConfirm(autoConfirm)}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5",
            "rounded-md text-xs font-medium",
            "bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900",
            "hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors"
          )}
          aria-label="Confirmar ação"
        >
          <CheckCircle className="w-3.5 h-3.5" strokeWidth={2} />
          Confirmar
        </button>
        <button
          onClick={onCancel}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5",
            "rounded-md text-xs font-medium",
            "border border-gray-200 dark:border-gray-700",
            "text-gray-600 dark:text-gray-400",
            "hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          )}
          aria-label="Cancelar ação"
        >
          <XCircle className="w-3.5 h-3.5" strokeWidth={2} />
          Cancelar
        </button>
      </div>
    </div>
  )
}
