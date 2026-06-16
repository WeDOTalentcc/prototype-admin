/**
 * useAiPersona — hook canonical para tab "Personalidade da IA"
 * em Minha Empresa (E2.4 audit 2026-05-21).
 *
 * Carrega/atualiza {name, tone} via /api/backend-proxy/company-ai-persona.
 * Erros 422 do validator backend são surfaceados como objetos estruturados
 * pro UI renderizar inline. Erros 5xx genéricos viram mensagem fallback.
 */
"use client"

import { useCallback, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
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
  const { data, isLoading, error } = useQuery<AiPersonaOptions>({
    queryKey: ["company-ai-persona", "options"],
    queryFn: async () => {
      const res = await fetchWithRetry(
        "/api/backend-proxy/company-ai-persona/options",
      )
      if (!res.ok) {
        throw new Error(
          `Falha ao carregar catalogo de tons (HTTP ${res.status})`,
        )
      }
      return (await res.json()) as AiPersonaOptions
    },
    staleTime: 5 * 60_000,
  })
  return {
    options: data ?? null,
    isLoading,
    error: error
      ? error instanceof Error
        ? error.message
        : "Falha ao carregar catalogo de tons"
      : null,
  }
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

const DEFAULT_PERSONA: AiPersona = { name: "IA", tone: "profissional" }

export function useAiPersona(): UseAiPersonaResult {
  const queryClient = useQueryClient()
  const [validationErrors, setValidationErrors] = useState<
    AiPersonaValidationError[]
  >([])
  const [saveError, setSaveError] = useState<string | null>(null)

  const {
    data,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery<AiPersona>({
    queryKey: ["company-ai-persona"],
    queryFn: async () => {
      const res = await fetchWithRetry("/api/backend-proxy/company-ai-persona")
      if (!res.ok) {
        if (res.status === 404 || res.status === 422) return DEFAULT_PERSONA
        throw new Error(`Falha ao carregar persona (HTTP ${res.status})`)
      }
      return (await res.json()) as AiPersona
    },
  })

  const reload = useCallback(async () => {
    await refetch()
  }, [refetch])

  const mutation = useMutation<AiPersona, Error, Partial<AiPersona>>({
    mutationFn: async (patch) => {
      const res = await apiFetch("/api/backend-proxy/company-ai-persona", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      })
      if (res.status === 422) {
        const body = await res.json().catch(() => null)
        const detail = body?.detail
        const errors: AiPersonaValidationError[] = detail?.errors ?? [
          { code: "unknown", message: "Erro de validacao" },
        ]
        const e = new Error("validation") as Error & {
          validationErrors?: AiPersonaValidationError[]
        }
        e.validationErrors = errors
        throw e
      }
      if (!res.ok) {
        throw new Error(`Falha ao salvar (HTTP ${res.status})`)
      }
      return (await res.json()) as AiPersona
    },
    onSuccess: (saved, patch) => {
      queryClient.setQueryData(["company-ai-persona"], saved)
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("lia:settings-updated", {
            detail: {
              section: "ai_persona",
              actionId: "configure_ai_persona",
              field: Object.keys(patch).join("+"),
              value: saved,
              source: "ui",
              ts: Date.now(),
            },
          }),
        )
      }
    },
  })

  const update = useCallback(
    async (patch: Partial<AiPersona>): Promise<boolean> => {
      setValidationErrors([])
      setSaveError(null)
      try {
        await mutation.mutateAsync(patch)
        return true
      } catch (err) {
        const ve = (err as { validationErrors?: AiPersonaValidationError[] })
          .validationErrors
        if (ve) {
          setValidationErrors(ve)
          return false
        }
        setSaveError(err instanceof Error ? err.message : "Falha ao salvar")
        return false
      }
    },
    [mutation],
  )

  const persona = data ?? (queryError ? DEFAULT_PERSONA : null)
  const loadError = queryError
    ? queryError instanceof Error
      ? queryError.message
      : "Falha ao carregar persona"
    : null

  return {
    persona,
    isLoading,
    isSaving: mutation.isPending,
    error: saveError ?? loadError,
    validationErrors,
    reload,
    update,
  }
}
