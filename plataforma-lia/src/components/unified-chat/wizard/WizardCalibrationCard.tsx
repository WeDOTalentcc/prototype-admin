"use client"

import React, { useState } from "react"
import { ChevronDown, Target, ThumbsUp, ThumbsDown, Users, CheckCircle, Minus, User } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import type { CalibrationData, CalibrationCandidate } from "./wizard-types"

/**
 * WizardCalibrationCard — card inline no chat para o stage de calibração.
 *
 * Renderiza no chat em qualquer modo (sidebar, floating, fullscreen).
 * Permite aprovar/rejeitar/pular candidatos diretamente no chat, como
 * fallback quando o usuário está em modo painel lateral ou declinizou a
 * transição para tela cheia. Em modo fullscreen o painel lateral
 * (CalibrationPanel) é o surface principal; este card serve como
 * checkpoint histórico visível no scroll do chat.
 *
 * Despacha os mesmos CustomEvents que CalibrationPanel para que o
 * orchestrator consuma o feedback de forma homogênea.
 */
export function WizardCalibrationCard({ data }: { data: Record<string, unknown> }) {
  const [expanded, setExpanded] = useState(true)
  const d = data as unknown as CalibrationData & { pool_count?: number }
  const candidates = d.candidates || []
  const threshold = d.threshold || 3
  const approvedCount = d.approved_count || 0
  const canAdvance = approvedCount >= threshold
  const poolCount = d.pool_count ?? null

  const handleApprove = (candidateId: string, comment?: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_approve", candidateId, reason: comment },
    }))
  }

  const handleReject = (candidateId: string, comment?: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_reject", candidateId, reason: comment },
    }))
  }

  const handleSkip = (candidateId: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_skip", candidateId },
    }))
  }

  const handleAdvance = () => {
    window.dispatchEvent(new CustomEvent("lia:wizard-advance", {
      detail: { stage: "calibration" },
    }))
  }

  return (
    <div
      role="region"
      aria-label="Calibração de candidatos"
      className="mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary overflow-hidden"
    >
      {/* Header — progress + toggle */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <Target className="w-4 h-4 text-wedo-cyan flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary">
            Calibração de candidatos
          </p>
          <p className="text-xs text-lia-text-secondary">
            {approvedCount}/{threshold} perfis avaliados
            {poolCount !== null && (
              <span className="ml-2 text-wedo-cyan">
                · {poolCount.toLocaleString("pt-BR")} no pool
              </span>
            )}
          </p>
        </div>
        {canAdvance && (
          <span className="px-2 py-0.5 rounded bg-status-success/10 text-status-success text-[10px] font-medium flex-shrink-0">
            Pronto
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-disabled flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      {/* Progress bar */}
      <div className="h-1 bg-lia-bg-tertiary">
        <div
          className={cn(
            "h-full transition-[width] duration-300",
            canAdvance ? "bg-status-success" : "bg-wedo-cyan"
          )}
          style={{ width:  }}
        />
      </div>

      {/* Expandable body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="calibration-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-3 py-2 space-y-2 border-t border-lia-border-subtle">
              {candidates.length === 0 ? (
                <div className="text-center py-3">
                  <div className="w-4 h-4 mx-auto mb-1.5 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
                  <p className="text-xs text-lia-text-tertiary">
                    Aguardando candidatos...
                  </p>
                </div>
              ) : (
                candidates.map((c) => (
                  <InlineCandidateCard
                    key={c.id}
                    candidate={c}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onSkip={handleSkip}
                  />
                ))
              )}
            </div>

            {candidates.length > 0 && (
              <div className="px-3 pb-3 border-t border-lia-border-subtle pt-2">
                <button
                  type="button"
                  onClick={handleAdvance}
                  disabled={!canAdvance}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-colors",
                    canAdvance
                      ? "bg-wedo-cyan text-white hover:bg-wedo-cyan/90"
                      : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
                  )}
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                  {canAdvance
                    ? "Calibração completa — Avançar"
                    : }
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function InlineCandidateCard({
  candidate,
  onApprove,
  onReject,
  onSkip,
}: {
  candidate: CalibrationCandidate
  onApprove: (id: string, comment?: string) => void
  onReject: (id: string, comment?: string) => void
  onSkip: (id: string) => void
}) {
  const decided = !!candidate.decision
  const [comment, setComment] = useState("")
  const [showComment, setShowComment] = useState(false)

  return (
    <div className={cn(
      "rounded-md border bg-lia-bg-primary overflow-hidden",
      decided ? "border-lia-border-subtle/50 opacity-60" : "border-lia-border-subtle",
    )}>
      <div className="flex items-start gap-2 px-2.5 py-2">
        {/* Avatar */}
        <div className="w-7 h-7 rounded-full bg-lia-bg-secondary flex items-center justify-center flex-shrink-0 overflow-hidden">
          {candidate.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={candidate.avatar_url} alt={candidate.name} className="w-full h-full object-cover" />
          ) : (
            <User className="w-3.5 h-3.5 text-lia-text-disabled" />
          )}
        </div>
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <p className="text-xs font-medium text-lia-text-primary truncate">{candidate.name}</p>
            <span className="text-[10px] text-wedo-cyan font-medium flex-shrink-0">
              {Math.round(candidate.match_score * 100)}%
            </span>
          </div>
          <p className="text-[11px] text-lia-text-secondary truncate">
            {candidate.current_title}
          </p>
          {candidate.auto_tags && candidate.auto_tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {candidate.auto_tags.slice(0, 3).map((tag, i) => (
                <span key={i} className="px-1 py-0 rounded bg-lia-bg-tertiary text-lia-text-secondary text-[9px]">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
        {/* Decision badge */}
        {decided && (
          <span className={cn(
            "text-[10px] font-medium px-1.5 py-0.5 rounded flex-shrink-0",
            candidate.decision === "approved" ? "bg-status-success/10 text-status-success" :
            candidate.decision === "skipped" ? "bg-lia-bg-tertiary text-lia-text-disabled" :
            "bg-status-error/10 text-status-error"
          )}>
            {candidate.decision === "approved" ? "Aprovado" :
             candidate.decision === "skipped" ? "Pulado" : "Rejeitado"}
          </span>
        )}
      </div>

      {/* Comment field — shown on demand */}
      {!decided && showComment && (
        <div className="px-2.5 pb-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Por que gostou ou não? (opcional)"
            rows={2}
            autoFocus
            className="w-full text-[11px] text-lia-text-primary placeholder:text-lia-text-disabled bg-lia-bg-secondary border border-lia-border-subtle rounded px-2 py-1 resize-none focus:outline-none focus:ring-1 focus:ring-wedo-cyan/40"
          />
        </div>
      )}

      {/* Actions */}
      {!decided && (
        <div className="flex border-t border-lia-border-subtle">
          <button
            type="button"
            onClick={() => onReject(candidate.id, comment || undefined)}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 text-[11px] text-status-error hover:bg-status-error/5 transition-colors"
          >
            <ThumbsDown className="w-3 h-3" />
            Rejeitar
          </button>
          <div className="w-px bg-lia-border-subtle" />
          <button
            type="button"
            onClick={() => onSkip(candidate.id)}
            className="px-2.5 py-1.5 text-[11px] text-lia-text-tertiary hover:bg-lia-interactive-hover transition-colors"
            title="Pular"
          >
            <Minus className="w-3 h-3" />
          </button>
          <div className="w-px bg-lia-border-subtle" />
          <button
            type="button"
            onClick={() => setShowComment((v) => !v)}
            className="px-2 py-1.5 text-[11px] text-lia-text-tertiary hover:bg-lia-interactive-hover transition-colors"
            title="Adicionar comentário"
          >
            ✎
          </button>
          <div className="w-px bg-lia-border-subtle" />
          <button
            type="button"
            onClick={() => onApprove(candidate.id, comment || undefined)}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 text-[11px] text-status-success hover:bg-status-success/5 transition-colors"
          >
            <ThumbsUp className="w-3 h-3" />
            Aprovar
          </button>
        </div>
      )}
    </div>
  )
}
