"use client"

import { useState } from "react"
import { Phone, Loader2, X, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import type { Candidate } from "@/components/pages/candidates/types"

interface TwilioCallButtonProps {
  candidate: Candidate
  jobTitle?: string
  jobId?: string
  companyId?: string
}

interface InitiateState {
  loading: boolean
  error: string | null
  success: {
    sessionId: string
    callSid: string | null
    status: string
    fallbackChannel?: string | null
  } | null
}

/**
 * Task #425 — recruiter-side trigger for an automatic Twilio PSTN screening call.
 *
 * Surfaced in the triagem details footer. Renders a button that opens a
 * confirmation modal showing the candidate's phone (no silent dial). On
 * confirm, calls the Next.js proxy `/api/backend-proxy/twilio-voice/initiate`
 * and reports success/failure explicitly via toast + inline state.
 */
export function TwilioCallButton({ candidate, jobTitle, jobId, companyId }: TwilioCallButtonProps) {
  const [open, setOpen] = useState(false)
  const [state, setState] = useState<InitiateState>({ loading: false, error: null, success: null })

  const phone = candidate.phone?.trim()
  const canCall = !!phone && !!companyId

  const handleConfirm = async () => {
    if (!phone || !companyId) return
    setState({ loading: true, error: null, success: null })
    try {
      const res = await fetch("/api/backend-proxy/twilio-voice/initiate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidate.id,
          candidate_name: candidate.name,
          phone_number: phone,
          job_title: jobTitle || candidate.role || "Triagem",
          company_id: companyId,
          job_id: jobId,
          language: "pt-BR",
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || data?.success === false) {
        const message =
          data?.detail?.message ||
          data?.message ||
          data?.error ||
          `Falha ao iniciar ligação (HTTP ${res.status})`
        const fallback = data?.fallback_channel || data?.detail?.fallback_channel
        setState({ loading: false, error: String(message), success: null })
        if (fallback) {
          toast.error(
            `Não foi possível iniciar a ligação: ${message}. Canal alternativo sugerido: ${fallback}.`
          )
        } else {
          toast.error(`Não foi possível iniciar a ligação: ${message}`)
        }
        return
      }
      const callSid: string | null = data.call_sid ?? null
      const fallbackChannel: string | null = data.fallback_channel ?? null
      setState({
        loading: false,
        error: null,
        success: {
          sessionId: data.session_id,
          callSid,
          status: data.status ?? "initiated",
          fallbackChannel,
        },
      })
      // Task #425 — surface call_sid explicitly so recruiter can correlate the
      // dial in Twilio logs, and announce fallback_channel when backend
      // suggests one (e.g., PSTN unavailable → recommend wa_link).
      const sidPart = callSid ? ` (Call SID: ${callSid})` : ""
      const fbPart = fallbackChannel
        ? ` Canal alternativo disponível: ${fallbackChannel}.`
        : ""
      toast.success(
        `Ligação iniciada${sidPart} — a LIA vai discar para o candidato em instantes.${fbPart}`
      )
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      setState({ loading: false, error: message, success: null })
      toast.error(`Erro de rede ao iniciar ligação: ${message}`)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => { setState({ loading: false, error: null, success: null }); setOpen(true) }}
        disabled={!canCall}
        title={!phone ? "Candidato sem telefone cadastrado" : !companyId ? "Empresa não identificada" : "Iniciar ligação automática Twilio (PSTN)"}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-xl transition-colors motion-reduce:transition-none border border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Phone className="w-3.5 h-3.5" />
        Ligação automática
      </button>

      {open && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar ligação automática"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={() => !state.loading && setOpen(false)}
        >
          <div
            className="w-full max-w-md bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lia-md p-5 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-wedo-orange" />
                <h2 className="text-sm font-semibold text-lia-text-primary">Iniciar ligação automática</h2>
              </div>
              <button
                type="button"
                onClick={() => !state.loading && setOpen(false)}
                aria-label="Fechar"
                className="text-lia-text-tertiary hover:text-lia-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {!state.success ? (
              <>
                <div className="text-xs text-lia-text-secondary leading-relaxed space-y-2">
                  <p>
                    A LIA vai discar para <strong className="text-lia-text-primary">{candidate.name}</strong> no número:
                  </p>
                  <p className="font-['JetBrains_Mono',monospace] text-sm text-lia-text-primary border border-lia-border-subtle rounded-md px-3 py-2 bg-lia-bg-secondary">
                    {phone || "—"}
                  </p>
                  <p className="text-micro text-lia-text-tertiary">
                    A ligação será conduzida em pt-BR e a triagem WSI será aplicada por voz.
                    O consentimento LGPD será verificado antes da chamada.
                  </p>
                </div>

                {state.error && (
                  <div className="flex items-start gap-2 text-xs text-status-error bg-status-error/10 border border-status-error/30 rounded-md p-2.5">
                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                    <span>{state.error}</span>
                  </div>
                )}

                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setOpen(false)}
                    disabled={state.loading}
                    className="px-3 py-1.5 text-xs font-medium rounded-md border border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-tertiary disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={handleConfirm}
                    disabled={state.loading || !canCall}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50"
                  >
                    {state.loading
                      ? <><Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" /> Discando...</>
                      : <><Phone className="w-3.5 h-3.5" /> Confirmar e ligar</>}
                  </button>
                </div>
              </>
            ) : (
              <div className="text-xs text-lia-text-secondary space-y-2">
                <p className="text-status-success font-medium">Ligação iniciada com sucesso.</p>
                <p>Status: <strong>{state.success.status}</strong></p>
                {state.success.callSid && (
                  <p className="font-['JetBrains_Mono',monospace] text-micro text-lia-text-tertiary">
                    Call SID: {state.success.callSid}
                  </p>
                )}
                {state.success.fallbackChannel && (
                  <p className="text-micro text-lia-text-tertiary">
                    Canal alternativo sugerido: <strong>{state.success.fallbackChannel}</strong>
                  </p>
                )}
                <div className="flex justify-end pt-1">
                  <button
                    type="button"
                    onClick={() => setOpen(false)}
                    className="px-3 py-1.5 text-xs font-medium rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
                  >
                    Fechar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
