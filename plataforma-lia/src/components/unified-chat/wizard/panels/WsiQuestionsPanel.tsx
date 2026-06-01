"use client"

import React, { useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { Check, Edit2, GripVertical, RefreshCw, Trash2, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react"
import type { WsiQuestionsData, ScreeningQuestion } from "../wizard-types"
import { FallbackBanner } from "./FallbackBanner"
import { AiDegradedModeBanner } from "./AiDegradedModeBanner"

interface Props {
  data: Record<string, unknown>
  requiresApproval: boolean
  onApprove?: () => void
  onReject?: () => void
}

const FRAMEWORK_COLORS: Record<string, string> = {
  CBI: "bg-wedo-cyan/10 text-wedo-cyan",
  Bloom: "bg-wedo-purple/10 text-wedo-purple",
  Dreyfus: "bg-wedo-magenta/10 text-wedo-magenta",
  BigFive: "bg-wedo-green/10 text-wedo-green",
}

/**
 * WsiQuestionsPanel — F6 HITL approval panel.
 * Shows generated questions as cards. Recruiter can approve/edit/regenerate each.
 */
export function WsiQuestionsPanel({ data, requiresApproval, onApprove, onReject }: Props) {
  const d = data as unknown as WsiQuestionsData
  const questions = d.questions || []
  const mode = d.screening_mode
  const dist = d.distribution
  const [expandedId, setExpandedId] = useState<number | null>(null)
  // Onda 33: HTML5 native drag-to-reorder. Source index lives in a ref so the
  // drop handler can pair it with the target index without re-rendering.
  const dragSourceRef = useRef<number | null>(null)

  // B.4: Individual question actions
  const handleEditQuestion = (index: number, newText: string) => {
    // Dispatches event for chat to handle (sends edit to backend)
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { index, newText },
    }))
  }

  const handleRegenerateQuestion = (index: number) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-regenerate-question", {
      detail: { index },
    }))
  }

  const handleRemoveQuestion = (index: number) => {
    // Enforce minimum question count
    const minQuestions = mode === "compact" ? 7 : 12
    if (questions.length <= minQuestions) return
    window.dispatchEvent(new CustomEvent("lia:wizard-remove-question", {
      detail: { index },
    }))
  }

  // Onda 33: Drag-to-reorder handlers. Reorder is dispatched as an event;
  // the actual question array stays controlled by `data` prop (backend echoes
  // the new order on the next wizard_step_response). No local question state.
  const handleDragStart = (index: number) => {
    dragSourceRef.current = index
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (targetIndex: number) => {
    const sourceIndex = dragSourceRef.current
    dragSourceRef.current = null
    if (sourceIndex === null || sourceIndex === targetIndex) return
    window.dispatchEvent(new CustomEvent("lia:wizard-reorder-questions", {
      detail: { fromIndex: sourceIndex, toIndex: targetIndex },
    }))
  }

  const techCount = questions.filter((q) => q.block === "technical").length
  const behavCount = questions.filter((q) => q.block === "behavioral").length
  const minQuestions = mode === "compact" ? 7 : 12
  const isAtMinimum = questions.length <= minQuestions

  return (
    <div className="flex flex-col">
      {/* Task #1070 — banner de modo degradado agregado (sessao/tenant). */}
      <AiDegradedModeBanner state={d.ai_degraded_mode ?? null} />
      {/* Task #1065 — banner de fallback determinístico (timeout do LLM
          → CBI mínimo). HITL #2 ainda obrigatório, banner só dá contexto. */}
      {d.wsi_questions_used_fallback && (
        <FallbackBanner
          reason={d.wsi_questions_fallback_reason ?? "timeout"}
          onRetry={() =>
            window.dispatchEvent(
              new CustomEvent("lia:wizard-retry-stage", {
                detail: { stage: "wsi_questions" },
              }),
            )
          }
        />
      )}
      {/* Summary header */}
      <div className="px-4 py-3">
        <div className="flex items-center gap-3 text-xs">
          <span className="text-lia-text-secondary">
            {questions.length} perguntas {isAtMinimum && `(mín: ${minQuestions})`}
          </span>
          <span className="w-px h-3 bg-lia-border-subtle" />
          <span className="text-lia-text-secondary">{techCount} técnicas</span>
          <span className="w-px h-3 bg-lia-border-subtle" />
          <span className="text-lia-text-secondary">{behavCount} comportamentais</span>
        </div>
        {mode && (
          <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded bg-wedo-cyan/10 text-wedo-cyan text-[10px] font-medium">
            Modo {mode === "compact" ? "Compacto" : "Completo"}
          </span>
        )}
      </div>

      {/* Question cards */}
      <div className="px-4 py-3 space-y-2" role="list">
        {questions.map((q, idx) => (
          <QuestionCard
            key={idx}
            index={idx}
            question={q}
            isExpanded={expandedId === idx}
            onToggle={() => setExpandedId(expandedId === idx ? null : idx)}
            onEdit={handleEditQuestion}
            onRegenerate={handleRegenerateQuestion}
            onRemove={isAtMinimum ? undefined : handleRemoveQuestion}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          />
        ))}
      </div>

      {/* HITL Approval footer */}
      {requiresApproval && questions.length > 0 && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-primary flex items-center gap-2">
          <button
            onClick={onReject}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md border border-lia-border-subtle text-sm font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Regenerar
          </button>
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none"
          >
            <Check className="w-3.5 h-3.5" />
            Aprovar todas
          </button>
        </div>
      )}
    </div>
  )
}

