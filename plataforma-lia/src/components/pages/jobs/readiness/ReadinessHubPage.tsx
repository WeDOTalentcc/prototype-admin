"use client"

import React, { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  Play,
  RefreshCcw,
  Brain,
  XCircle,
} from "lucide-react"
import { toast } from "sonner"
import {
  approveReadinessStage,
  dispatchReadinessScreening,
  getReadinessBoard,
  getReadinessJob,
  getReadinessOverview,
  rejectReadinessStage,
  runReadinessAll,
  runReadinessBatch,
  type AudiencePolicy,
  type ReadinessBoard,
  type ReadinessJobCard,
  type ReadinessJobDetail,
  type ReadinessOverview,
  type ReadinessStage,
  type ReadinessTimelineEvent,
  READINESS_STAGES_ORDER,
} from "@/services/lia-api/readiness-api"

const STAGE_COLOR: Record<ReadinessStage, string> = {
  importada: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  sem_jd: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  jd_rascunho: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
  jd_enriquecido: "bg-violet-50 text-violet-700 dark:bg-violet-950/40 dark:text-violet-300",
  perguntas_triagem: "bg-fuchsia-50 text-fuchsia-700 dark:bg-fuchsia-950/40 dark:text-fuchsia-300",
  pronta_disparo: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  em_triagem: "bg-cyan-50 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300",
}

const KNOWN_BLOCKERS = new Set([
  "missing_jd",
  "missing_enrichment",
  "missing_competencies",
  "missing_questions",
])

