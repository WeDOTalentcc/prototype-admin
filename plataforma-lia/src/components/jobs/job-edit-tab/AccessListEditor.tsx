"use client"

import React, { useState } from "react"
import { X, Plus, Mail } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * AccessListEditor — Sprint 1 RBAC (2026-05-25).
 *
 * Multi-tag input para gerenciar access_list (emails de hiring team)
 * em vagas confidenciais. Backend persiste em ARRAY[String] de emails.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
 *
 * Comportamento:
 * - Input email + Enter (ou botão "+") adiciona ao access_list
 * - Cada email vira chip clicável com X para remover
 * - Validação básica: email format (regex simples)
 * - Disabled state preserva display read-only
 *
 * Backend: filtro em app/api/v1/job_vacancies/crud.py:list_job_vacancies
 * verifica `user_email in jv_access_list` (lowercase) para liberar visibilidade.
 *
 * Wave 1+ (Phase H RBAC Sprint 2): refatorar para FK array de User.id
 * em vez de emails-strings (resistência a rename de email).
 */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface AccessListEditorProps {
  accessList: string[]
  onChange: (newList: string[]) => void
  disabled?: boolean
}

export function AccessListEditor({ accessList, onChange, disabled = false }: AccessListEditorProps) {
  const [input, setInput] = useState("")
  const [error, setError] = useState<string | null>(null)

  const normalized = (accessList || []).map((e) => e.toLowerCase().trim()).filter(Boolean)

  const addEmail = () => {
    const trimmed = input.trim().toLowerCase()
    if (!trimmed) return
    if (!EMAIL_REGEX.test(trimmed)) {
      setError("Email inválido")
      return
    }
    if (normalized.includes(trimmed)) {
      setError("Email já está na lista")
      return
    }
    onChange([...normalized, trimmed])
    setInput("")
    setError(null)
  }

  const removeEmail = (email: string) => {
    onChange(normalized.filter((e) => e !== email))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      addEmail()
    } else if (e.key === "," || e.key === ";") {
      e.preventDefault()
      addEmail()
    }
  }

  return (
    <div className="space-y-2" data-testid="access-list-editor">
      {!disabled && (
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <Mail className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-tertiary" />
            <input
              type="email"
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                setError(null)
              }}
              onKeyDown={handleKeyDown}
              placeholder="email@empresa.com"
              className="w-full pl-8 pr-2 py-1.5 text-xs rounded-md border border-lia-border-default bg-lia-bg-primary text-lia-text-primary placeholder:text-lia-text-tertiary focus:outline-none focus:ring-1 focus:ring-lia-accent-primary"
              data-testid="access-list-input"
            />
          </div>
          <button
            type="button"
            onClick={addEmail}
            disabled={!input.trim()}
            className={cn(
              "inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
              input.trim()
                ? "bg-lia-accent-primary text-white hover:opacity-90"
                : "bg-lia-bg-tertiary text-lia-text-tertiary cursor-not-allowed"
            )}
            data-testid="access-list-add"
          >
            <Plus className="w-3.5 h-3.5" />
            Adicionar
          </button>
        </div>
      )}

      {error && (
        <p className="text-xs text-status-error" data-testid="access-list-error">{error}</p>
      )}

      <div className="flex flex-wrap gap-1.5">
        {normalized.length === 0 ? (
          <p className="text-xs text-lia-text-tertiary italic">
            {disabled ? "Sem membros adicionais (apenas owner + admin)" : "Adicione emails dos membros do hiring team"}
          </p>
        ) : (
          normalized.map((email) => (
            <div
              key={email}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-xs text-amber-700 dark:text-amber-400"
              data-testid={`access-list-chip-${email}`}
            >
              <Mail className="w-3 h-3" />
              <span>{email}</span>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeEmail(email)}
                  className="ml-0.5 hover:bg-amber-500/20 rounded-sm transition-colors"
                  aria-label={`Remover ${email}`}
                  data-testid={`access-list-remove-${email}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
