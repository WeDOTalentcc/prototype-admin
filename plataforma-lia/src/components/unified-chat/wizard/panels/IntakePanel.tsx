"use client"

import React, { useEffect, useState } from "react"
import { FileText, Tag, Edit2, Check } from "lucide-react"
import { useAuthStore } from "@/stores/auth-store"
import { useJdSimilar } from "@/hooks/jobs/use-jd-similar"
import { JdSimilarCard } from "./JdSimilarCard"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

/**
 * IntakePanel — displays the raw job description input during intake stage.
 * Shows extracted keywords as chip tags when available.
 */
export function IntakePanel({ data, onUpdate }: Props) {
  const rawInput = (data.raw_input as string) || ""
  const extractedKeywords = (data.extracted_keywords as string[]) || []
  const source = (data.source as string) || "chat"
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(rawInput)

  // ── Sprint B Phase 1 ─ Sugestao de JDs similares no historico ──────────
  const companyId = useAuthStore((s) => (s.user as { company_id?: string } | null)?.company_id || "")
  const parsedTitle = (data.parsed_title as string) || ""
  const parsedDepartment = (data.parsed_department as string) || ""
  const { items: similarJds, loading: jdSimilarLoading, lookup: lookupSimilarJds } = useJdSimilar({ companyId })

  useEffect(() => {
    if (!companyId) return
    const titleHint = parsedTitle || rawInput.split(/[\n.]/)[0]?.trim().slice(0, 80) || ""
    if (!titleHint) return
    const timer = setTimeout(() => { void lookupSimilarJds(titleHint, parsedDepartment || undefined) }, 600)
    return () => clearTimeout(timer)
  }, [companyId, parsedTitle, parsedDepartment, rawInput, lookupSimilarJds])

  const handleReuseJd = (id: string) => {
    onUpdate?.({ jd_similar_reuse_id: id, jd_similar_reuse_started_at: new Date().toISOString() })
  }
  const handleCreateFresh = () => {
    onUpdate?.({ jd_similar_dismissed: true })
  }


  const handleSaveEdit = () => {
    if (editText.trim() && editText !== rawInput) {
      onUpdate?.({ raw_input: editText.trim() })
    }
    setIsEditing(false)
  }

  return (
    <div className="p-4 space-y-4">
      {/* Source indicator */}
      <div className="flex items-center justify-between text-xs text-lia-text-disabled">
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5" />
          <span>
            {source === "file" ? "Enviado via arquivo" : "Descrito no chat"}
          </span>
        </div>
        {rawInput && !isEditing && (
          <button
            onClick={() => { setEditText(rawInput); setIsEditing(true) }}
            className="flex items-center gap-1 text-lia-text-secondary hover:text-wedo-cyan transition-colors"
            aria-label="Editar descricao"
          >
            <Edit2 className="w-3 h-3" />
            <span>Editar</span>
          </button>
        )}
      </div>

      {/* Raw input display / edit */}
      <div className="rounded-md bg-lia-bg-secondary p-3">
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full text-sm text-lia-text-primary bg-transparent resize-none leading-relaxed focus:outline-none min-h-[80px]"
              autoFocus
              aria-label="Editar descricao da vaga"
            />
            <div className="flex justify-end gap-1.5">
              <button
                onClick={() => setIsEditing(false)}
                className="px-2 py-1 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover rounded"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveEdit}
                className="flex items-center gap-1 px-2 py-1 text-xs text-white bg-wedo-cyan rounded hover:bg-wedo-cyan/90"
              >
                <Check className="w-3 h-3" />
                Salvar
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-lia-text-primary whitespace-pre-wrap leading-relaxed">
            {rawInput || "Aguardando descricao da vaga..."}
          </p>
        )}
      </div>

      {/* Extracted keywords */}
      {extractedKeywords.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
            <Tag className="w-3 h-3" />
            <span>Palavras-chave detectadas</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {extractedKeywords.map((kw, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-micro rounded-full bg-wedo-cyan/10 text-wedo-cyan border border-wedo-cyan/20"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* JD similar history suggestions (Sprint B Phase 1) */}
      {!data.jd_similar_dismissed && (similarJds.length > 0 || jdSimilarLoading) && (
        <JdSimilarCard
          items={similarJds}
          loading={jdSimilarLoading}
          onReuse={handleReuseJd}
          onCreateFresh={handleCreateFresh}
        />
      )}

      {/* Processing indicator */}
      {rawInput && (
        <div className="flex items-center gap-2 text-xs text-lia-text-disabled">
          <div className="w-3 h-3 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
          <span>Analisando e enriquecendo JD...</span>
        </div>
      )}
    </div>
  )
}