function StageBadge({ stage, label }: { stage: ReadinessStage; label: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${STAGE_COLOR[stage] || ""}`}>
      {label}
    </span>
  )
}

function OverviewHeader({
  overview,
  loading,
  onRunAll,
  runAllPending,
}: {
  overview: ReadinessOverview | null
  loading: boolean
  onRunAll: () => void
  runAllPending: boolean
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-3">
      <div>
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-wedo-cyan" />
          <h1 className="text-lg font-semibold text-lia-text-primary">Hub de Prontidão</h1>
        </div>
        <p className="text-xs text-lia-text-secondary mt-1 max-w-2xl">
          Prepare suas vagas importadas do ATS para começar a triar candidatos com a LIA.
          Cada vaga passa pelos estágios abaixo até estar pronta para o disparo.
        </p>
        {overview && !loading && (
          <div className="flex items-center gap-4 mt-3 text-xs">
            <span className="text-lia-text-secondary">
              <strong className="text-lia-text-primary">{overview.total}</strong> vagas
            </span>
            <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-3.5 h-3.5" />
              <strong>{overview.action_required}</strong> aguardando você
            </span>
            <span className="flex items-center gap-1 text-lia-text-secondary">
              <Clock className="w-3.5 h-3.5" />
              <strong className="text-lia-text-primary">{overview.queued_actions}</strong> ações automáticas pendentes
            </span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button
          onClick={onRunAll}
          disabled={runAllPending || loading}
          className="gap-2 h-8 px-3 bg-lia-btn-primary-hover"
        >
          {runAllPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          Rodar tudo
        </Button>
      </div>
    </div>
  )
}

function JobCardCell({
  card,
  selected,
  onToggle,
  onOpen,
}: {
  card: ReadinessJobCard
  selected: boolean
  onToggle: () => void
  onOpen: () => void
}) {
  const tBlockers = useTranslations("jobs.readinessBlockers")
  const translateBlocker = (b: string) => (KNOWN_BLOCKERS.has(b) ? tBlockers(b) : b)
  return (
    <div
      className={`group p-2.5 rounded-lg border bg-lia-bg-elevated hover:border-lia-border-medium transition cursor-pointer ${
        selected ? "border-wedo-cyan ring-1 ring-wedo-cyan" : "border-lia-border-default"
      }`}
      onClick={onOpen}
    >
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          className="mt-1 accent-wedo-cyan"
          checked={selected}
          onClick={(e) => e.stopPropagation()}
          onChange={onToggle}
          aria-label={`Selecionar ${card.title}`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-medium text-lia-text-primary truncate">{card.title}</h3>
            {card.requires_human && (
              <Chip variant="neutral" className="text-[10px] border-amber-300 text-amber-600 dark:text-amber-400">
                ação requerida
              </Chip>
            )}
          </div>
          <div className="mt-1 flex items-center gap-2 flex-wrap text-[11px] text-lia-text-secondary">
            {card.source_system && <span>ATS: {card.source_system}</span>}
            {card.department && <span>· {card.department}</span>}
            {card.status && <span>· {card.status}</span>}
          </div>
          {card.readiness_blockers.length > 0 && (
            <div className="mt-1 flex items-center gap-1 flex-wrap">
              {card.readiness_blockers.slice(0, 3).map((b) => (
                <span
                  key={b}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
                >
                  {translateBlocker(b)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function JobDetailDrawer({
  detail,
  loading,
  onClose,
  onApprove,
  onReject,
  onDispatch,
  pending,
}: {
  detail: ReadinessJobDetail | null
  loading: boolean
  onClose: () => void
  onApprove: () => void
  onReject: (reason: string) => void
  onDispatch: (policy: AudiencePolicy) => void
  pending: boolean
}) {
  const [policy, setPolicy] = useState<AudiencePolicy>("imported_untriaged")
  const [reason, setReason] = useState("")
  if (!detail && !loading) return null
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
              <StageBadge stage={detail.readiness_stage} label={detail.readiness_label} />
              {detail.last_event_at && (
                <span className="ml-2 text-[11px] text-lia-text-secondary">
                  último evento {new Date(detail.last_event_at).toLocaleString("pt-BR")}
                </span>
              )}
            </div>

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
                  <Button size="sm" variant="outline" onClick={() => onReject(reason)} disabled={pending} className="gap-1">
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
                <Button size="sm" onClick={() => onDispatch(policy)} disabled={pending} className="gap-1 bg-wedo-cyan hover:bg-wedo-cyan/90 text-white">
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

export function ReadinessHubPage() {
  const [overview, setOverview] = useState<ReadinessOverview | null>(null)
  const [board, setBoard] = useState<ReadinessBoard | null>(null)
  const [loading, setLoading] = useState(true)
  const [runAllPending, setRunAllPending] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [openId, setOpenId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ReadinessJobDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [drawerPending, setDrawerPending] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [o, b] = await Promise.all([getReadinessOverview(), getReadinessBoard({ limit: 200 })])
      setOverview(o)
      setBoard(b)
    } catch (err) {
      console.error("readiness refresh failed", err)
      toast.error("Não foi possível carregar o Hub de Prontidão")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const grouped = useMemo(() => {
    const out: Record<ReadinessStage, ReadinessJobCard[]> = {
      importada: [], sem_jd: [], jd_rascunho: [], jd_enriquecido: [],
      perguntas_triagem: [], pronta_disparo: [], em_triagem: [],
    }
    for (const c of board?.items || []) out[c.readiness_stage]?.push(c)
    return out
  }, [board])

  const onRunAll = useCallback(async () => {
    setRunAllPending(true)
    try {
      const r = await runReadinessAll()
      toast.success(`${r.enqueued.length} ações enfileiradas`)
      await refresh()
    } catch (err) {
      console.error(err)
      toast.error("Falha ao enfileirar ações")
    } finally {
      setRunAllPending(false)
    }
  }, [refresh])

  const onRunBatch = useCallback(async () => {
    if (selected.size === 0) return
    try {
      const r = await runReadinessBatch(Array.from(selected))
      toast.success(`${r.enqueued.length} de ${r.total} vagas enfileiradas`)
      setSelected(new Set())
      await refresh()
    } catch (err) {
      console.error(err)
      toast.error("Falha ao enfileirar lote")
    }
  }, [selected, refresh])

  const openJob = useCallback(async (id: string) => {
    setOpenId(id); setDetailLoading(true); setDetail(null)
    try { setDetail(await getReadinessJob(id)) }
    catch { toast.error("Não foi possível abrir a vaga") }
    finally { setDetailLoading(false) }
  }, [])

  const closeDrawer = useCallback(() => { setOpenId(null); setDetail(null) }, [])

  const onApprove = useCallback(async () => {
    if (!detail) return
    setDrawerPending(true)
    try {
      const updated = await approveReadinessStage(detail.id)
      setDetail(updated)
      toast.success("Etapa aprovada")
      await refresh()
    } catch (err) {
      console.error(err)
      toast.error("Falha ao aprovar")
    } finally { setDrawerPending(false) }
  }, [detail, refresh])

  const onReject = useCallback(async (reason: string) => {
    if (!detail) return
    setDrawerPending(true)
    try {
      const updated = await rejectReadinessStage(detail.id, reason)
      setDetail(updated)
      toast.success("Etapa rejeitada — pronta para nova geração")
      await refresh()
    } catch (err) {
      console.error(err)
      toast.error("Falha ao rejeitar")
    } finally { setDrawerPending(false) }
  }, [detail, refresh])

  const onDispatch = useCallback(async (policy: AudiencePolicy) => {
    if (!detail) return
    setDrawerPending(true)
    try {
      const updated = await dispatchReadinessScreening(detail.id, policy)
      setDetail(updated)
      toast.success("Triagem disparada")
      await refresh()
    } catch (err) {
      console.error(err)
      toast.error("Falha ao disparar triagem")
    } finally { setDrawerPending(false) }
  }, [detail, refresh])

  return (
    <div className="h-full flex flex-col bg-lia-bg-primary overflow-hidden">
      <div className="flex-shrink-0 px-4 pt-3 pb-2">
        <OverviewHeader
          overview={overview}
          loading={loading}
          onRunAll={onRunAll}
          runAllPending={runAllPending}
        />
        {selected.size > 0 && (
          <div className="flex items-center justify-between p-2 mb-2 rounded-md bg-wedo-cyan/10 border border-wedo-cyan/30">
            <span className="text-xs text-lia-text-primary">{selected.size} vaga(s) selecionada(s)</span>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}>Limpar</Button>
              <Button size="sm" onClick={onRunBatch} className="gap-1 bg-wedo-cyan hover:bg-wedo-cyan/90 text-white">
                <Play className="w-3.5 h-3.5" /> Rodar selecionadas
              </Button>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-x-auto px-4 pb-4">
        {loading && !board ? (
          <div className="flex items-center gap-2 text-sm text-lia-text-secondary py-6">
            <Loader2 className="w-4 h-4 animate-spin" /> Carregando vagas…
          </div>
        ) : (
          <div className="flex gap-3 min-w-max h-full">
            {READINESS_STAGES_ORDER.map((stage) => {
              const items = grouped[stage] || []
              const count = overview?.by_stage.find((s) => s.stage === stage)?.count ?? items.length
              const label = overview?.by_stage.find((s) => s.stage === stage)?.label ?? stage
              return (
                <div key={stage} className="w-72 flex-shrink-0 flex flex-col">
                  <div className="flex items-center justify-between mb-2 px-1">
                    <StageBadge stage={stage} label={label} />
                    <span className="text-xs text-lia-text-secondary">{count}</span>
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 p-1 rounded-lg bg-lia-bg-secondary/40 min-h-[200px]">
                    {items.length === 0 ? (
                      <p className="text-[11px] text-lia-text-tertiary p-2">— vazio —</p>
                    ) : (
                      items.map((card) => (
                        <JobCardCell
                          key={card.id}
                          card={card}
                          selected={selected.has(card.id)}
                          onToggle={() => {
                            setSelected((prev) => {
                              const next = new Set(prev)
                              if (next.has(card.id)) next.delete(card.id); else next.add(card.id)
                              return next
                            })
                          }}
                          onOpen={() => void openJob(card.id)}
                        />
                      ))
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {openId && (
        <JobDetailDrawer
          detail={detail}
          loading={detailLoading}
          onClose={closeDrawer}
          onApprove={onApprove}
          onReject={onReject}
          onDispatch={onDispatch}
          pending={drawerPending}
        />
      )}
    </div>
  )
}

export default ReadinessHubPage
