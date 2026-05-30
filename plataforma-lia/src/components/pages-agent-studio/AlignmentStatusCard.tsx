"use client"

import { useState, useEffect } from "react"
import { CheckCircle2, Clock, Send, Loader2, XCircle, ChevronDown } from "lucide-react"

interface Job {
  id: string
  title: string
}

interface AlignmentStatusCardProps {
  jobId: string | null
  jobs?: Job[]
}

interface AlignmentState {
  id: string
  status: "pending" | "approved" | "rejected" | "expired"
  manager_email: string
  expires_at: string
  public_url?: string
}

export function AlignmentStatusCard({ jobId, jobs = [] }: AlignmentStatusCardProps) {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(jobId)
  const [alignment, setAlignment] = useState<AlignmentState | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [showForm, setShowForm] = useState(false)

  // Sync if parent supplies jobId after initial render
  useEffect(() => {
    if (jobId && !selectedJobId) setSelectedJobId(jobId)
  }, [jobId])

  useEffect(() => {
    if (!selectedJobId) { setLoading(false); return }
    setAlignment(null)
    setShowForm(false)
    setLoading(true)
    fetch(
      `/api/backend-proxy/manager-alignments?job_vacancy_id=${encodeURIComponent(selectedJobId)}&limit=1`,
      { credentials: "include" }
    )
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        const list = Array.isArray(data?.alignments) ? data.alignments : []
        if (list.length > 0) setAlignment(list[0])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [selectedJobId])

  const handleRequest = async () => {
    if (!email || !selectedJobId) return
    setActionLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/manager-alignments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_vacancy_id: selectedJobId,
          manager_email: email,
          manager_name: name || undefined,
        }),
      })
      if (!res.ok) {
        const e = await res.json()
        throw new Error(e.detail || "Erro ao solicitar alinhamento")
      }
      const data = await res.json()
      setAlignment(data)
      setShowForm(false)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao solicitar")
    } finally {
      setActionLoading(false)
    }
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
          <span className="text-xs">Verificando alinhamentos...</span>
        </div>
      </div>
    )
  }

  if (alignment) {
    const isPending = alignment.status === "pending"
    const isApproved = alignment.status === "approved"
    const isRejected = alignment.status === "rejected"
    const isExpired = alignment.status === "expired"

    return (
      <div>
        {jobSelector}
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-3 rounded-xl border border-[#E5E7EB] p-3.5 bg-[#F9FAFB]">
            <div className="flex-shrink-0">
              {isApproved && <CheckCircle2 className="w-5 h-5 text-[#5DA47A]" />}
              {isPending && <Clock className="w-5 h-5 text-[#D19960]" />}
              {(isRejected || isExpired) && <XCircle className="w-5 h-5 text-[#9CA3AF]" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[#030712]">
                {isApproved && "Vaga aprovada pelo gestor"}
                {isPending && "Aguardando resposta do gestor"}
                {isRejected && "Não aprovada pelo gestor"}
                {isExpired && "Link expirado"}
              </p>
              <p className="text-xs text-[#6B7280] truncate">{alignment.manager_email}</p>
            </div>
          </div>

          {isPending && alignment.public_url && (
            <div className="rounded-lg border border-[#E5E7EB] p-3 bg-white">
              <p className="text-xs text-[#6B7280] mb-1">Link de alinhamento:</p>
              <p className="text-xs font-mono text-[#4B5563] break-all select-all">
                {typeof window !== "undefined" ? `${window.location.origin}${alignment.public_url}` : alignment.public_url}
              </p>
            </div>
          )}

          {(isRejected || isExpired) && (
            <button
              type="button"
              onClick={() => { setAlignment(null); setShowForm(true) }}
              className="text-xs text-[#60BED1] hover:underline"
            >
              Enviar novo pedido
            </button>
          )}
        </div>
      </div>
    )
  }

  if (!showForm) {
    return (
      <div>
        {jobSelector}
        <div className="p-4 space-y-3">
          <p className="text-xs text-[#6B7280] max-w-md">
            Solicite a aprovação do gestor antes de iniciar a prospecção. Um link de alinhamento será enviado para o e-mail indicado.
          </p>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 text-sm font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-4 py-2 transition-colors"
          >
            <Send className="w-4 h-4" />
            Solicitar alinhamento
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      {jobSelector}
      <div className="p-4 space-y-4">
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[#4B5563] mb-1">E-mail do gestor *</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="gestor@empresa.com"
              className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#4B5563] mb-1">Nome (opcional)</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Nome do gestor"
              className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF]"
            />
          </div>
        </div>

        {error && <p className="text-xs text-[#EF4444]">{error}</p>}

        <div className="flex gap-2">
          <button
            type="button"
            disabled={actionLoading || !email}
            onClick={handleRequest}
            className="flex items-center gap-2 text-sm font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-4 py-2 transition-colors disabled:opacity-50"
          >
            {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Enviar link
          </button>
          <button
            type="button"
            onClick={() => setShowForm(false)}
            className="text-sm text-[#6B7280] hover:text-[#030712] px-3 py-2 transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}
