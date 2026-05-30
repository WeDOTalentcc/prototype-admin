"use client"

import { useState, useEffect } from "react"
import { Star, Send, Loader2, ChevronDown } from "lucide-react"

interface Job {
  id: string
  title: string
}

interface NpsStatusCardProps {
  jobId: string | null
  jobs?: Job[]
}

interface Survey {
  id: string
  respondent_type: string
  respondent_email: string
  status: string
  score: number | null
  responded_at: string | null
  public_url: string
}

const RESPONDENT_LABEL: Record<string, string> = {
  candidate: "Candidato",
  manager: "Gestor",
}

const STATUS_COLOR: Record<string, string> = {
  pending: "text-[#D19960]",
  responded: "text-[#5DA47A]",
  expired: "text-[#9CA3AF]",
}

export function NpsStatusCard({ jobId, jobs = [] }: NpsStatusCardProps) {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(jobId)
  const [surveys, setSurveys] = useState<Survey[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [email, setEmail] = useState("")
  const [type, setType] = useState<"candidate" | "manager">("candidate")

  // Sync if parent supplies jobId after initial render
  useEffect(() => {
    if (jobId && !selectedJobId) setSelectedJobId(jobId)
  }, [jobId])

  const loadSurveys = async (jid: string) => {
    setLoading(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/hiring-nps?job_vacancy_id=${encodeURIComponent(jid)}&limit=20`,
        { credentials: "include" }
      )
      if (res.ok) {
        const data = await res.json()
        setSurveys(Array.isArray(data?.surveys) ? data.surveys : [])
      }
    } catch { /* silently skip */ }
    finally { setLoading(false) }
  }

  useEffect(() => {
    if (!selectedJobId) { setLoading(false); return }
    setSurveys([])
    setShowForm(false)
    loadSurveys(selectedJobId)
  }, [selectedJobId])

  const handleSend = async () => {
    if (!email.trim() || !selectedJobId) return
    setActionLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/hiring-nps", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_vacancy_id: selectedJobId,
          respondent_type: type,
          respondent_email: email.trim(),
        }),
      })
      if (!res.ok) {
        const e = await res.json()
        throw new Error(e.detail || "Erro ao enviar pesquisa")
      }
      setShowForm(false)
      setEmail("")
      await loadSurveys(selectedJobId)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao enviar")
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
          <span className="text-xs">Carregando pesquisas...</span>
        </div>
      </div>
    )
  }

  const respondedSurveys = surveys.filter(s => s.score !== null)
  const avgScore = respondedSurveys.length > 0
    ? (respondedSurveys.reduce((acc, s) => acc + (s.score ?? 0), 0) / respondedSurveys.length).toFixed(1)
    : null

  return (
    <div>
      {jobSelector}
      <div className="p-4 space-y-3">
        {surveys.length > 0 && avgScore && (
          <div className="flex items-center gap-3 rounded-xl border border-[#E5E7EB] p-3 bg-[#F9FAFB]">
            <Star className="w-5 h-5 text-[#D19960] flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-[#030712]">{avgScore}/10 média NPS</p>
              <p className="text-[10px] text-[#9CA3AF]">
                {respondedSurveys.length} de {surveys.length} respondidas
              </p>
            </div>
          </div>
        )}

        {surveys.length === 0 && !showForm && (
          <div className="space-y-2">
            <p className="text-xs text-[#6B7280] max-w-md">
              Envie pesquisas de satisfação para candidatos e gestores após o processo de contratação.
            </p>
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 text-sm font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-4 py-2 transition-colors"
            >
              <Send className="w-4 h-4" />
              Enviar pesquisa NPS
            </button>
          </div>
        )}

        {surveys.length > 0 && (
          <div className="space-y-1.5">
            {surveys.slice(0, 5).map(s => (
              <div
                key={s.id}
                className="flex items-center gap-3 rounded-lg border border-[#E5E7EB] px-3 py-2 bg-white"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-[#030712] truncate">
                    {RESPONDENT_LABEL[s.respondent_type] ?? s.respondent_type} — {s.respondent_email}
                  </p>
                  <p className={`text-[10px] ${STATUS_COLOR[s.status] ?? "text-[#9CA3AF]"}`}>
                    {s.status === "responded" && s.score !== null
                      ? `Nota ${s.score}/10`
                      : s.status === "pending"
                      ? "Aguardando resposta"
                      : "Expirada"}
                  </p>
                </div>
              </div>
            ))}
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="text-xs text-[#60BED1] hover:underline"
            >
              + Enviar nova pesquisa
            </button>
          </div>
        )}

        {showForm && (
          <div className="rounded-xl border border-[#E5E7EB] p-4 space-y-3 bg-white">
            <p className="text-xs font-semibold text-[#030712]">Nova pesquisa NPS</p>

            <div className="flex gap-2">
              {(["candidate", "manager"] as const).map(t => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors border
                    ${type === t
                      ? "bg-[#60BED1] text-white border-[#60BED1]"
                      : "bg-white text-[#6B7280] border-[#E5E7EB] hover:border-[#60BED1]/40"}`}
                >
                  {RESPONDENT_LABEL[t]}
                </button>
              ))}
            </div>

            <div>
              <label className="block text-[10px] font-medium text-[#4B5563] mb-1">E-mail *</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder={type === "candidate" ? "candidato@email.com" : "gestor@empresa.com"}
                className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF]"
              />
            </div>

            {error && <p className="text-[10px] text-[#EF4444]">{error}</p>}

            <div className="flex gap-2">
              <button
                type="button"
                disabled={!email.trim() || actionLoading}
                onClick={handleSend}
                className="flex items-center gap-1.5 text-xs font-medium text-white bg-[#60BED1] hover:bg-[#4fa8bc] rounded-lg px-3 py-2 transition-colors disabled:opacity-50"
              >
                {actionLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                Enviar link
              </button>
              <button
                type="button"
                onClick={() => { setShowForm(false); setError(null) }}
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
