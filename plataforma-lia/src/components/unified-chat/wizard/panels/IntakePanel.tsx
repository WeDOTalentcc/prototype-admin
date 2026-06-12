"use client"

import React, { useEffect, useState } from "react"
import { FileText, Tag, Edit2, Check, X, Plus, CircleDashed } from "lucide-react"
import { cn } from "@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { useAuthStore } from "@/stores/auth-store"
import { useJdSimilar } from "@/hooks/jobs/use-jd-similar"
import { ComplianceBadge } from "@/components/lia-float/ComplianceBadge"
import { JdSimilarCard } from "./JdSimilarCard"
import { WizardSuggestionChips } from "./WizardSuggestionChips"

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

/** Coerção defensiva: qualquer valor (string, objeto {city,state,country}, etc.)
 * vira string renderável. Evita "Objects are not valid as a React child" quando
 * o backend manda parsed_location como objeto. */
function fieldText(v: unknown): string {
  if (v == null) return ""
  if (typeof v === "string") return v
  if (typeof v === "number" || typeof v === "boolean") return String(v)
  if (typeof v === "object") {
    const o = v as Record<string, unknown>
    const located = [o.city, o.state, o.country].filter(Boolean).map(String)
    if (located.length) return located.join(", ")
    return Object.values(o).filter((x) => x != null && x !== "").map(String).join(", ")
  }
  return String(v)
}


function isValidEmail(v: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())
}

/** Uma linha de campo da ficha: rótulo + valor (Chip success) ou pendente.
 *
 * Quando `editKey` é passado, o campo vira inline click-to-edit (mesmo padrão
 * dos chips de competência e da edição de raw_input): clicar abre input, Enter
 * salva via onUpdate({ [editKey]: valor }), Esc/blur cancela. `editKey` é o
 * nome do campo no SCHEMA do backend (manager_name, work_model, contract_type…),
 * porque o write-back viaja como context.right_panel_form, que o IntakeExtractor
 * honra a 0.95 de confiança. `type="email"` valida antes de salvar. */
function FichaField({
  label,
  value,
  editKey,
  type = "text",
  inferred,
  onUpdate,
}: {
  label: string
  value: string
  editKey?: string
  type?: "text" | "email"
  inferred?: boolean
  onUpdate?: (updates: Record<string, unknown>) => void
}) {
  const filled = Boolean(value)
  const editable = Boolean(editKey && onUpdate)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const [invalid, setInvalid] = useState(false)

  const begin = () => {
    if (!editable) return
    setDraft(value)
    setInvalid(false)
    setEditing(true)
  }
  const commit = () => {
    const v = draft.trim()
    if (type === "email" && v && !isValidEmail(v)) {
      setInvalid(true)
      return
    }
    if (v !== value) onUpdate?.({ [editKey as string]: v })
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="flex items-center justify-between gap-3 py-1">
        <span className="text-xs text-lia-text-primary">{label}</span>
        <input
          type={type}
          value={draft}
          autoFocus
          data-testid={`edit-ficha-${editKey}`}
          onChange={(e) => { setDraft(e.target.value); setInvalid(false) }}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit()
            if (e.key === "Escape") setEditing(false)
          }}
          aria-label={`Editar ${label}`}
          aria-invalid={invalid}
          className={cn(
            "max-w-[60%] px-2 py-0.5 text-xs rounded bg-lia-bg-tertiary text-lia-text-primary border focus:outline-none",
            invalid ? "border-status-danger" : "border-wedo-cyan",
          )}
        />
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between gap-3 py-1">
      <span className="text-xs text-lia-text-primary">{label}</span>
      {filled ? (
        <Chip
          density="relaxed"
          variant="success"
          className={cn("truncate max-w-[60%]", editable && "cursor-text")}
          onClick={editable ? begin : undefined}
          title={editable ? "Clique para editar" : undefined}
        >
          {value}
          {inferred && (
            <span className="ml-1 text-[10px] text-wedo-cyan bg-wedo-cyan/10 px-1.5 py-0.5 rounded-full font-normal">inferido</span>
          )}
        </Chip>
      ) : editable ? (
        <button
          type="button"
          onClick={begin}
          data-testid={`add-ficha-${editKey}`}
          className="flex items-center gap-1 text-micro text-lia-text-disabled hover:text-wedo-cyan transition-colors"
          aria-label={`Adicionar ${label}`}
        >
          <Plus className="w-3 h-3" />
          adicionar
        </button>
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
      <span className="text-micro font-medium text-lia-text-secondary uppercase tracking-wide">{label}</span>
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
                density="relaxed"
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
  const parsedTitle = fieldText(data.parsed_title)
  const parsedDepartment = fieldText(data.parsed_department)
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
  // editKey = nome do campo no schema do backend (right_panel_form). Campos sem
  // editKey ficam display-only (modo de triagem tem affordance própria de chips;
  // salário tem o SalaryPanel dedicado).
  const blockingFields: { label: string; value: string; editKey?: string; type?: "text" | "email"; inferred?: boolean }[] = [
    { label: "Título", value: fieldText(data.parsed_title), editKey: "title" },
    { label: "Senioridade", value: fieldText(data.parsed_seniority), editKey: "seniority", inferred: Boolean(data.seniority_inferred_from_title) },
    { label: "Modelo de trabalho", value: fieldText(data.parsed_model), editKey: "work_model" },
  ]
  const enrichingFields: { label: string; value: string; editKey?: string; type?: "text" | "email"; inferred?: boolean }[] = [
    { label: "Departamento", value: fieldText(data.parsed_department), editKey: "department", inferred: Boolean(data.department_inferred_from_title) },
    { label: "Localização", value: fieldText(data.parsed_location), editKey: "location" },
    { label: "Contrato", value: fieldText(data.parsed_employment_type), editKey: "contract_type" },
    { label: "Gestor responsável", value: fieldText(data.parsed_manager_name), editKey: "manager_name", inferred: Boolean(data.manager_name_suggested_from_email) },
    { label: "Email do gestor", value: fieldText(data.parsed_manager_email), editKey: "manager_email", type: "email" },
    { label: "Salário", value: salaryText(data) },
    { label: "Modo de triagem", value: screeningMode ? (MODE_LABEL[screeningMode] || screeningMode) : "" },
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
          <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider">Falta para avançar</p>
          {blockingFields.map((f) => (
            <FichaField key={f.label} label={f.label} value={f.value} editKey={f.editKey} type={f.type} inferred={f.inferred} onUpdate={onUpdate} />
          ))}
        </div>
      )}

      {/* ── Ficha viva: zona enriquecedora ── */}
      {hasSignal && (
        <div data-testid="intake-enriching-zone" className="space-y-1 pt-1">
          <p className="text-micro font-medium text-lia-text-secondary uppercase tracking-wide">Enriquecer (opcional)</p>
          {enrichingFields.map((f) => (
            <FichaField key={f.label} label={f.label} value={f.value} editKey={f.editKey} type={f.type} inferred={f.inferred} onUpdate={onUpdate} />
          ))}
          <ComplianceBadge className="mt-1" />
        </div>
      )}

      {/* ── Competências confirmadas/sugeridas ── */}
      {hasCompetencies && (
        <div data-testid="intake-competencies" className="space-y-3 pt-1 border-t border-lia-border-subtle">
          <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider pt-3">Competências</p>
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

      {/* W3-D: chips de sugestão do histórico da empresa */}
      <WizardSuggestionChips data={data} onUpdate={onUpdate} />

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
