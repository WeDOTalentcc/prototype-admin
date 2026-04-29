"use client"

import React, { useState } from "react"
import { ShieldCheck, Plus, Trash2, Edit2, Check, X } from "lucide-react"
import type { EligibilityData, EligibilityQuestion } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

export function EligibilityPanel({ data, onUpdate }: Props) {
  const d = data as unknown as EligibilityData
  const questions = d.questions || []
  const [newQuestion, setNewQuestion] = useState("")
  const [editingIdx, setEditingIdx] = useState<number | null>(null)
  const [editText, setEditText] = useState("")

  const handleAdd = () => {
    if (!newQuestion.trim()) return
    const updated = [
      ...questions,
      {
        id: `elig_${Date.now()}`,
        question: newQuestion.trim(),
        required_answer: "yes" as const,
        eliminatory: true,
      },
    ]
    onUpdate?.({ questions: updated })
    setNewQuestion("")
  }

  const handleRemove = (idx: number) => {
    const updated = questions.filter((_, i) => i !== idx)
    onUpdate?.({ questions: updated })
  }

  const handleEditStart = (idx: number) => {
    setEditingIdx(idx)
    setEditText(questions[idx].question)
  }

  const handleEditSave = () => {
    if (editingIdx === null || !editText.trim()) return
    const updated = questions.map((q, i) =>
      i === editingIdx ? { ...q, question: editText.trim() } : q
    )
    onUpdate?.({ questions: updated })
    setEditingIdx(null)
    setEditText("")
  }

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-1.5">
        <ShieldCheck className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-medium text-lia-text-secondary">
          Perguntas eliminatorias ({questions.length})
        </span>
      </div>

      {/* Question list */}
      {questions.length > 0 && (
        <div className="space-y-2">
          {questions.map((q, i) => (
            <div key={q.id || i} className="flex items-start gap-2 p-2.5 rounded-md border border-lia-border-subtle">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-status-error/10 text-status-error flex items-center justify-center text-[10px] font-medium mt-0.5">!</span>
              <div className="flex-1 min-w-0">
                {editingIdx === i ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="flex-1 text-sm bg-lia-bg-secondary rounded px-2 py-1 text-lia-text-primary border border-lia-border-subtle focus:border-wedo-cyan outline-none"
                      autoFocus
                      onKeyDown={(e) => e.key === "Enter" && handleEditSave()}
                    />
                    <button onClick={handleEditSave} className="p-1 text-status-success hover:bg-status-success/10 rounded">
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => setEditingIdx(null)} className="p-1 text-lia-text-disabled hover:bg-lia-interactive-hover rounded">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <>
                    <p className="text-sm text-lia-text-primary">{q.question}</p>
                    <p className="text-[10px] text-lia-text-tertiary mt-0.5">
                      Resposta obrigatoria: {q.required_answer === "yes" ? "Sim" : "Nao"}
                    </p>
                  </>
                )}
              </div>
              {editingIdx !== i && (
                <div className="flex items-center gap-0.5 flex-shrink-0">
                  <button
                    onClick={() => handleEditStart(i)}
                    className="p-1 text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover rounded transition-colors"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleRemove(i)}
                    className="p-1 text-lia-text-disabled hover:text-status-error hover:bg-status-error/10 rounded transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {questions.length === 0 && (
        <p className="text-xs text-lia-text-tertiary">
          Nenhuma pergunta eliminatoria configurada.
        </p>
      )}

      {/* Add new question */}
      <div className="flex items-center gap-1.5">
        <input
          type="text"
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          placeholder="Nova pergunta eliminatoria..."
          className="flex-1 text-xs bg-lia-bg-secondary rounded-md px-3 py-2 text-lia-text-primary border border-lia-border-subtle focus:border-wedo-cyan outline-none placeholder:text-lia-text-disabled"
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        />
        <button
          onClick={handleAdd}
          disabled={!newQuestion.trim()}
          className="flex items-center gap-1 px-2.5 py-2 rounded-md bg-wedo-cyan text-white text-xs font-medium hover:bg-wedo-cyan/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
