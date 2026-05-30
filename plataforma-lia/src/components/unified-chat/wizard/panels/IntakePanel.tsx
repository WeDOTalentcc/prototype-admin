"use client"

import React, { useEffect, useState } from "react"
import { FileText, Tag, Edit2, Check, X, Plus, CircleDashed } from "lucide-react"
import { cn } from "@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { useAuthStore } from "@/stores/auth-store"
import { useJdSimilar } from "@/hooks/jobs/use-jd-similar"
import { JdSimilarCard } from "./JdSimilarCard"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

type Competency = Record<string, unknown>

const MODE_LABEL: Record<string, string> = {
  compact: "Compacto (7 perguntas)",
  full: "Completo (12 perguntas)",
}

/** Resolve a faixa salarial para texto, defensivo a salary_range obj ou salary_min/max. */
function salaryText(data: Record<string, unknown>): string {
  const range = data.salary_range as { min?: number; max?: number } | undefined
  const min = range?.min ?? (data.salary_min as number | undefined)
  const max = range?.max ?? (data.salary_max as number | undefined)
  if (!min && !max) return ""
  const fmt = (v?: number) => (v ? `R$ ${v.toLocaleString("pt-BR")}` : "")
  return [fmt(min), fmt(max)].filter(Boolean).join(" – ")
}

/** Uma linha de campo da ficha: rótulo + valor (Chip success) ou estado pendente. */
function FichaField({ label, value }: { label: string; value: string }) {
  const filled = Boolean(value)
  return (
    <div className="flex items-center justify-between gap-3 py-1">
      <span className="text-xs text-lia-text-secondary">{label}</span>
      {filled ? (
        <Chip density="compact" variant="success" className="truncate max-w-[60%]">
          {value}
        </Chip>
      ) : (
        <span className="flex items-center gap-1 text-micro text-lia-text-disabled">
          <CircleDashed className="w-3 h-3" />
          pendente
        </span>
      )}
    </div>
  )
}

/**
 * Grupo de chips de competências editáveis (técnicas OU comportamentais).
 * Hooks no topo (Rules of Hooks). Edição local: add (input+Enter), remover (x),
 * editar (clique no chip → inline). Mudanças sobem via onChange.
 */
