"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { Check, Edit2, RefreshCw, Trash2, ChevronDown, ChevronUp } from "lucide-react"
import type { WsiQuestionsData, ScreeningQuestion } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  requiresApproval: boolean
  onApprove?: () => void
  onReject?: () => void
}

const FRAMEWORK_COLORS: Record<string, string> = {
  CBI: "bg-wedo-cyan/10 text-wedo-cyan",
  Bloom: "bg-purple-100 text-purple-700",
  Dreyfus: "bg-amber-100 text-amber-700",
  BigFive: "bg-blue-100 text-blue-700",
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

  const techCount = questions.filter((q) => q.block === "technical").length
  const behavCount = questions.filter((q) => q.block === "behavioral").length
  const minQuestions = mode === "compact" ? 7 : 12
  const isAtMinimum = questions.length <= minQuestions

  return (
    <div className="flex flex-col">
      {/* Summary header */}
      <div className="px-4 py-3 border-b border-lia-border-subtle">
        <div className="flex items-center gap-3 text-xs font-['Open_Sans',sans-serif]">
          <span className="text-lia-text-secondary">
            {questions.length} perguntas {isAtMinimum && `(min: ${minQuestions})`}
          </span>
          <span className="w-px h-3 bg-lia-border-subtle" />
          <span className="text-lia-text-secondary">{techCount} tecnicas</span>
          <span className="w-px h-3 bg-lia-border-subtle" />
          <span className="text-lia-text-secondary">{behavCount} comportamentais</span>
        </div>
        {mode && (
          <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded bg-wedo-cyan/10 text-wedo-cyan text-[10px] font-medium font-['Open_Sans',sans-serif]">
            Modo {mode === "compact" ? "Compacto" : "Completo"}
          </span>
        )}
      </div>

      {/* Question cards */}
      <div className="px-4 py-3 space-y-2">
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
          />
        ))}
      </div>

      {/* HITL Approval footer */}
      {requiresApproval && questions.length > 0 && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-primary flex items-center gap-2">
          <button
            onClick={onReject}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md border border-lia-border-subtle text-sm font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Regenerar
          </button>
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
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
}: {
  index: number
  question: ScreeningQuestion
  isExpanded: boolean
  onToggle: () => void
  onEdit?: (index: number, newText: string) => void
  onRegenerate?: (index: number) => void
  onRemove?: (index: number) => void
}) {
  const frameworkColor = FRAMEWORK_COLORS[question.framework] || FRAMEWORK_COLORS.CBI

  return (
    <div className="rounded-md border border-lia-border-subtle overflow-hidden">
      {/* Card header */}
      <button
        onClick={onToggle}
        className="w-full flex items-start gap-2 px-3 py-2 text-left hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
      >
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-lia-bg-secondary flex items-center justify-center text-[10px] font-medium text-lia-text-secondary font-['Open_Sans',sans-serif] mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-lia-text-primary font-['Open_Sans',sans-serif] leading-snug">
            {question.question}
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-medium", frameworkColor)}>
              {question.framework}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-lia-bg-secondary text-[10px] text-lia-text-secondary font-['Open_Sans',sans-serif]">
              {question.block === "technical" ? "Tecnica" : "Comportamental"}
            </span>
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
            <p className="text-[10px] font-medium text-lia-text-tertiary font-['Open_Sans',sans-serif] mb-0.5">
              Resposta ideal
            </p>
            <p className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] leading-relaxed">
              {question.ideal_answer}
            </p>
          </div>

          {question.skill && (
            <div className="flex items-center gap-1.5 text-xs font-['Open_Sans',sans-serif]">
              <span className="text-lia-text-tertiary">Skill:</span>
              <span className="text-lia-text-primary">{question.skill}</span>
            </div>
          )}

          <div className="flex items-center gap-3 text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif]">
            {question.bloom_level && <span>Bloom: {question.bloom_level}/6</span>}
            {question.dreyfus_level && <span>Dreyfus: {question.dreyfus_level}/5</span>}
            <span>Peso: {(question.weight * 100).toFixed(0)}%</span>
          </div>

          {/* Individual question actions */}
          <div className="flex items-center gap-1.5 pt-1.5 border-t border-lia-border-subtle mt-1.5">
            <button
              onClick={() => onEdit?.(index, question.question)}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
            >
              <Edit2 className="w-3 h-3" />
              Editar
            </button>
            <button
              onClick={() => onRegenerate?.(index)}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium text-wedo-cyan hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]"
            >
              <RefreshCw className="w-3 h-3" />
              Regenerar
            </button>
            <button
              onClick={() => onRemove?.(index)}
              disabled={!onRemove}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif] disabled:opacity-30 disabled:cursor-not-allowed text-status-error hover:bg-status-error/10 disabled:hover:bg-transparent"
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
