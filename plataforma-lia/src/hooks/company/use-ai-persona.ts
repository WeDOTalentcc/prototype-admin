/**
 * useAiPersona — hook canonical para tab "Personalidade da IA"
 * em Minha Empresa (E2.4 audit 2026-05-21).
 *
 * Carrega/atualiza {name, tone} via /api/backend-proxy/company-ai-persona.
 * Erros 422 do validator backend são surfaceados como objetos estruturados
 * pro UI renderizar inline. Erros 5xx genéricos viram mensagem fallback.
 */
"use client"

import { useCallback, useEffect, useState } from "react"
import { apiFetch } from "@/lib/api/api-fetch"

export interface AiPersona {
  name: string
  tone: AiPersonaTone
}

export type AiPersonaTone =
  | "profissional"
  | "amigavel"
  | "formal"
  | "casual"
  | "formal_amigavel"
  | "empatico"

export const CANONICAL_TONES: AiPersonaTone[] = [
  "profissional",
  "amigavel",
  "formal",
  "casual",
  "formal_amigavel",
  "empatico",
]

export interface AiPersonaValidationError {
  code: string
  message: string
  fix?: string
  anchor?: string
}

interface UseAiPersonaResult {
  persona: AiPersona | null
  isLoading: boolean
  isSaving: boolean
  error: string | null
  validationErrors: AiPersonaValidationError[]
  reload: () => Promise<void>
  update: (patch: Partial<AiPersona>) => Promise<boolean>
}

const DEFAULT_PERSONA: AiPersona = { name: "LIA", tone: "profissional" }

export function useAiPersona(): UseAiPersonaResult {
  const [persona, setPersona] = useState<AiPersona | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<
    AiPersonaValidationError[]
  >([])

  const reload = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await apiFetch("/api/backend-proxy/company-ai-persona")
      if (!res.ok) {
        if (res.status === 404 || res.status === 422) {
          setPersona(DEFAULT_PERSONA)
          return
        }
        throw new Error(`Falha ao carregar persona (HTTP ${res.status})`)
      }
      const data = (await res.json()) as AiPersona
      setPersona(data)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao carregar persona",
      )
      setPersona(DEFAULT_PERSONA)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  const update = useCallback(
    async (patch: Partial<AiPersona>): Promise<boolean> => {
      setIsSaving(true)
      setError(null)
      setValidationErrors([])
      try {
        const res = await apiFetch("/api/backend-proxy/company-ai-persona", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(patch),
        })
        if (res.status === 422) {
          // Validator backend: detail.errors[] estruturado em PT-BR.
          const body = await res.json().catch(() => null)
          const detail = body?.detail
          const errors: AiPersonaValidationError[] =
            detail?.errors ?? [
              { code: "unknown", message: "Erro de validação" },
            ]
          setValidationErrors(errors)
          return false
        }
        if (!res.ok) {
          throw new Error(`Falha ao salvar (HTTP ${res.status})`)
        }
        const data = (await res.json()) as AiPersona
        setPersona(data)
        // Bidirectional sync: pode disparar lia:settings-updated pra LIA
        // chat reagir (alinhado com pattern P0-1 do hook canonical).
        if (typeof window !== "undefined") {
          window.dispatchEvent(
            new CustomEvent("lia:settings-updated", {
              detail: {
                section: "ai_persona",
                actionId: "configure_ai_persona",
                field: Object.keys(patch).join("+"),
                value: data,
                source: "ui",
                ts: Date.now(),
              },
            }),
          )
        }
        return true
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao salvar")
        return false
      } finally {
        setIsSaving(false)
      }
    },
    [],
  )

  return {
    persona,
    isLoading,
    isSaving,
    error,
    validationErrors,
    reload,
    update,
  }
}
