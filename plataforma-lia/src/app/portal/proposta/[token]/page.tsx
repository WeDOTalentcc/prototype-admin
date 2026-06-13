"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams } from "next/navigation"

// ── Types ──────────────────────────────────────────────────────────────────

type OfferPortalView = {
  offer_id: string
  candidate_name: string
  job_title: string
  department: string
  company_name: string
  salary_formatted: string
  currency: string
  start_date: string | null
  response_deadline: string | null
  benefits: Array<{ name?: string; value?: string; [k: string]: unknown }>
  letter_html: string | null
  status: string
  current_round: number
  offer_link: string | null
  viewed_at: string | null
}

type PageState = "loading" | "loaded" | "responding" | "done" | "error" | "expired"

const PROXY_BASE = "/api/backend-proxy/portal/proposta"

// ── Fetch helpers ──────────────────────────────────────────────────────────

async function fetchOffer(token: string): Promise<OfferPortalView> {
  const res = await fetch(`${PROXY_BASE}/${token}`, { cache: "no-store" })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

async function markViewed(token: string) {
  await fetch(`${PROXY_BASE}/${token}/visualizado`, { method: "POST" }).catch(() => {
    // fail-soft — tracking, not critical
  })
}

async function respond(
  token: string,
  acao: "aceitar" | "recusar",
  notas: string | null
): Promise<{ mensagem: string; next_steps: string | null }> {
  const res = await fetch(`${PROXY_BASE}/${token}/responder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ acao, notas: notas || undefined }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Status helpers ─────────────────────────────────────────────────────────

function isResponseAllowed(status: string) {
  return status === "sent" || status === "viewed"
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    draft: "Rascunho",
    sent: "Aguardando resposta",
    viewed: "Visualizada",
    accepted: "Aceita",
    declined: "Recusada",
    expired: "Expirada",
    cancelled: "Cancelada",
    negotiating: "Em negociação",
  }
  return map[status] ?? status
}

// ── Sub-components ─────────────────────────────────────────────────────────

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 gap-4">
      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      <p className="text-gray-500 text-sm">Carregando proposta...</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 gap-4 px-4">
      <div className="text-4xl">⚠️</div>
      <h1 className="text-xl font-semibold text-gray-800">Proposta não encontrada</h1>
      <p className="text-gray-500 text-sm text-center max-w-sm">
        {message.includes("404") || message.includes("não encontrada") || message.includes("inválido")
          ? "Este link de proposta é inválido ou expirou. Verifique se você acessou o link correto."
          : message}
      </p>
    </div>
  )
}

function DoneState({
  acao,
  mensagem,
  nextSteps,
}: {
  acao: "aceitar" | "recusar"
  mensagem: string
  nextSteps: string | null
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 gap-6 px-4">
      <div className="text-5xl">{acao === "aceitar" ? "🎉" : "✅"}</div>
      <h1 className="text-2xl font-bold text-gray-800">
        {acao === "aceitar" ? "Proposta aceita!" : "Resposta enviada"}
      </h1>
      <p className="text-gray-600 text-center max-w-sm">{mensagem}</p>
      {nextSteps && (
        <p className="text-gray-500 text-sm text-center max-w-sm">{nextSteps}</p>
      )}
    </div>
  )
}

function BenefitItem({ benefit }: { benefit: OfferPortalView["benefits"][number] }) {
  const name = benefit.name ?? (benefit as { label?: string }).label ?? String(Object.values(benefit)[0] ?? "Benefício")
  const value = benefit.value ?? (benefit as { amount?: string }).amount
  return (
    <li className="flex items-start gap-2 text-gray-700 text-sm">
      <span className="text-green-500 mt-0.5">✓</span>
      <span>
        {name}
        {value ? `: ${value}` : ""}
      </span>
    </li>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function OfferPortalPage() {
  const params = useParams()
  const token = typeof params?.token === "string" ? params.token : ""

  const [state, setState] = useState<PageState>("loading")
  const [offer, setOffer] = useState<OfferPortalView | null>(null)
  const [errorMsg, setErrorMsg] = useState("")
  const [doneAcao, setDoneAcao] = useState<"aceitar" | "recusar">("aceitar")
  const [doneMensagem, setDoneMensagem] = useState("")
  const [doneNextSteps, setDoneNextSteps] = useState<string | null>(null)
  const [notes, setNotes] = useState("")
  const [showDeclineForm, setShowDeclineForm] = useState(false)
  const [respondError, setRespondError] = useState("")

  useEffect(() => {
    if (!token) {
      setState("error")
      setErrorMsg("Token de proposta ausente.")
      return
    }
    fetchOffer(token)
      .then((data) => {
        setOffer(data)
        setState("loaded")
        if (isResponseAllowed(data.status)) {
          markViewed(token)
        }
      })
      .catch((e: Error) => {
        setState("error")
        setErrorMsg(e.message)
      })
  }, [token])

  const handleAccept = useCallback(async () => {
    if (!token) return
    setState("responding")
    setRespondError("")
    try {
      const result = await respond(token, "aceitar", null)
      setDoneAcao("aceitar")
      setDoneMensagem(result.mensagem)
      setDoneNextSteps(result.next_steps)
      setState("done")
    } catch (e: unknown) {
      setState("loaded")
      setRespondError(e instanceof Error ? e.message : "Erro ao enviar resposta.")
    }
  }, [token])

  const handleDecline = useCallback(async () => {
    if (!token) return
    setState("responding")
    setRespondError("")
    try {
      const result = await respond(token, "recusar", notes || null)
      setDoneAcao("recusar")
      setDoneMensagem(result.mensagem)
      setDoneNextSteps(result.next_steps)
      setState("done")
    } catch (e: unknown) {
      setState("loaded")
      setRespondError(e instanceof Error ? e.message : "Erro ao enviar resposta.")
    }
  }, [token, notes])

  if (state === "loading") return <LoadingState />
  if (state === "error") return <ErrorState message={errorMsg} />
  if (state === "done")
    return <DoneState acao={doneAcao} mensagem={doneMensagem} nextSteps={doneNextSteps} />
  if (!offer) return <LoadingState />

  const canRespond = isResponseAllowed(offer.status) && state !== "responding"
  const alreadyResponded = offer.status === "accepted" || offer.status === "declined"

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
                {offer.company_name}
              </p>
              <h1 className="text-2xl font-bold text-gray-900">{offer.job_title}</h1>
              {offer.department && (
                <p className="text-sm text-gray-500 mt-0.5">{offer.department}</p>
              )}
            </div>
            <span
              className={`shrink-0 px-3 py-1 rounded-full text-xs font-medium ${
                offer.status === "accepted"
                  ? "bg-green-100 text-green-700"
                  : offer.status === "declined"
                  ? "bg-red-100 text-red-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {statusLabel(offer.status)}
            </span>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-50">
            <p className="text-gray-700">
              Olá, <strong>{offer.candidate_name}</strong>! Você recebeu uma proposta de emprego.
            </p>
          </div>
        </div>

        {/* Details */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Detalhes da Proposta
          </h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-400">Remuneração</p>
              <p className="text-lg font-semibold text-gray-900">{offer.salary_formatted}</p>
            </div>

            {offer.start_date && (
              <div>
                <p className="text-xs text-gray-400">Data de início</p>
                <p className="text-base font-medium text-gray-800">{offer.start_date}</p>
              </div>
            )}

            {offer.response_deadline && (
              <div>
                <p className="text-xs text-gray-400">Responder até</p>
                <p className="text-base font-medium text-gray-800">{offer.response_deadline}</p>
              </div>
            )}

            {offer.current_round > 0 && (
              <div>
                <p className="text-xs text-gray-400">Rodada de negociação</p>
                <p className="text-base font-medium text-gray-800">{offer.current_round}</p>
              </div>
            )}
          </div>

          {/* Benefits */}
          {offer.benefits.length > 0 && (
            <div className="pt-2">
              <p className="text-xs text-gray-400 mb-2">Benefícios</p>
              <ul className="space-y-1">
                {offer.benefits.map((b, i) => (
                  <BenefitItem key={i} benefit={b} />
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Letter */}
        {offer.letter_html && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Carta de Oferta
            </h2>
            <div
              className="prose prose-sm max-w-none text-gray-700"
              dangerouslySetInnerHTML={{ __html: offer.letter_html }}
            />
          </div>
        )}

        {/* Response area */}
        {canRespond && !alreadyResponded && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Sua Resposta
            </h2>

            {respondError && (
              <div className="bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-700">
                {respondError}
              </div>
            )}

            {!showDeclineForm ? (
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleAccept}
                  disabled={state === "responding"}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
                >
                  {state === "responding" ? "Enviando..." : "Aceitar Proposta"}
                </button>
                <button
                  onClick={() => setShowDeclineForm(true)}
                  disabled={state === "responding"}
                  className="flex-1 bg-white hover:bg-gray-50 disabled:bg-gray-50 border border-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-xl transition-colors"
                >
                  Recusar
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  Você pode deixar uma mensagem opcional antes de recusar.
                </p>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Motivo (opcional)..."
                  rows={3}
                  maxLength={2000}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex gap-3">
                  <button
                    onClick={handleDecline}
                    disabled={state === "responding"}
                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
                  >
                    {state === "responding" ? "Enviando..." : "Confirmar Recusa"}
                  </button>
                  <button
                    onClick={() => setShowDeclineForm(false)}
                    disabled={state === "responding"}
                    className="border border-gray-200 text-gray-600 font-medium py-3 px-6 rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    Voltar
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Already responded */}
        {alreadyResponded && (
          <div
            className={`rounded-2xl border p-5 text-center ${
              offer.status === "accepted"
                ? "bg-green-50 border-green-100 text-green-800"
                : "bg-gray-50 border-gray-100 text-gray-600"
            }`}
          >
            {offer.status === "accepted"
              ? "Você já aceitou esta proposta. Aguarde o contato do recrutador."
              : "Você já recusou esta proposta."}
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-xs text-gray-400 pb-6">
          Esta proposta foi enviada via WeDOTalent. Seus dados são tratados conforme a LGPD.
        </p>
      </div>
    </main>
  )
}
