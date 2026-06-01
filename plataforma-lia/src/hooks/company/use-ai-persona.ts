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

/**
 * @deprecated F3.2 audit 2026-05-24 — use `useAiPersonaOptions()` para
 * obter o catálogo canonical do backend. Esta constante existia como
 * espelho local de CANONICAL_AI_TONES (backend) e criava drift garantido.
 * Mantida temporariamente para não quebrar consumidores que ainda não
 * migraram. Próxima sprint: remover quando 0 imports remanescentes.
 */
export const CANONICAL_TONES: AiPersonaTone[] = [
  "profissional",
  "amigavel",
  "formal",
  "casual",
  "formal_amigavel",
  "empatico",
]

// ---------------------------------------------------------------------------
// useAiPersonaOptions — catálogo canonical (tons + name constraints)
// ---------------------------------------------------------------------------

/**
 * Single tone canonical retornado pelo backend.
 * Schema espelha `ToneOption` em `lia-agent-system/app/api/v1/company_ai_persona.py`.
 */
export interface ToneOption {
  value: string
  label_pt: string
  short_pt: string
  instruction: string
  preview_message_pt: string
  preview_chat_pt: string
}

/**
 * Constraints de nome (min/max length + blocklist de marcas IA terceiras).
 * Backend é defense-in-depth: re-valida no PUT. Frontend usa para warning inline.
 */
export interface NameConstraints {
  min_length: number
  max_length: number
  blocked_brand_tokens: string[]
}

export interface AiPersonaOptions {
  tones: ToneOption[]
  name_constraints: NameConstraints
}

interface UseAiPersonaOptionsResult {
  options: AiPersonaOptions | null
  isLoading: boolean
  error: string | null
}

/**
 * Carrega o catálogo canonical (tons + name constraints) do backend.
 *
 * Fail-loud (REGRA 4 anti-silent-fallback): se o fetch falhar, `options`
 * fica `null` e `error` traz a mensagem. UI consumidora DEVE mostrar
 * estado de erro e bloquear interação — nunca renderizar lista vazia
 * silenciosamente.
 */
/**
 * V3.4 (2026-06-01): retry curto em erros TRANSITÓRIOS de gateway (502/503/504)
 * e falhas de rede. Resolve o "Tom de Voz não carrega" causado por janelas de
 * reload do uvicorn (--reload) durante desenvolvimento ativo — o 504 transitório
 * antes "grudava" no estado e exigia refresh manual. Fail-loud preservado: após
 * `attempts` tentativas, propaga o erro (não mascara falha real). Só para GET.
 */
async function fetchWithRetry(
  url: string,
  init?: RequestInit,
  attempts = 3,
): Promise<Response> {
  let lastErr: unknown
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await apiFetch(url, init)
      if ((res.status === 502 || res.status === 503 || res.status === 504) && i < attempts - 1) {
        await new Promise<void>((r) => setTimeout(r, 400 * (i + 1)))
        continue
      }
      return res
    } catch (err) {
      lastErr = err
      if (i < attempts - 1) {
        await new Promise<void>((r) => setTimeout(r, 400 * (i + 1)))
        continue
      }
      throw err
    }
  }
  throw lastErr ?? new Error("fetch failed")
}

export function useAiPersonaOptions(): UseAiPersonaOptionsResult {
  const [options, setOptions] = useState<AiPersonaOptions | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const fetchOptions = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const res = await fetchWithRetry(
          "/api/backend-proxy/company-ai-persona/options",
        )
        if (!res.ok) {
          throw new Error(
            `Falha ao carregar catálogo de tons (HTTP ${res.status})`,
          )
        }
        const data = (await res.json()) as AiPersonaOptions
        if (!cancelled) setOptions(data)
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Falha ao carregar catálogo de tons",
          )
          setOptions(null)
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    void fetchOptions()
    return () => {
      cancelled = true
    }
  }, [])

  return { options, isLoading, error }
}

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
      const res = await fetchWithRetry("/api/backend-proxy/company-ai-persona")
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
