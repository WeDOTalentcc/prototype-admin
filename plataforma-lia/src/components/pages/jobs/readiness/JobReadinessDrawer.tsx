"use client"

import React, { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { CheckCircle2, Loader2, Play, XCircle } from "lucide-react"
import { toast } from "sonner"
import {
  approveReadinessStage,
  dispatchReadinessScreening,
  getReadinessJob,
  rejectReadinessStage,
  type AudiencePolicy,
  type ReadinessJobDetail,
  type ReadinessStage,
  type ReadinessTimelineEvent,
} from "@/services/lia-api/readiness-api"

export const STAGE_COLOR: Record<ReadinessStage, string> = {
  importada: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  sem_jd: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  jd_rascunho: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
  jd_enriquecido: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300",
  perguntas_triagem: "bg-fuchsia-50 text-fuchsia-700 dark:bg-fuchsia-950/40 dark:text-fuchsia-300",
  pronta_disparo: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  em_triagem: "bg-cyan-50 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300",
}

export const STAGE_LABEL_PT: Record<ReadinessStage, string> = {
  importada: "Importada",
  sem_jd: "Sem JD",
  jd_rascunho: "JD Rascunho",
  jd_enriquecido: "JD Enriquecido",
  perguntas_triagem: "Perguntas de Triagem",
  pronta_disparo: "Pronta para Disparo",
  em_triagem: "Em Triagem",
}

export const BLOCKER_LABEL: Record<string, string> = {
  missing_jd: "Sem JD",
  missing_enrichment: "Sem enriquecimento",
  missing_competencies: "Sem competências",
  missing_questions: "Sem perguntas",
}

const KNOWN_BLOCKERS = new Set(Object.keys(BLOCKER_LABEL))

export function StageBadge({
  stage,
  className = "",
}: {
  stage: ReadinessStage
  className?: string
}) {
  const tStages = useTranslations("jobs.readinessStages")
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${STAGE_COLOR[stage] || ""} ${className}`}
    >
      {stage in STAGE_LABEL_PT ? tStages(stage) : stage}
    </span>
  )
}

interface JobReadinessDrawerProps {
  jobId: string | null
  onClose: () => void
  onChanged?: () => void
}

export function JobReadinessDrawer({ jobId, onClose, onChanged }: JobReadinessDrawerProps) {
  const tBlockers = useTranslations("jobs.readinessBlockers")
  const translateBlocker = (b: string) => (KNOWN_BLOCKERS.has(b) ? tBlockers(b) : b)
  const [detail, setDetail] = useState<ReadinessJobDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [pending, setPending] = useState(false)
  const [policy, setPolicy] = useState<AudiencePolicy>("imported_untriaged")
  const [reason, setReason] = useState("")

  useEffect(() => {
    if (!jobId) {
      setDetail(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setDetail(null)
    getReadinessJob(jobId)
      .then((d) => {
        if (!cancelled) setDetail(d)
      })
      .catch(() => {
        if (!cancelled) toast.error("Não foi possível abrir a vaga")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [jobId])

  const onApprove = useCallback(async () => {
    if (!detail) return
    setPending(true)
    try {
      const updated = await approveReadinessStage(detail.id)
      setDetail(updated)
      toast.success("Etapa aprovada")
      onChanged?.()
    } catch {
      toast.error("Falha ao aprovar")
    } finally {
      setPending(false)
    }
  }, [detail, onChanged])

  const onReject = useCallback(async () => {
    if (!detail) return
    setPending(true)
    try {
      const updated = await rejectReadinessStage(detail.id, reason)
      setDetail(updated)
      toast.success("Etapa rejeitada — pronta para nova geração")
      onChanged?.()
    } catch {
      toast.error("Falha ao rejeitar")
    } finally {
      setPending(false)
    }
  }, [detail, reason, onChanged])

  const onDispatch = useCallback(async () => {
    if (!detail) return
    setPending(true)
    try {
      const updated = await dispatchReadinessScreening(detail.id, policy)
      setDetail(updated)
      toast.success("Triagem disparada")
      onChanged?.()
    } catch {
      toast.error("Falha ao disparar triagem")
    } finally {
      setPending(false)
    }
  }, [detail, policy, onChanged])

  if (!jobId) return null

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true">
      <div className="flex-1 bg-black/30" onClick={onClose} />
      <aside className="w-[480px] max-w-full bg-lia-bg-primary border-l border-lia-border-default shadow-xl overflow-y-auto">
        <div className="p-4 border-b border-lia-border-default flex items-center justify-between">
          <h2 className="text-base font-semibold text-lia-text-primary truncate">
            {loading || !detail ? "Carregando…" : detail.title}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Fechar">
            <XCircle className="w-4 h-4" />
          </Button>
        </div>
        {loading || !detail ? (
          <div className="p-6 flex items-center gap-2 text-lia-text-secondary text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Carregando detalhes…
          </div>
        ) : (
          <div className="p-4 space-y-4 text-sm">
            <div>
              <StageBadge stage={detail.readiness_stage} />
              {detail.last_event_at && (
                <span className="ml-2 text-[11px] text-lia-text-secondary">
                  último evento {new Date(detail.last_event_at).toLocaleString("pt-BR")}
                </span>
              )}
            </div>

            {detail.readiness_blockers.length > 0 && (
              <div className="flex items-center gap-1 flex-wrap">
                {detail.readiness_blockers.map((b) => (
                  <span
                    key={b}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
                  >
                    {translateBlocker(b)}
                  </span>
                ))}
              </div>
            )}

            {detail.description && (
              <section>
                <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-1">JD original</h3>
                <p className="text-xs text-lia-text-primary whitespace-pre-wrap line-clamp-6">{detail.description}</p>
              </section>
            )}

            {detail.enriched_jd && (
              <section>
                <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-1">JD enriquecido pela LIA</h3>
                <pre className="text-[11px] bg-lia-bg-elevated p-2 rounded border border-lia-border-default overflow-x-auto max-h-40">
                  {JSON.stringify(detail.enriched_jd, null, 2)}
                </pre>
              </section>
            )}

            {detail.behavioral_competencies?.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-1">Competências comportamentais</h3>
                <div className="flex flex-wrap gap-1">
                  {detail.behavioral_competencies.map((c, i) => (
                    <span key={i} className="text-[11px] px-1.5 py-0.5 rounded bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300">
                      {typeof c === "string" ? c : (c as { competency?: string })?.competency ?? JSON.stringify(c)}
                    </span>
                  ))}
                </div>
              </section>
            )}

            {detail.screening_questions?.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-1">
                  Perguntas de triagem ({detail.screening_questions.length})
                </h3>
                <ul className="list-disc pl-4 space-y-1">
                  {detail.screening_questions.slice(0, 8).map((q, i) => (
                    <li key={i} className="text-xs text-lia-text-primary">
                      {(q as { question?: string })?.question ?? JSON.stringify(q)}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {detail.timeline?.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-1">
                  Linha do tempo ({detail.timeline.length})
                </h3>
                <ol className="space-y-1.5 border-l border-lia-border-default pl-3">
                  {detail.timeline.slice(0, 12).map((ev: ReadinessTimelineEvent) => (
                    <li key={ev.id} className="text-[11px]">
                      <div className="flex items-baseline gap-2">
                        <span className="text-lia-text-primary font-medium">{ev.summary}</span>
                        <span className="text-lia-text-tertiary">· {ev.actor}</span>
                      </div>
                      {ev.at && (
                        <div className="text-lia-text-tertiary">
                          {new Date(ev.at).toLocaleString("pt-BR")}
                        </div>
                      )}
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {detail.requires_human && detail.readiness_stage !== "pronta_disparo" && (
              <section className="border border-amber-200 dark:border-amber-800/40 rounded-lg p-3 bg-amber-50/40 dark:bg-amber-950/20 space-y-2">
                <p className="text-xs text-amber-800 dark:text-amber-300">
                  Esta etapa precisa da sua aprovação para a LIA seguir.
                </p>
                <textarea
                  className="w-full text-xs p-2 rounded border border-lia-border-default bg-lia-bg-primary"
                  rows={2}
                  placeholder="Motivo (opcional, usado se você rejeitar)…"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={onApprove} disabled={pending} className="gap-1 bg-emerald-600 hover:bg-emerald-700 text-white">
                    {pending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                    Aprovar
                  </Button>
                  <Button size="sm" variant="outline" onClick={onReject} disabled={pending} className="gap-1">
                    <XCircle className="w-3.5 h-3.5" /> Rejeitar
                  </Button>
                </div>
              </section>
            )}

            {detail.readiness_stage === "pronta_disparo" && (
              <section className="border border-emerald-200 dark:border-emerald-800/40 rounded-lg p-3 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-2">
                <h3 className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">Disparar triagem</h3>
                <label className="block text-xs text-lia-text-secondary">
                  Público alvo
                  <select
                    className="mt-1 w-full text-xs p-2 rounded border border-lia-border-default bg-lia-bg-primary"
                    value={policy}
                    onChange={(e) => setPolicy(e.target.value as AudiencePolicy)}
                  >
                    <option value="new_only">Apenas candidatos novos do ATS</option>
                    <option value="imported_untriaged">Importados ainda sem triagem</option>
                    <option value="manual_selection">Seleção manual (lote customizado)</option>
                  </select>
                </label>
                <Button size="sm" onClick={onDispatch} disabled={pending} className="gap-1 bg-wedo-cyan hover:bg-wedo-cyan/90 text-white">
                  {pending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Disparar agora
                </Button>
              </section>
            )}
          </div>
        )}
      </aside>
    </div>
  )
}

export default JobReadinessDrawer
