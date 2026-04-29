"use client"

import React, { useState, useRef } from "react"
import { cn } from "@/lib/utils"
import { RefreshCw, Check } from "lucide-react"
import type { ScreeningMode } from "../wizard-types"

// --- Types ---

export interface WsiQuestion {
  id: string
  text: string
  competency: string
  type: "technical" | "behavioral"
  selected: boolean
}

export interface WizardWSIListPanelProps {
  questions: WsiQuestion[]
  screeningMode: ScreeningMode
  onAccept: (selectedQuestions: WsiQuestion[]) => void
  onGenerateMore: () => void
}

// --- Drag context ---

const TYPE_LABEL: Record<WsiQuestion["type"], string> = {
  technical: "Técnica",
  behavioral: "Comportamental",
}

const TYPE_COLOR: Record<WsiQuestion["type"], string> = {
  technical: "bg-blue-100 text-blue-700",
  behavioral: "bg-purple-100 text-purple-700",
}

// --- Question row ---

function QuestionRow({
  question,
  index,
  onToggle,
  onEdit,
  onDragStart,
  onDragOver,
  onDrop,
}: {
  question: WsiQuestion
  index: number
  onToggle: (id: string) => void
  onEdit: (id: string, newText: string) => void
  onDragStart: (index: number) => void
  onDragOver: (e: React.DragEvent) => void
  onDrop: (targetIndex: number) => void
}) {
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(question.text)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleEditCommit = () => {
    const trimmed = editValue.trim()
    if (trimmed && trimmed !== question.text) {
      onEdit(question.id, trimmed)
    }
    setEditing(false)
  }

  const handleEditKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") { e.preventDefault(); handleEditCommit() }
    if (e.key === "Escape") { setEditValue(question.text); setEditing(false) }
  }

  return (
    <div
      draggable
      onDragStart={() => onDragStart(index)}
      onDragOver={onDragOver}
      onDrop={() => onDrop(index)}
      className={cn(
        "flex items-start gap-3 px-3 py-2.5 rounded-lg border transition-colors",
        question.selected
          ? "border-primary/40 bg-primary/5"
          : "border-border bg-card hover:bg-muted/30"
      )}
    >
      {/* Drag handle */}
      <span
        className="text-muted-foreground/50 cursor-grab active:cursor-grabbing text-base leading-none mt-0.5 flex-shrink-0 select-none"
        aria-hidden="true"
      >
        ⠿
      </span>

      {/* Checkbox */}
      <button
        role="checkbox"
        aria-checked={question.selected}
        onClick={() => onToggle(question.id)}
        className={cn(
          "w-4 h-4 flex-shrink-0 mt-0.5 rounded border transition-colors",
          question.selected
            ? "bg-primary border-primary"
            : "border-border bg-background"
        )}
      >
        {question.selected && (
          <Check className="w-3 h-3 text-primary-foreground mx-auto" />
        )}
      </button>

      {/* Text (inline editable) */}
      <div className="flex-1 min-w-0">
        {editing ? (
          <input
            ref={inputRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleEditCommit}
            onKeyDown={handleEditKeyDown}
            autoFocus
            className="w-full text-sm bg-background border border-ring rounded px-2 py-0.5 focus:outline-none focus:ring-2 focus:ring-ring"
          />
        ) : (
          <button
            onClick={() => { setEditing(true); setEditValue(question.text) }}
            className="text-sm text-left text-foreground hover:text-primary transition-colors w-full"
            title="Clique para editar"
          >
            {question.text}
          </button>
        )}

        <div className="flex items-center gap-1.5 mt-1">
          <span
            className={cn(
              "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium",
              TYPE_COLOR[question.type]
            )}
          >
            {TYPE_LABEL[question.type]}
          </span>
          {question.competency && (
            <span className="text-[10px] text-muted-foreground">
              {question.competency}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

// --- Main Component ---

/**
 * WizardWSIListPanel (HITL gate 2) — Onda 26-27 E.4
 *
 * Displays WSI questions as a reorderable, selectable list.
 * Recruiter can toggle selection, edit inline, drag to reorder,
 * generate more questions, or accept the current selection.
 */
export function WizardWSIListPanel({
  questions: initialQuestions,
  screeningMode,
  onAccept,
  onGenerateMore,
}: WizardWSIListPanelProps) {
  const [questions, setQuestions] = useState<WsiQuestion[]>(initialQuestions)
  const dragIndexRef = useRef<number | null>(null)

  const selectedQuestions = questions.filter((q) => q.selected)
  const modeLabel = screeningMode === "compact"
    ? `compacto (${questions.length})`
    : `completo (${questions.length})`

  const handleToggle = (id: string) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, selected: !q.selected } : q))
    )
  }

  const handleEdit = (id: string, newText: string) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, text: newText } : q))
    )
  }

  const handleDragStart = (index: number) => {
    dragIndexRef.current = index
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (targetIndex: number) => {
    const sourceIndex = dragIndexRef.current
    if (sourceIndex === null || sourceIndex === targetIndex) return
    setQuestions((prev) => {
      const next = [...prev]
      const [moved] = next.splice(sourceIndex, 1)
      next.splice(targetIndex, 0, moved)
      return next
    })
    dragIndexRef.current = null
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border space-y-1">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-foreground">
            Perguntas de Triagem WSI
          </h2>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-muted text-xs font-medium text-muted-foreground">
            {modeLabel}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {selectedQuestions.length} de {questions.length} selecionadas
        </p>
      </div>

      {/* Question list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {questions.length > 0 ? (
          questions.map((q, idx) => (
            <QuestionRow
              key={q.id}
              question={q}
              index={idx}
              onToggle={handleToggle}
              onEdit={handleEdit}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            />
          ))
        ) : (
          <div className="text-center py-8 space-y-2">
            <div className="w-5 h-5 mx-auto border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-muted-foreground">Gerando perguntas...</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 flex items-center gap-2 px-4 py-3 border-t border-border bg-background">
        <button
          onClick={onGenerateMore}
          className="flex items-center gap-2 px-3 py-2 rounded border border-border text-sm font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Gerar mais
        </button>
        <button
          onClick={() => onAccept(selectedQuestions)}
          disabled={selectedQuestions.length === 0}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Check className="w-4 h-4" />
          Aceitar selecionadas ({selectedQuestions.length})
        </button>
      </div>
    </div>
  )
}