function QuestionCard({
  index,
  question,
  isExpanded,
  onToggle,
  onEdit,
  onRegenerate,
  onRemove,
  onDragStart,
  onDragOver,
  onDrop,
}: {
  index: number
  question: ScreeningQuestion
  isExpanded: boolean
  onToggle: () => void
  onEdit?: (index: number, newText: string) => void
  onRegenerate?: (index: number) => void
  onRemove?: (index: number) => void
  onDragStart?: (index: number) => void
  onDragOver?: (e: React.DragEvent) => void
  onDrop?: (index: number) => void
}) {
  const frameworkColor = FRAMEWORK_COLORS[question.framework] || FRAMEWORK_COLORS.CBI

  return (
    <div
      role="listitem"
      draggable={!!onDragStart}
      onDragStart={() => onDragStart?.(index)}
      onDragOver={onDragOver}
      onDrop={() => onDrop?.(index)}
      data-testid={`wsi-question-row-${index}`}
      className="group rounded-md border border-lia-border-subtle overflow-hidden"
    >
      {/* Card header */}
      <button
        onClick={onToggle}
        className="w-full flex items-start gap-2 px-3 py-2 text-left hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
      >
        {/* Onda 33: drag handle visible only on hover; pointer-events-none so it
            doesn't swallow the toggle click — drag is on the wrapper div. */}
        <GripVertical
          className="w-3.5 h-3.5 text-lia-text-disabled opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-1 pointer-events-none"
          aria-hidden="true"
        />
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-lia-bg-secondary flex items-center justify-center text-[10px] font-medium text-lia-text-secondary mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-lia-text-primary leading-snug">
            {question.question}
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", frameworkColor)}>
              {question.framework}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-lia-bg-secondary text-[10px] text-lia-text-secondary">
              {question.block === "technical" ? "Técnica" : "Comportamental"}
            </span>
            {question.needs_manual_review && (
              <span
                className="px-1.5 py-0.5 rounded bg-status-warning/10 text-[10px] text-status-warning font-medium inline-flex items-center gap-0.5"
                title="Pergunta pouco ancorada no JD — revise antes de aprovar"
              >
                <AlertTriangle className="w-2.5 h-2.5" aria-hidden="true" />
                Revisar
              </span>
            )}
            {question.trait_ocean && (
              <span className="px-1.5 py-0.5 rounded bg-wedo-cyan/10 text-[10px] text-wedo-cyan font-medium">
                {question.trait_ocean}
              </span>
            )}
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-lia-text-disabled flex-shrink-0 mt-1" />
        ) : (
          <ChevronDown className="w-4 h-4 text-lia-text-disabled flex-shrink-0 mt-1" />
        )}
      </button>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-3 pb-3 pt-1 border-t border-lia-border-subtle bg-lia-bg-secondary/50 space-y-2">
          <div>
            <p className="text-[10px] font-medium text-lia-text-tertiary mb-0.5">
              Resposta ideal
            </p>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {question.ideal_answer}
            </p>
          </div>

          {question.skill && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-lia-text-tertiary">Skill:</span>
              <span className="text-lia-text-primary">{question.skill}</span>
            </div>
          )}

          <div className="flex items-center gap-3 text-[10px] text-lia-text-tertiary">
            {question.bloom_level && <span>Bloom: {question.bloom_level}/6</span>}
            {question.dreyfus_level && <span>Dreyfus: {question.dreyfus_level}/5</span>}
            <span>Peso: {(question.weight * 100).toFixed(0)}%</span>
          </div>

          {/* Individual question actions */}
          <div className="flex items-center gap-1.5 pt-1.5 border-t border-lia-border-subtle mt-1.5">
            <button
              onClick={() => onEdit?.(index, question.question)}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3 h-3" />
              Editar
            </button>
            <button
              onClick={() => onRegenerate?.(index)}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium text-wedo-cyan hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none"
            >
              <RefreshCw className="w-3 h-3" />
              Regenerar
            </button>
            <button
              onClick={() => onRemove?.(index)}
              disabled={!onRemove}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium transition-colors motion-reduce:transition-none disabled:opacity-30 disabled:cursor-not-allowed text-status-error hover:bg-status-error/10 disabled:hover:bg-transparent"
              aria-label={`Remover pergunta ${index + 1}`}
            >
              <Trash2 className="w-3 h-3" />
              Remover
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
