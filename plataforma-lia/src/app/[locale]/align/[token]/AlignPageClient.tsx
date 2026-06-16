"use client"

import { useState, useEffect } from "react"
import { CheckCircle2, XCircle, Loader2, Briefcase } from "lucide-react"

interface AlignContext {
  alignment_id: string
  status: string
  job: { id: string; title?: string; department?: string; seniority?: string }
  manager_name?: string
  expires_at: string
  already_responded?: boolean
  responded_at?: string
}

export function AlignPageClient({ token }: { token: string }) {
  const [ctx, setCtx] = useState<AlignContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [decision, setDecision] = useState<"approved" | "rejected" | null>(null)
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState<"approved" | "rejected" | null>(null)

  useEffect(() => {
    fetch(`/api/backend-proxy/manager-alignments/respond?token=${encodeURIComponent(token)}`)
      .then(async r => {
        if (!r.ok) {
          const e = await r.json().catch(() => ({}))
          throw new Error(e.detail || (r.status === 410 ? "Este link expirou." : "Link inválido."))
        }
        return r.json()
      })
      .then(setCtx)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  const handleSubmit = async () => {
    if (!decision || !ctx) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/backend-proxy/manager-alignments/${ctx.alignment_id}/respond`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, status: decision, response_notes: notes || undefined }),
      })
      if (!res.ok) {
        const e = await res.json().catch(() => ({}))
        throw new Error(e.detail || "Erro ao enviar resposta")
      }
      setDone(decision)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erro ao enviar")
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB]">
        <Loader2 className="w-6 h-6 animate-spin text-[#60BED1]" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB] px-4">
        <div className="max-w-sm text-center space-y-3">
          <p className="text-lg font-semibold text-[#030712]">Link indisponível</p>
          <p className="text-sm text-[#6B7280]">{error}</p>
        </div>
      </div>
    )
  }

  const respondedStatus = done ?? (ctx?.already_responded ? ctx.status : null)
  if (respondedStatus) {
    const approved = respondedStatus === "approved"
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB] px-4">
        <div className="max-w-sm text-center space-y-4">
          {approved
            ? <CheckCircle2 className="w-12 h-12 text-[#5DA47A] mx-auto" />
            : <XCircle className="w-12 h-12 text-[#EF4444] mx-auto" />}
          <p className="text-xl font-semibold text-[#030712]">
            {approved ? "Vaga aprovada" : "Vaga reprovada"}
          </p>
          <p className="text-sm text-[#6B7280]">
            {approved
              ? "Obrigado! O recrutador foi notificado e o sourcing pode iniciar."
              : "Obrigado pelo retorno. O recrutador foi notificado da sua decisão."}
          </p>
        </div>
      </div>
    )
  }

  const jobTitle = ctx?.job?.title ?? "esta vaga"
  const greeting = ctx?.manager_name ? `Olá, ${ctx.manager_name}` : "Olá"

  return (
    <div className="min-h-screen bg-[#F9FAFB] px-4 py-12 flex items-start justify-center">
      <div className="w-full max-w-lg space-y-8">
        <div className="text-center space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[#60BED1]">WeDo Talent</p>
          <h1 className="text-2xl font-bold text-[#030712]">Aprovação de vaga</h1>
          <p className="text-sm text-[#6B7280]">
            {greeting}, sua aprovação é necessária para iniciar a busca de candidatos.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-5">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#60BED1]/10 flex items-center justify-center shrink-0">
              <Briefcase className="w-5 h-5 text-[#60BED1]" />
            </div>
            <div className="min-w-0">
              <p className="text-base font-semibold text-[#030712] truncate">{jobTitle}</p>
              <p className="text-xs text-[#6B7280]">
                {[ctx?.job?.department, ctx?.job?.seniority].filter(Boolean).join(" · ") || "Detalhes da vaga"}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setDecision("approved")}
              className={`flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-all border
                ${decision === "approved"
                  ? "bg-[#5DA47A] text-white border-[#5DA47A] ring-2 ring-offset-1 ring-[#5DA47A]"
                  : "bg-white text-[#5DA47A] border-[#5DA47A]/40 hover:bg-[#5DA47A]/5"}`}
            >
              <CheckCircle2 className="w-4 h-4" /> Aprovar
            </button>
            <button
              type="button"
              onClick={() => setDecision("rejected")}
              className={`flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-all border
                ${decision === "rejected"
                  ? "bg-[#EF4444] text-white border-[#EF4444] ring-2 ring-offset-1 ring-[#EF4444]"
                  : "bg-white text-[#EF4444] border-[#EF4444]/40 hover:bg-[#EF4444]/5"}`}
            >
              <XCircle className="w-4 h-4" /> Reprovar
            </button>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#4B5563] mb-1.5">
              Observações (opcional)
            </label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              placeholder="Ajustes na vaga, condições, contexto para o recrutador..."
              className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF] resize-none"
            />
          </div>

          <button
            type="button"
            disabled={decision === null || submitting}
            onClick={handleSubmit}
            className="w-full flex items-center justify-center gap-2 bg-[#60BED1] hover:bg-[#4fa8bc] text-white font-semibold rounded-xl px-4 py-3 transition-colors disabled:opacity-50"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Confirmar decisão
          </button>
        </div>

        <p className="text-center text-[10px] text-[#9CA3AF]">
          Link válido até {ctx ? new Date(ctx.expires_at).toLocaleDateString("pt-BR") : "—"}
        </p>
      </div>
    </div>
  )
}
