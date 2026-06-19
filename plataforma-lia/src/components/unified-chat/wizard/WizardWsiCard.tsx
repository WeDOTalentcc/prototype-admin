"use client"

import React, { useState } from "react"
import { ChevronDown, Brain, AlertCircle } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { useToolSurface } from "@/contexts/ToolSurfaceContext"

interface WsiQuestion {
  question: string
  block?: string
  wsi_block?: number
  difficulty?: string
  needs_manual_review?: boolean
}

interface WizardWsiCardProps {
  data: Record<string, unknown>
}

function QBadge({ block }: { block?: string }) {
  if (!block) return null
  const map: Record<string, { label: string; cls: string }> = {
    technical: { label: "Técnica", cls: "bg-wedo-cyan/10 text-wedo-cyan-text" },
    behavioral: { label: "Comportamental", cls: "bg-wedo-purple/10 text-wedo-purple-text" },
    cbi: { label: "CBI", cls: "bg-status-warning/10 text-status-warning" },
  }
  const b = map[block] ?? {
    label: block,
    cls: "bg-lia-bg-primary text-lia-text-secondary",
  }
  return (
    <span
      className={cn(
        "text-[10px] px-1.5 py-0.5 rounded-full font-medium flex-shrink-0",
        b.cls,
      )}
    >
      {b.label}
    </span>
  )
}

/**
 * WizardWsiCard — card inline no chat para stage .
 * Lista colapsável com badges por tipo de pergunta.
 * Tokens DS LIA v4.2.1.
 * F4: AnimatePresence nas perguntas extras (slice(3+)).
 * adaptive-surface: auto-expandido e sem botão "Ver todas" em surface=panel.
 */