function CompetencyChipGroup({
  label,
  items,
  labelKey,
  testidPrefix,
  newItem,
  onChange,
}: {
  label: string
  items: Competency[]
  labelKey: "skill" | "competencia"
  testidPrefix: string
  newItem: (value: string) => Competency
  onChange: (next: Competency[]) => void
}) {
  const [draft, setDraft] = useState("")
  const [editingIdx, setEditingIdx] = useState<number | null>(null)
  const [editText, setEditText] = useState("")

  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i))
  const add = () => {
    const v = draft.trim()
    if (!v) return
    onChange([...items, newItem(v)])
    setDraft("")
  }
  const startEdit = (i: number) => {
    setEditingIdx(i)
    setEditText(String(items[i]?.[labelKey] ?? ""))
  }
  const commitEdit = () => {
    if (editingIdx === null) return
    const v = editText.trim()
    if (v) onChange(items.map((it, idx) => (idx === editingIdx ? { ...it, [labelKey]: v } : it)))
    setEditingIdx(null)
  }

  return (
    <div className="space-y-1.5">
      <span className="text-micro font-medium text-lia-text-disabled uppercase tracking-wide">{label}</span>
      <div className="flex flex-wrap gap-1.5">
        {items.map((it, i) =>
          editingIdx === i ? (
            <input
              key={i}
              data-testid={`edit-${testidPrefix}-${i}`}
              value={editText}
              autoFocus
              onChange={(e) => setEditText(e.target.value)}
              onBlur={commitEdit}
              onKeyDown={(e) => {
                if (e.key === "Enter") commitEdit()
                if (e.key === "Escape") setEditingIdx(null)
              }}
              className="px-2 py-0.5 text-micro rounded-full bg-lia-bg-tertiary text-lia-text-primary border border-wedo-cyan focus:outline-none"
              aria-label={`Editar ${label} ${i + 1}`}
            />
          ) : (
            <span key={i} className="inline-flex items-center">
              <Chip
                density="compact"
                variant="info"
                className="cursor-text"
                onClick={() => startEdit(i)}
                title="Clique para editar"
              >
                {String(it[labelKey] ?? "")}
                <button
                  type="button"
                  data-testid={`remove-${testidPrefix}-${i}`}
                  onClick={(e) => {
                    e.stopPropagation()
                    remove(i)
                  }}
                  className="ml-1 -mr-0.5 rounded-full hover:text-status-danger transition-colors"
                  aria-label={`Remover ${String(it[labelKey] ?? "")}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            </span>
          ),
        )}
        <span className="inline-flex items-center gap-1 rounded-full border border-dashed border-lia-border-subtle px-1.5">
          <Plus className="w-3 h-3 text-lia-text-disabled" />
          <input
            data-testid={`add-${testidPrefix}-input`}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") add()
            }}
            placeholder="adicionar"
            className="w-20 bg-transparent text-micro text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none py-0.5"
            aria-label={`Adicionar ${label}`}
          />
        </span>
      </div>
    </div>
  )
}

/**
 * IntakePanel — ficha viva do estágio de intake (Fase 5a).
 *
 * Zona bloqueante (título/senioridade/modelo/modo de triagem) + zona
 * enriquecedora (depto/localização/contrato/salário) + chips de competências
 * editáveis (Fase 2/3). Edição local via onUpdate; write-back ao backend é 5b.
 * Preserva: edição de raw_input, keywords, JDs similares, indicador de processamento.
 */
export function IntakePanel({ data, onUpdate }: Props) {
  const rawInput = (data.raw_input as string) || ""
  const extractedKeywords = (data.extracted_keywords as string[]) || []
  const source = (data.source as string) || "chat"
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(rawInput)

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

  // ── Ficha viva: zonas + competências (derivadas de data, sem hooks) ──
  const screeningMode = (data.screening_mode as string) || ""
  const blockingFields = [
    { label: "Título", value: parsedTitle },
    { label: "Senioridade", value: (data.parsed_seniority as string) || "" },
    { label: "Modelo de trabalho", value: (data.parsed_model as string) || "" },
    { label: "Modo de triagem", value: screeningMode ? (MODE_LABEL[screeningMode] || screeningMode) : "" },
  ]
  const enrichingFields = [
    { label: "Departamento", value: parsedDepartment },
    { label: "Localização", value: (data.parsed_location as string) || "" },
    { label: "Contrato", value: (data.parsed_employment_type as string) || "" },
    { label: "Salário", value: salaryText(data) },
  ]
  const hasSignal = Boolean(rawInput) || blockingFields.some((f) => f.value) || enrichingFields.some((f) => f.value)

  const suggestions = (data.suggestions_data as { competencies?: { technical?: Competency[]; behavioral?: Competency[] } } | undefined)?.competencies
  const technical = (data.confirmed_technical_competencies as Competency[]) ?? suggestions?.technical ?? []
  const behavioral = (data.confirmed_behavioral_competencies as Competency[]) ?? suggestions?.behavioral ?? []
  const hasCompetencies = technical.length > 0 || behavioral.length > 0

  return (
    <div className="p-4 space-y-4">
      {/* Source indicator */}
      <div className="flex items-center justify-between text-xs text-lia-text-disabled">
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5" />
          <span>{source === "file" ? "Enviado via arquivo" : "Descrito no chat"}</span>
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
              <button onClick={() => setIsEditing(false)} className="px-2 py-1 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover rounded">
                Cancelar
              </button>
              <button onClick={handleSaveEdit} className="flex items-center gap-1 px-2 py-1 text-xs text-white bg-wedo-cyan rounded hover:bg-wedo-cyan/90">
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

      {/* ── Ficha viva: zona bloqueante ── */}
      {hasSignal && (
        <div data-testid="intake-blocking-zone" className="space-y-1">
          <p className="text-micro font-semibold text-lia-text-disabled uppercase tracking-wider">Falta para avançar</p>
          {blockingFields.map((f) => (
            <FichaField key={f.label} label={f.label} value={f.value} />
          ))}
        </div>
      )}

      {/* ── Ficha viva: zona enriquecedora ── */}
      {hasSignal && (
        <div data-testid="intake-enriching-zone" className="space-y-1 pt-1">
          <p className="text-micro font-medium text-lia-text-disabled uppercase tracking-wide opacity-80">Enriquecer (opcional)</p>
          {enrichingFields.map((f) => (
            <FichaField key={f.label} label={f.label} value={f.value} />
          ))}
        </div>
      )}

      {/* ── Competências confirmadas/sugeridas ── */}
      {hasCompetencies && (
        <div data-testid="intake-competencies" className="space-y-3 pt-1 border-t border-lia-border-subtle">
          <p className="text-micro font-semibold text-lia-text-disabled uppercase tracking-wider pt-3">Competências</p>
          <CompetencyChipGroup
            label="Técnicas"
            items={technical}
            labelKey="skill"
            testidPrefix="technical"
            newItem={(v) => ({ skill: v, contexto: "" })}
            onChange={(next) => onUpdate?.({ confirmed_technical_competencies: next })}
          />
          <CompetencyChipGroup
            label="Comportamentais"
            items={behavioral}
            labelKey="competencia"
            testidPrefix="behavioral"
            newItem={(v) => ({ competencia: v, contexto: "", trait_big_five: "conscientiousness" })}
            onChange={(next) => onUpdate?.({ confirmed_behavioral_competencies: next })}
          />
        </div>
      )}

      {/* Extracted keywords */}
      {extractedKeywords.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
            <Tag className="w-3 h-3" />
            <span>Palavras-chave detectadas</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {extractedKeywords.map((kw, i) => (
              <span key={i} className="px-2 py-0.5 text-micro rounded-full bg-wedo-cyan/10 text-wedo-cyan border border-wedo-cyan/20">
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* JD similar history suggestions (Sprint B Phase 1) */}
      {!data.jd_similar_dismissed && (similarJds.length > 0 || jdSimilarLoading) && (
        <JdSimilarCard items={similarJds} loading={jdSimilarLoading} onReuse={handleReuseJd} onCreateFresh={handleCreateFresh} />
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
