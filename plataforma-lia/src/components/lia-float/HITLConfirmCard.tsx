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
 "rounded-md border border-status-warning/30 dark:border-status-warning/30",
        "bg-status-warning/10",
        "p-3 space-y-2.5"
      )}
      role="alertdialog"
      aria-label="Confirmação de ação"
    >
      {/* Header */}
      <div className="flex items-start gap-2">
        <AlertCircle
          className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5"
          strokeWidth={2}
        />
        <p
          className="text-sm-ui font-semibold text-status-warning leading-snug"
          
        >
          Confirmação necessária
        </p>
      </div>

      {/* Descrição da ação */}
      <p
        className="text-sm-ui text-lia-text-secondary leading-relaxed pl-6"
       
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
          className="w-3.5 h-3.5 rounded-md accent-lia-btn-primary-bg cursor-pointer"
          aria-label="Confirmar automaticamente esta ação no futuro"
        />
        <span
          className="text-xs text-lia-text-tertiary"
         
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
            "bg-lia-btn-primary-bg text-lia-btn-primary-text",
            "hover:bg-lia-btn-primary-bg dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
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
            "border border-lia-border-subtle",
            "text-lia-text-secondary",
            "hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
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
