"use client"

import { useState, useEffect } from "react"
import { CheckCircle2, Clock, Send, Loader2, XCircle, Plus, ChevronDown } from "lucide-react"

interface Job {
  id: string
  title: string
}

interface OfferStatusCardProps {
  jobId: string | null
  jobs?: Job[]
}

interface Offer {
  id: string
  candidate_id: string
  status: string
  salary: number | null
  currency: string
  sent_at: string | null
  responded_at: string | null
  candidate_response: string | null
}

const STATUS_LABEL: Record<string, string> = {
  draft: "Rascunho",
  sent: "Enviada — aguardando resposta",
  accepted: "Aceita pelo candidato",
  rejected: "Recusada pelo candidato",
  withdrawn: "Retirada",
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  draft: <Clock className="w-4 h-4 text-[#D19960]" />,
  sent: <Clock className="w-4 h-4 text-[#60BED1]" />,
  accepted: <CheckCircle2 className="w-4 h-4 text-[#5DA47A]" />,
  rejected: <XCircle className="w-4 h-4 text-[#9CA3AF]" />,
  withdrawn: <XCircle className="w-4 h-4 text-[#D1D5DB]" />,
}

export function OfferStatusCard({ jobId, jobs = [] }: OfferStatusCardProps) {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(jobId)
  const [offers, setOffers] = useState<Offer[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [candidateId, setCandidateId] = useState("")
  const [salary, setSalary] = useState("")

  // Sync if parent supplies jobId after initial render
  useEffect(() => {
    if (jobId && !selectedJobId) setSelectedJobId(jobId)
  }, [jobId])

  const loadOffers = async (jid: string) => {
    setLoading(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/job-offers?job_vacancy_id=${encodeURIComponent(jid)}&limit=20`,
        { credentials: "include" }
      )
      if (res.ok) {
        const data = await res.json()
        setOffers(Array.isArray(data?.offers) ? data.offers : [])
      }
    } catch { /* silently skip */ }
    finally { setLoading(false) }
  }

  useEffect(() => {
    if (!selectedJobId) { setLoading(false); return }
    setOffers([])
    setShowCreate(false)
    loadOffers(selectedJobId)
  }, [selectedJobId])

  const handleCreate = async () => {
    if (!candidateId.trim() || !selectedJobId) return
    setActionLoading("create")
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/job-offers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_vacancy_id: selectedJobId,
          candidate_id: candidateId.trim(),
          salary: salary ? parseFloat(salary) : null,
        }),
      })
      if (!res.ok) {
        const e = await res.json()
        throw new Error(e.detail || "Erro ao criar oferta")
      }
      setShowCreate(false)
      setCandidateId("")
      setSalary("")
      await loadOffers(selectedJobId)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao criar oferta")
    } finally {
      setActionLoading(null)
    }
  }

  const handleAction = async (offerId: string, action: "send" | "withdraw") => {
    setActionLoading(offerId + action)
    try {
      await fetch(`/api/backend-proxy/job-offers/${offerId}/${action}`, {
        method: "PATCH",
        credentials: "include",
      })
      if (selectedJobId) await loadOffers(selectedJobId)
    } catch { /* silently skip */ }
    finally { setActionLoading(null) }
  }

  const jobSelector = jobs.length > 1 ? (
    <div className="px-4 pt-3 pb-1">
      <div className="relative">
        <select
          value={selectedJobId ?? ""}
          onChange={e => setSelectedJobId(e.target.value)}
          className="w-full appearance-none rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 pr-8 text-xs text-[#030712] focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30"
        >
          {jobs.map(j => (
            <option key={j.id} value={j.id}>{j.title || j.id.slice(0, 16) + "…"}</option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#9CA3AF]" />
      </div>
    </div>
  ) : null

  if (loading) {
    return (
      <div>
        {jobSelector}
        <div className="p-4 flex items-center gap-2 text-[#9CA3AF]">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-xs">Carregando ofertas...</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      {jobSelector}
      <div className="p-4 space-y-3">
        {offers.length === 0 && !showCreate && (
          <div className="space-y-2">
            <p className="text-xs text-[#6B7280] max-w-md">
              Registre propostas de oferta para candidatos aprovados nesta vaga.
            </p>
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 text-sm font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-4 py-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Nova oferta
            </button>
          </div>
        )}

        {offers.length > 0 && (
          <div className="space-y-2">
            {offers.map(offer => (
              <div
                key={offer.id}
                className="flex items-center gap-3 rounded-xl border border-[#E5E7EB] p-3 bg-[#F9FAFB]"
              >
                <div className="flex-shrink-0">{STATUS_ICON[offer.status] ?? STATUS_ICON.draft}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#030712] truncate">
                    {STATUS_LABEL[offer.status] ?? offer.status}
                  </p>
                  <p className="text-[10px] text-[#9CA3AF] truncate">
                    Candidato: {offer.candidate_id.slice(0, 8)}…
                    {offer.salary ? ` · R$ ${offer.salary.toLocaleString("pt-BR")}` : ""}
                  </p>
                </div>
                {offer.status === "draft" && (
                  <button
                    type="button"
                    disabled={actionLoading === offer.id + "send"}
                    onClick={() => handleAction(offer.id, "send")}
                    className="text-[10px] font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-md px-2.5 py-1.5 transition-colors disabled:opacity-50 flex items-center gap-1"
                  >
                    {actionLoading === offer.id + "send"
                      ? <Loader2 className="w-3 h-3 animate-spin" />
                      : <Send className="w-3 h-3" />}
                    Enviar
                  </button>
                )}
                {offer.status === "sent" && (
                  <button
                    type="button"
                    disabled={actionLoading === offer.id + "withdraw"}
                    onClick={() => handleAction(offer.id, "withdraw")}
                    className="text-[10px] text-[#9CA3AF] hover:text-[#EF4444] rounded-md px-2 py-1.5 transition-colors disabled:opacity-50"
                  >
                    Retirar
                  </button>
                )}
              </div>
            ))}

            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="text-xs text-[#60BED1] hover:underline"
            >
              + Nova oferta
            </button>
          </div>
        )}

        {showCreate && (
          <div className="rounded-xl border border-[#E5E7EB] p-4 space-y-3 bg-white">
            <p className="text-xs font-semibold text-[#030712]">Nova oferta</p>
            <div>
              <label className="block text-[10px] font-medium text-[#4B5563] mb-1">ID do candidato *</label>
              <input
                type="text"
                value={candidateId}
                onChange={e => setCandidateId(e.target.value)}
                placeholder="UUID do candidato aprovado"
                className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF]"
              />
            </div>
            <div>
              <label className="block text-[10px] font-medium text-[#4B5563] mb-1">Salário (opcional)</label>
              <input
                type="number"
                value={salary}
                onChange={e => setSalary(e.target.value)}
                placeholder="Ex: 8000"
                className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF]"
              />
            </div>
            {error && <p className="text-[10px] text-[#EF4444]">{error}</p>}
            <div className="flex gap-2">
              <button
                type="button"
                disabled={!candidateId.trim() || actionLoading === "create"}
                onClick={handleCreate}
                className="flex items-center gap-1.5 text-xs font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-3 py-2 transition-colors disabled:opacity-50"
              >
                {actionLoading === "create" ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                Criar rascunho
              </button>
              <button
                type="button"
                onClick={() => { setShowCreate(false); setError(null) }}
                className="text-xs text-[#6B7280] hover:text-[#030712] px-3 py-2 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