// ─── TriagemConfigSection ─────────────────────────────────────────────────────
function TriagemConfigSection({ jobId }: { jobId?: string }) {
  const [open, setOpen] = React.useState(false)
  const [score, setScore] = React.useState<number>(76)
  const [timeout, setTimeout] = React.useState<number>(48)
  const [chatWeb, setChatWeb] = React.useState(true)
  const [whatsapp, setWhatsapp] = React.useState(true)
  const [saving, setSaving] = React.useState(false)
  const [loaded, setLoaded] = React.useState(false)

  React.useEffect(() => {
    if (!open || loaded) return
    fetch("/api/backend-proxy/company/screening-config-defaults")
      .then((r) => r.json())
      .then((d) => {
        const s = d?.screening_config_defaults?.settings ?? d?.settings ?? {}
        const ch = d?.screening_config_defaults?.channels ?? d?.channels ?? {}
        if (s.min_score != null) setScore(Number(s.min_score))
        if (s.response_timeout_hours != null) setTimeout(Number(s.response_timeout_hours))
        if (ch.chat_web?.enabled != null) setChatWeb(Boolean(ch.chat_web.enabled))
        if (ch.whatsapp?.enabled != null) setWhatsapp(Boolean(ch.whatsapp.enabled))
        setLoaded(true)
      })
      .catch(() => setLoaded(true))
  }, [open, loaded])

  const handleSave = async () => {
    if (!jobId) return
    setSaving(true)
    try {
      await fetch(`/api/backend-proxy/job-vacancies/${jobId}/screening-config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          settings: { min_score: score, response_timeout_hours: timeout },
          channels: { chat_web: { enabled: chatWeb }, whatsapp: { enabled: whatsapp } },
        }),
      })
    } catch {}
    setSaving(false)
  }

  return (
    <div className="border-b border-lia-border-subtle">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-lia-interactive-hover transition-colors"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="text-lia-text-secondary font-medium">Configurações de Triagem</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary text-lia-text-muted">
            Score: {score}/100 · {timeout}h
          </span>
        </div>
        <span className="text-lia-text-tertiary text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-4 pb-3 space-y-3 bg-lia-bg-secondary/30">
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-lia-text-secondary block">Score mínimo (/100)</label>
              <input
                type="number" min={0} max={100} value={score}
                onChange={(e) => setScore(Math.max(0, Math.min(100, Number(e.target.value))))}
                className="w-full h-7 px-2 text-sm rounded border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:border-wedo-cyan"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-lia-text-secondary block">Prazo de resposta (h)</label>
              <input
                type="number" min={1} max={168} value={timeout}
                onChange={(e) => setTimeout(Math.max(1, Math.min(168, Number(e.target.value))))}
                className="w-full h-7 px-2 text-sm rounded border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary focus:outline-none focus:border-wedo-cyan"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" checked={chatWeb} onChange={(e) => setChatWeb(e.target.checked)} className="accent-wedo-cyan" />
              <span className="text-xs text-lia-text-secondary">Chat Web</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" checked={whatsapp} onChange={(e) => setWhatsapp(e.target.checked)} className="accent-wedo-cyan" />
              <span className="text-xs text-lia-text-secondary">WhatsApp</span>
            </label>
          </div>
          {jobId && (
            <button
              onClick={handleSave} disabled={saving}
              className="text-[10px] px-2.5 py-1 rounded bg-wedo-cyan text-white hover:bg-wedo-cyan/90 transition-colors disabled:opacity-50"
            >
              {saving ? "Salvando..." : "Salvar para esta vaga"}
            </button>
          )}
        </div>
      )}
    </div>
  )
}


export function WizardWsiCard({ data }: WizardWsiCardProps) {
  const surface = useToolSurface()
  const [expanded, setExpanded] = useState(surface === "panel")
  const [expandedQ, setExpandedQ] = useState<number | null>(null)

  const questions = (data.questions as WsiQuestion[]) ?? []
  const distribution = data.distribution as
    | { technical?: number; behavioral?: number }
    | undefined
  const needsReview = questions.filter((q) => q.needs_manual_review).length
  const jobId = (data.job_id as string | undefined) ?? (data.job_vacancy_id as string | undefined)

  if (questions.length === 0) return null

  const firstThree = questions.slice(0, 3)
  const extraQuestions = questions.slice(3)

  return (
    <div
      role="region"
      aria-label="Perguntas de triagem WSI"
      className={cn("mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary", surface !== "panel" && "overflow-hidden")}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <Brain className="w-4 h-4 text-wedo-purple flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary">
            {questions.length} perguntas de triagem
          </p>
          {distribution && (
            <p className="text-xs text-lia-text-secondary">
              {distribution.technical ?? 0} técnicas ·{" "}
              {distribution.behavioral ?? 0} comportamentais
            </p>
          )}
        </div>
        {needsReview > 0 && (
          <span className="flex items-center gap-1 text-[10px] text-status-warning flex-shrink-0">
            <AlertCircle className="w-3 h-3" aria-hidden="true" />
            {needsReview} revisar
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-muted flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      <TriagemConfigSection jobId={jobId} />
      {/* Lista de perguntas */}
      <div className="border-t border-lia-border-subtle divide-y divide-lia-border-subtle">
        {/* Primeiras 3 sempre visíveis */}
        {firstThree.map((q, i) => (
          <div key={i}>
            <button
              type="button"
              onClick={() => setExpandedQ(expandedQ === i ? null : i)}
              className="w-full flex items-start gap-2 px-3 py-2 hover:bg-lia-interactive-hover transition-colors text-left"
            >
              <span className="text-[11px] text-lia-text-muted flex-shrink-0 mt-0.5 tabular-nums w-4">
                {i + 1}.
              </span>
              <p
                className={cn(
                  "text-xs text-lia-text-secondary flex-1 min-w-0",
                  expandedQ === i ? "" : "line-clamp-2",
                )}
              >
                {q.question}
              </p>
              <div className="flex items-center gap-1 flex-shrink-0">
                {q.needs_manual_review && (
                  <AlertCircle
                    className="w-3 h-3 text-status-warning"
                    aria-label="Requer revisão"
                  />
                )}
                <QBadge block={q.block} />
              </div>
            </button>
          </div>
        ))}

        {/* Perguntas extras — animadas com AnimatePresence */}
        <AnimatePresence initial={false}>
          {expanded && extraQuestions.map((q, idx) => {
            const i = idx + 3
            return (
              <motion.div
                key={"extra-" + i}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setExpandedQ(expandedQ === i ? null : i)}
                  className="w-full flex items-start gap-2 px-3 py-2 hover:bg-lia-interactive-hover transition-colors text-left border-t border-lia-border-subtle"
                >
                  <span className="text-[11px] text-lia-text-muted flex-shrink-0 mt-0.5 tabular-nums w-4">
                    {i + 1}.
                  </span>
                  <p
                    className={cn(
                      "text-xs text-lia-text-secondary flex-1 min-w-0",
                      expandedQ === i ? "" : "line-clamp-2",
                    )}
                  >
                    {q.question}
                  </p>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {q.needs_manual_review && (
                      <AlertCircle
                        className="w-3 h-3 text-status-warning"
                        aria-label="Requer revisão"
                      />
                    )}
                    <QBadge block={q.block} />
                  </div>
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {!expanded && questions.length > 3 && surface !== "panel" && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="w-full px-3 py-2 text-xs text-lia-text-muted hover:bg-lia-interactive-hover transition-colors text-left"
          >
            Ver todas as {questions.length} perguntas
          </button>
        )}

      </div>
    </div>
  )
}
