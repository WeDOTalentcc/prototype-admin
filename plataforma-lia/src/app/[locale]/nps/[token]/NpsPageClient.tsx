"use client"

import { useState, useEffect } from "react"
import { CheckCircle2, Loader2 } from "lucide-react"

interface NpsContext {
  nps_id: string
  status: string
  respondent_type: "candidate" | "manager"
  job: { id: string; title?: string }
  expires_at: string
  already_responded?: boolean
  score?: number
}

const SCORE_LABELS: Record<number, string> = {
  0: "Péssimo", 1: "Muito ruim", 2: "Ruim", 3: "Abaixo do esperado",
  4: "Regular", 5: "Neutro", 6: "Razoável",
  7: "Bom", 8: "Muito bom", 9: "Ótimo", 10: "Excelente",
}

function scoreColor(score: number): string {
  if (score <= 6) return "bg-[#EF4444] text-white"
  if (score <= 8) return "bg-[#D19960] text-white"
  return "bg-[#5DA47A] text-white"
}

export function NpsPageClient({ token }: { token: string }) {
  const [ctx, setCtx] = useState<NpsContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [comment, setComment] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    fetch(`/api/backend-proxy/hiring-nps/respond?token=${encodeURIComponent(token)}`)
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
    if (selected === null || !ctx) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/backend-proxy/hiring-nps/${ctx.nps_id}/respond`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, score: selected, comment: comment || undefined }),
      })
      if (!res.ok) {
        const e = await res.json().catch(() => ({}))
        throw new Error(e.detail || "Erro ao enviar resposta")
      }
      setDone(true)
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

  if (ctx?.already_responded || done) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB] px-4">
        <div className="max-w-sm text-center space-y-4">
          <CheckCircle2 className="w-12 h-12 text-[#5DA47A] mx-auto" />
          <p className="text-xl font-semibold text-[#030712]">Obrigado pelo feedback!</p>
          <p className="text-sm text-[#6B7280]">
            Sua avaliação foi registrada e vai nos ajudar a melhorar o processo.
          </p>
          {ctx?.score !== undefined && (
            <span className={`inline-block px-4 py-2 rounded-full text-sm font-bold ${scoreColor(ctx.score)}`}>
              Nota {ctx.score}/10
            </span>
          )}
        </div>
      </div>
    )
  }

  const isCandidate = ctx?.respondent_type === "candidate"
  const jobTitle = ctx?.job?.title ?? "a vaga"

  return (
    <div className="min-h-screen bg-[#F9FAFB] px-4 py-12 flex items-start justify-center">
      <div className="w-full max-w-lg space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[#60BED1]">WeDo Talent</p>
          <h1 className="text-2xl font-bold text-[#030712]">
            {isCandidate ? "Como foi sua experiência?" : "Avalie o processo de recrutamento"}
          </h1>
          <p className="text-sm text-[#6B7280]">
            {isCandidate
              ? `Referente ao processo seletivo para ${jobTitle}.`
              : `Referente ao recrutamento para ${jobTitle}.`}
          </p>
        </div>

        {/* Score selector */}
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-5">
          <p className="text-sm font-medium text-[#030712]">
            De 0 a 10, como você avalia sua experiência?
          </p>
          <div className="flex gap-1.5 flex-wrap justify-center">
            {Array.from({ length: 11 }, (_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setSelected(i)}
                className={`w-10 h-10 rounded-xl text-sm font-semibold transition-all
                  ${selected === i
                    ? scoreColor(i) + " scale-110 ring-2 ring-offset-1 ring-current"
                    : "bg-[#F3F4F6] text-[#4B5563] hover:bg-[#E5E7EB]"
                  }`}
              >
                {i}
              </button>
            ))}
          </div>
          {selected !== null && (
            <p className="text-center text-sm font-medium text-[#4B5563]">
              {SCORE_LABELS[selected]}
            </p>
          )}

          <div>
            <label className="block text-xs font-medium text-[#4B5563] mb-1.5">
              Comentário (opcional)
            </label>
            <textarea
              value={comment}
              onChange={e => setComment(e.target.value)}
              rows={3}
              placeholder="O que poderia ter sido melhor? O que foi destaque?"
              className="w-full rounded-xl border border-[#E5E7EB] px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#60BED1]/30 text-[#030712] placeholder:text-[#9CA3AF] resize-none"
            />
          </div>

          <button
            type="button"
            disabled={selected === null || submitting}
            onClick={handleSubmit}
            className="w-full flex items-center justify-center gap-2 bg-[#60BED1] hover:bg-[#4fa8bc] text-white font-semibold rounded-xl px-4 py-3 transition-colors disabled:opacity-50"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Enviar avaliação
          </button>
        </div>

        <p className="text-center text-[10px] text-[#9CA3AF]">
          Link válido até {ctx ? new Date(ctx.expires_at).toLocaleDateString("pt-BR") : "—"}
        </p>
      </div>
    </div>
  )
}
