"use client"

/**
 * useEmailTemplatePreview — canonical hook para preview de template de email
 * com substituição de variáveis pelo backend.
 *
 * GAP-07-006: Live email template preview with real data.
 *
 * Chama POST /api/backend-proxy/email-templates/[id]/preview com as variáveis
 * fornecidas. Retorna subject/body_html/body_text renderizados e a lista de
 * missing_variables para exibir aviso ao usuário.
 *
 * Pattern: useState + fetch manual (sem React Query — projeto não usa).
 * Renderização só sob demanda (botão Preview), não auto-fetch.
 */

import { useCallback, useState } from "react"

export interface EmailTemplatePreviewRequest {
  variables: Record<string, string>
}

export interface EmailTemplatePreviewData {
  subject: string
  body_html: string
  body_text: string | null
}

export interface EmailTemplatePreviewState {
  /** Rendered preview data (null while loading or before first fetch) */
  preview: EmailTemplatePreviewData | null
  /** Variables present in template but missing from the provided dict */
  missingVariables: string[]
  /** Loading state */
  isLoading: boolean
  /** Error message if request failed */
  error: string | null
}

export interface UseEmailTemplatePreviewReturn extends EmailTemplatePreviewState {
  /**
   * Fetch the rendered preview from the backend.
   * @param templateId UUID or string ID of the template
   * @param variables  Key-value map of variable name → value
   */
  fetchPreview: (templateId: string, variables: Record<string, string>) => Promise<void>
  /** Reset state (e.g. when template changes) */
  reset: () => void
}

const INITIAL_STATE: EmailTemplatePreviewState = {
  preview: null,
  missingVariables: [],
  isLoading: false,
  error: null,
}

/**
 * Calls the preview endpoint and returns the rendered template.
 * Endpoint: POST /api/backend-proxy/email-templates/[id]/preview
 * Response shape (from BE TemplatePreviewByIdResponse):
 *   { success: boolean, data: { subject, body_html, body_text } }
 *
 * Note: the BE endpoint does not return missing_variables — it renders with
 * whatever variables are provided and leaves unfilled placeholders as-is.
 * We compute missing_variables client-side by scanning the rendered output
 * for remaining {{...}} placeholders.
 */
async function callPreviewEndpoint(
  templateId: string,
  variables: Record<string, string>,
): Promise<{ data: EmailTemplatePreviewData; missingVariables: string[] }> {
  const url = `/api/backend-proxy/email-templates/${encodeURIComponent(templateId)}/preview`
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variables }),
  })

  if (res.status === 404) {
    throw new Error("Template não encontrado.")
  }
  if (!res.ok) {
    let detail = `Erro ${res.status}`
    try {
      const body = await res.json()
      detail = body?.detail || body?.message || detail
    } catch {
      // ignore parse error
    }
    throw new Error(detail)
  }

  const body = await res.json()

  // BE returns { success: true, data: { subject, body_html, body_text } }
  const data: EmailTemplatePreviewData = {
    subject: body?.data?.subject ?? body?.subject ?? "",
    body_html: body?.data?.body_html ?? body?.body_html ?? "",
    body_text: body?.data?.body_text ?? body?.body_text ?? null,
  }

  // Detect remaining unfilled placeholders as missing variables
  const allRendered = [data.subject, data.body_html, data.body_text ?? ""].join(" ")
  const remainingMatches = allRendered.matchAll(/\{\{(\w+)\}\}/g)
  const missingVariables = Array.from(
    new Set(Array.from(remainingMatches, (m) => m[1])),
  ).sort()

  return { data, missingVariables }
}

export function useEmailTemplatePreview(): UseEmailTemplatePreviewReturn {
  const [state, setState] = useState<EmailTemplatePreviewState>(INITIAL_STATE)

  const fetchPreview = useCallback(
    async (templateId: string, variables: Record<string, string>) => {
      if (!templateId) {
        setState((prev) => ({ ...prev, error: "ID do template é obrigatório." }))
        return
      }

      setState({ preview: null, missingVariables: [], isLoading: true, error: null })

      try {
        const { data, missingVariables } = await callPreviewEndpoint(templateId, variables)
        setState({ preview: data, missingVariables, isLoading: false, error: null })
      } catch (err) {
        const message = err instanceof Error ? err.message : "Erro ao carregar preview."
        setState({ preview: null, missingVariables: [], isLoading: false, error: message })
      }
    },
    [],
  )

  const reset = useCallback(() => {
    setState(INITIAL_STATE)
  }, [])

  return { ...state, fetchPreview, reset }
}
