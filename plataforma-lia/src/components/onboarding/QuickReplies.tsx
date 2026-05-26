"use client"

/**
 * QuickReplies — P2-2 Sprint B.2.
 *
 * Botões inline pra respostas estruturadas no onboarding chat.
 * Usado pra responder perguntas com validation rule enum_* ou boolean.
 *
 * Não modifica chat panel existente — é componente standalone que
 * pode ser montado dentro de qualquer message renderer.
 *
 * 6 presets canonical alinhados com validation rules do YAML
 * onboarding_questions:
 *   - boolean (Sim / Não)
 *   - work_model (Presencial / Híbrido / Remoto)
 *   - autonomy (Low / Medium / High)
 *   - channel (WhatsApp / E-mail / SMS)
 *   - experience_policy (Por vaga / Política da empresa)
 *   - ai_tone (Formal / Profissional / Amigável / Casual / Inspirador / Direto)
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.2
 */

import { Check } from "lucide-react"
import { useState } from "react"

export type QuickReplyPreset =
  | "boolean"
  | "work_model"
  | "autonomy"
  | "channel"
  | "experience_policy"
  | "ai_tone"

export interface QuickReplyOption {
  label: string  // texto visível no botão
  value: string  // valor enviado quando clicado
  icon?: React.ReactNode  // opcional
}

const PRESETS: Record<QuickReplyPreset, QuickReplyOption[]> = {
  boolean: [
    { label: "Sim", value: "sim" },
    { label: "Não", value: "não" },
  ],
  work_model: [
    { label: "Presencial", value: "presencial" },
    { label: "Híbrido", value: "hibrido" },
    { label: "Remoto", value: "remoto" },
  ],
  autonomy: [
    { label: "Low — sempre pede confirmação", value: "low" },
    { label: "Medium — age em decisões reversíveis", value: "medium" },
    { label: "High — age na maioria", value: "high" },
  ],
  channel: [
    { label: "WhatsApp", value: "whatsapp" },
    { label: "E-mail", value: "email" },
    { label: "SMS", value: "sms" },
  ],
  experience_policy: [
    { label: "Por vaga (individual)", value: "per_job" },
    { label: "Política da empresa (todas)", value: "company_wide" },
  ],
  ai_tone: [
    { label: "Formal", value: "formal" },
    { label: "Profissional", value: "profissional" },
    { label: "Amigável", value: "amigavel" },
    { label: "Casual", value: "casual" },
    { label: "Inspirador", value: "inspirador" },
    { label: "Direto", value: "direto" },
  ],
}

interface Props {
  preset?: QuickReplyPreset
  options?: QuickReplyOption[]  // override custom
  onSelect: (value: string, label: string) => void
  disabled?: boolean
  className?: string
}

export function QuickReplies({ preset, options, onSelect, disabled = false, className = "" }: Props) {
  const [selectedValue, setSelectedValue] = useState<string | null>(null)

  const items: QuickReplyOption[] = options ?? (preset ? PRESETS[preset] : [])

  if (items.length === 0) return null

  const handleClick = (option: QuickReplyOption) => {
    if (disabled || selectedValue !== null) return
    setSelectedValue(option.value)
    onSelect(option.value, option.label)
  }

  return (
    <div
      data-testid="quick-replies"
      role="group"
      aria-label="Respostas rápidas"
      className={`flex flex-wrap gap-2 mt-2 ${className}`}
    >
      {items.map((option) => {
        const isSelected = selectedValue === option.value
        const isAnotherSelected = selectedValue !== null && !isSelected
        return (
          <button
            key={option.value}
            type="button"
            data-testid={`quick-reply-${option.value}`}
            onClick={() => handleClick(option)}
            disabled={disabled || selectedValue !== null}
            className={`
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
              text-xs font-medium border transition-colors motion-reduce:transition-none
              ${isSelected
                ? "bg-wedo-cyan text-white border-wedo-cyan"
                : isAnotherSelected
                  ? "bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle opacity-50"
                  : "bg-lia-bg-primary text-lia-text-primary border-lia-border-default hover:bg-wedo-cyan/10 hover:border-wedo-cyan/40"
              }
              ${(disabled || isAnotherSelected) ? "cursor-not-allowed" : "cursor-pointer"}
            `}
            aria-pressed={isSelected}
          >
            {isSelected && <Check className="w-3 h-3" aria-hidden="true" />}
            {option.icon}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
