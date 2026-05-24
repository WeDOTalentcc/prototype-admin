"use client"

import { useState, useCallback } from "react"
import { createPortal } from "react-dom"
import { X, Plus, Trash2, Info, Lock, ChevronDown, ChevronUp } from "lucide-react"
import type {
  CompensationPolicyRecord,
  SalaryBand,
  VariableCompItem,
} from "./compensation-policies-types"
import {
  defaultPolicy,
  POLICY_TYPE_OPTIONS,
  SENIORITY_LEVEL_OPTIONS,
  VARIABLE_KIND_OPTIONS,
  FREQUENCY_OPTIONS,
  SALARY_LEVEL_ROWS,
} from "./compensation-policies-types"

// ---------------------------------------------------------------------------
// Sub-tabs
// ---------------------------------------------------------------------------

type Tab = "bands" | "variable" | "equity" | "eligibility" | "validity"

const TABS: { id: Tab; label: string }[] = [
  { id: "bands",       label: "Bandas Salariais" },
  { id: "variable",    label: "Verbas Variáveis" },
  { id: "equity",      label: "Equity" },
  { id: "eligibility", label: "Elegibilidade" },
  { id: "validity",    label: "Vigência & Aprovação" },
]

// ---------------------------------------------------------------------------
// ChipMultiSelect (reutilizável interno)
// ---------------------------------------------------------------------------

function ChipMultiSelect({
  options,
  value,
  onChange,
}: {
  options: readonly { id: string; label: string }[]
  value: string[]
  onChange: (v: string[]) => void
}) {
  const toggle = (id: string) => {
    onChange(value.includes(id) ? value.filter((v) => v !== id) : [...value, id])
  }
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt.id}
          type="button"
          onClick={() => toggle(opt.id)}
          className={`rounded-full border px-3 py-1 text-xs transition-all ${
            value.includes(opt.id)
              ? "border-lia-primary bg-lia-primary/10 text-lia-primary"
              : "border-lia-border bg-lia-surface text-lia-text-secondary hover:border-lia-primary/50"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// SalaryBandsTab
// ---------------------------------------------------------------------------

function SalaryBandsTab({
  bands,
  onChange,
}: {
  bands: SalaryBand[]
  onChange: (bands: SalaryBand[]) => void
}) {
  const updateField = (idx: number, field: keyof SalaryBand, val: string | number) => {
    const next = [...bands]
    next[idx] = { ...next[idx], [field]: val }
    onChange(next)
  }

  const addRow = () => {
    onChange([...bands, { level: "", min: 0, mid: 0, max: 0, currency: "BRL" }])
  }

  const removeRow = (idx: number) => onChange(bands.filter((_, i) => i !== idx))

  return (
    <div className="space-y-4">
      <p className="text-sm text-lia-text-secondary">
        Defina faixas salariais (Min / Mid / Max) por nível de senioridade. O valor Mid é referência de mercado.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-lia-border text-lia-text-secondary text-xs">
              <th className="pb-2 text-left font-medium">Nível</th>
              <th className="pb-2 text-right font-medium">Mín (R$)</th>
              <th className="pb-2 text-right font-medium">Mid (R$)</th>
              <th className="pb-2 text-right font-medium">Máx (R$)</th>
              <th className="pb-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-lia-border/50">
            {bands.map((band, idx) => (
              <tr key={idx}>
                <td className="py-2 pr-2">
                  <input
                    className="w-24 rounded border border-lia-border bg-lia-surface px-2 py-1 text-sm focus:border-lia-primary focus:outline-none"
                    value={band.level}
                    onChange={(e) => updateField(idx, "level", e.target.value)}
                    placeholder="junior"
                    list="seniority-levels"
                  />
                  <datalist id="seniority-levels">
                    {SALARY_LEVEL_ROWS.map((l) => <option key={l} value={l} />)}
                  </datalist>
                </td>
                {(["min", "mid", "max"] as const).map((field) => (
                  <td key={field} className="py-2 px-1">
                    <input
                      type="number"
                      className="w-28 rounded border border-lia-border bg-lia-surface px-2 py-1 text-sm text-right focus:border-lia-primary focus:outline-none"
                      value={band[field]}
                      onChange={(e) => updateField(idx, field, Number(e.target.value))}
                      min={0}
                    />
                  </td>
                ))}
                <td className="py-2 pl-2">
                  <button
                    type="button"
                    onClick={() => removeRow(idx)}
                    className="rounded p-1 text-lia-text-secondary hover:text-red-500"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        type="button"
        onClick={addRow}
        className="flex items-center gap-1.5 text-sm text-lia-primary hover:underline"
      >
        <Plus className="h-4 w-4" /> Adicionar nível
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// VariableCompTab
// ---------------------------------------------------------------------------

function VariableCompTab({
  items,
  onChange,
}: {
  items: VariableCompItem[]
  onChange: (items: VariableCompItem[]) => void
}) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  const addItem = (kind: VariableCompItem["kind"]) => {
    const newItem: VariableCompItem = { kind, name: VARIABLE_KIND_OPTIONS.find(k => k.id === kind)?.label ?? kind }
    const next = [...items, newItem]
    onChange(next)
    setExpandedIdx(next.length - 1)
  }

  const removeItem = (idx: number) => {
    onChange(items.filter((_, i) => i !== idx))
    setExpandedIdx(null)
  }

  const updateItem = (idx: number, patch: Partial<VariableCompItem>) => {
    const next = [...items]
    next[idx] = { ...next[idx], ...patch }
    onChange(next)
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-lia-text-secondary">
        Adicione verbas variáveis tipadas. Cada verba tem seu próprio schema de cálculo e frequência.
      </p>

      {/* Add buttons */}
      <div className="flex flex-wrap gap-2">
        {VARIABLE_KIND_OPTIONS.map((kind) => (
          <button
            key={kind.id}
            type="button"
            onClick={() => addItem(kind.id as VariableCompItem["kind"])}
            className="flex items-center gap-1.5 rounded-full border border-lia-border px-3 py-1 text-xs text-lia-text-secondary hover:border-lia-primary hover:text-lia-primary"
          >
            <Plus className="h-3 w-3" /> {kind.label}
          </button>
        ))}
      </div>

      {/* Item list */}
      <div className="space-y-2">
        {items.map((item, idx) => {
          const isOpen = expandedIdx === idx
          const kindMeta = VARIABLE_KIND_OPTIONS.find((k) => k.id === item.kind)
          return (
            <div key={idx} className="rounded-lg border border-lia-border overflow-hidden">
              {/* Row header */}
              <div
                className="flex items-center gap-2 px-3 py-2 cursor-pointer bg-lia-surface hover:bg-lia-muted/10"
                onClick={() => setExpandedIdx(isOpen ? null : idx)}
              >
                <span className="rounded-full bg-lia-primary/10 px-2 py-0.5 text-xs text-lia-primary font-medium">
                  {kindMeta?.label ?? item.kind}
                </span>
                <span className="flex-1 text-sm font-medium text-lia-text-primary">{item.name || "(sem nome)"}</span>
                {item.frequency && (
                  <span className="text-xs text-lia-text-secondary">
                    {FREQUENCY_OPTIONS.find(f => f.id === item.frequency)?.label}
                  </span>
                )}
                {item.max_pct !== undefined && (
                  <span className="text-xs text-lia-text-secondary">até {item.max_pct}%</span>
                )}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); removeItem(idx) }}
                  className="ml-1 rounded p-1 text-lia-text-secondary hover:text-red-500"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
                {isOpen ? <ChevronUp className="h-4 w-4 text-lia-text-secondary" /> : <ChevronDown className="h-4 w-4 text-lia-text-secondary" />}
              </div>

              {/* Expanded form */}
              {isOpen && (
                <div className="border-t border-lia-border bg-lia-bg-primary/40 p-3 grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="text-xs text-lia-text-secondary">Nome da verba</label>
                    <input
                      className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                      value={item.name}
                      onChange={(e) => updateItem(idx, { name: e.target.value })}
                      placeholder="Ex: PLR Anual 2026"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-lia-text-secondary">Base de cálculo</label>
                    <select
                      className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                      value={item.base ?? ""}
                      onChange={(e) => updateItem(idx, { base: e.target.value })}
                    >
                      <option value="">Selecionar</option>
                      <option value="salary_anual">% do salário anual</option>
                      <option value="salary_mensal">% do salário mensal</option>
                      <option value="revenue">% da receita</option>
                      <option value="result">Resultado financeiro (PPR)</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-lia-text-secondary">Frequência</label>
                    <select
                      className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                      value={item.frequency ?? ""}
                      onChange={(e) => updateItem(idx, { frequency: e.target.value })}
                    >
                      <option value="">Selecionar</option>
                      {FREQUENCY_OPTIONS.map((f) => (
                        <option key={f.id} value={f.id}>{f.label}</option>
                      ))}
                    </select>
                  </div>
                  {item.kind !== "commission" && (
                    <>
                      <div>
                        <label className="text-xs text-lia-text-secondary">% Mínimo</label>
                        <input
                          type="number" min={0} max={100}
                          className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                          value={item.min_pct ?? ""}
                          onChange={(e) => updateItem(idx, { min_pct: Number(e.target.value) })}
                          placeholder="0"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-lia-text-secondary">% Máximo / Alvo</label>
                        <input
                          type="number" min={0} max={500}
                          className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                          value={item.max_pct ?? item.value_pct ?? ""}
                          onChange={(e) => updateItem(idx, { max_pct: Number(e.target.value), value_pct: Number(e.target.value) })}
                          placeholder="15"
                        />
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )
        })}
        {items.length === 0 && (
          <p className="text-center text-sm text-lia-text-secondary py-4">
            Nenhuma verba variável adicionada. Clique em um tipo acima para começar.
          </p>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// EligibilityTab
// ---------------------------------------------------------------------------

function EligibilityTab({
  departments,
  seniority,
  roles,
  onChangeDepts,
  onChangeSeniority,
  onChangeRoles,
}: {
  departments: string[]
  seniority: string[]
  roles: string[]
  onChangeDepts: (v: string[]) => void
  onChangeSeniority: (v: string[]) => void
  onChangeRoles: (v: string[]) => void
}) {
  const [rolesInput, setRolesInput] = useState("")

  const addRole = () => {
    const trimmed = rolesInput.trim()
    if (trimmed && !roles.includes(trimmed)) {
      onChangeRoles([...roles, trimmed])
    }
    setRolesInput("")
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-status-warning/20 bg-status-warning/10 px-3 py-2 flex items-start gap-2 text-xs text-status-warning">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>
          Elegibilidade por atributo protegido (raça, gênero, idade, religião) é <strong>bloqueada</strong> automaticamente pelo backend (LGPD + Fairness Guard).
          Use apenas critérios neutros: cargo, senioridade, departamento.
        </span>
      </div>

      <div>
        <label className="text-sm font-medium text-lia-text-primary">Senioridade aplicável</label>
        <p className="text-xs text-lia-text-secondary mb-2">Deixe vazio para aplicar a todos os níveis.</p>
        <ChipMultiSelect
          options={SENIORITY_LEVEL_OPTIONS}
          value={seniority}
          onChange={onChangeSeniority}
        />
      </div>

      <div>
        <label className="text-sm font-medium text-lia-text-primary">Departamentos aplicáveis</label>
        <p className="text-xs text-lia-text-secondary mb-2">Deixe vazio para todos os departamentos.</p>
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
            placeholder="Ex: comercial, engineering"
            value={departments.join(", ")}
            onChange={(e) =>
              onChangeDepts(
                e.target.value
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
              )
            }
          />
        </div>
        {departments.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {departments.map((d) => (
              <span key={d} className="inline-flex items-center gap-1 rounded-full bg-lia-primary/10 px-2 py-0.5 text-xs text-lia-primary">
                {d}
                <button type="button" onClick={() => onChangeDepts(departments.filter(x => x !== d))} className="ml-0.5 hover:text-red-500">×</button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="text-sm font-medium text-lia-text-primary">Cargos aplicáveis</label>
        <p className="text-xs text-lia-text-secondary mb-2">Deixe vazio para todos os cargos.</p>
        <div className="flex gap-2">
          <input
            className="flex-1 rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
            placeholder="Adicionar cargo..."
            value={rolesInput}
            onChange={(e) => setRolesInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRole())}
          />
          <button
            type="button"
            onClick={addRole}
            className="rounded border border-lia-border px-3 py-1.5 text-sm hover:border-lia-primary hover:text-lia-primary"
          >
            Adicionar
          </button>
        </div>
        {roles.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {roles.map((r) => (
              <span key={r} className="inline-flex items-center gap-1 rounded-full bg-lia-primary/10 px-2 py-0.5 text-xs text-lia-primary">
                {r}
                <button type="button" onClick={() => onChangeRoles(roles.filter(x => x !== r))} className="ml-0.5 hover:text-red-500">×</button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ValidityTab
// ---------------------------------------------------------------------------

function ValidityTab({
  policy,
  onChange,
}: {
  policy: CompensationPolicyRecord
  onChange: (patch: Partial<CompensationPolicyRecord>) => void
}) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-lia-text-secondary">Vigência — início</label>
          <input
            type="date"
            className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
            value={policy.effective_from?.slice(0, 10) ?? ""}
            onChange={(e) => onChange({ effective_from: e.target.value || undefined })}
          />
        </div>
        <div>
          <label className="text-xs text-lia-text-secondary">Vigência — fim</label>
          <input
            type="date"
            className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
            value={policy.effective_until?.slice(0, 10) ?? ""}
            onChange={(e) => onChange({ effective_until: e.target.value || undefined })}
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-lia-text-secondary flex items-center gap-1">
          <Lock className="h-3 w-3" /> Aprovado por (user ID — informação interna)
        </label>
        <input
          className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
          value={policy.approved_by ?? ""}
          onChange={(e) => onChange({ approved_by: e.target.value || undefined })}
          placeholder="ID do aprovador (mascarado em logs e JD publicada)"
        />
      </div>

      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="rounded border-lia-border"
            checked={policy.is_default}
            onChange={(e) => onChange({ is_default: e.target.checked })}
          />
          <span className="text-sm text-lia-text-primary">Marcar como política padrão da empresa</span>
        </label>
      </div>

      {/* Version info (read-only) */}
      {policy.id && (
        <div className="rounded-lg border border-lia-border bg-lia-surface p-3 text-xs text-lia-text-secondary space-y-1">
          <div className="font-medium text-lia-text-primary">Histórico de versões</div>
          <div>Versão atual: <strong>v{policy.version}</strong></div>
          {policy.revision_history.length > 0 && (
            <ul className="mt-1 space-y-0.5">
              {policy.revision_history.slice(-3).map((rev, idx) => (
                <li key={idx}>
                  v{(rev as Record<string, unknown>).version as number} — {(rev as Record<string, unknown>).updated_at as string}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main modal
// ---------------------------------------------------------------------------

interface Props {
  isOpen: boolean
  initialData?: CompensationPolicyRecord | null
  onClose: () => void
  onSave: (data: CompensationPolicyRecord) => Promise<void>
  isSaving: boolean
  error: string | null
}

export function CompensationPolicyFormModal({
  isOpen,
  initialData,
  onClose,
  onSave,
  isSaving,
  error,
}: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("bands")
  const [form, setForm] = useState<CompensationPolicyRecord>(
    () => initialData ?? { ...defaultPolicy }
  )

  const patch = useCallback((update: Partial<CompensationPolicyRecord>) => {
    setForm((prev) => ({ ...prev, ...update }))
  }, [])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onSave(form)
  }

  const isEdit = Boolean(initialData?.id)

  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="relative flex flex-col w-full max-w-3xl max-h-[90vh] rounded-xl border border-lia-border bg-lia-surface shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-lia-border">
          <div>
            <h2 className="text-base font-semibold text-lia-text-primary">
              {isEdit ? "Editar Política de Remuneração" : "Nova Política de Remuneração"}
            </h2>
            <p className="text-xs text-lia-text-secondary mt-0.5">
              {isEdit ? `v${form.version} — alterações geram nova versão automaticamente` : "PRV com verbas tipadas (PLR, Bônus, Comissão, Equity)"}
            </p>
          </div>
          <button onClick={onClose} className="rounded p-1 hover:bg-lia-muted/20 text-lia-text-secondary">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Basic fields */}
        <div className="grid grid-cols-2 gap-3 px-5 pt-4">
          <div className="col-span-2">
            <label className="text-xs text-lia-text-secondary">Nome da política *</label>
            <input
              required
              className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
              value={form.name}
              onChange={(e) => patch({ name: e.target.value })}
              placeholder="Ex: PLR Anual Padrão 2026"
            />
          </div>
          <div>
            <label className="text-xs text-lia-text-secondary">Tipo</label>
            <select
              className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
              value={form.policy_type}
              onChange={(e) => patch({ policy_type: e.target.value })}
            >
              {POLICY_TYPE_OPTIONS.map((o) => (
                <option key={o.id} value={o.id}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-lia-text-secondary">Moeda</label>
            <select
              className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-2 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
              value={form.currency}
              onChange={(e) => patch({ currency: e.target.value })}
            >
              <option value="BRL">BRL — Real Brasileiro</option>
              <option value="USD">USD — Dólar</option>
              <option value="EUR">EUR — Euro</option>
              <option value="GBP">GBP — Libra Esterlina</option>  {/* P1-W2-09 */}
              <option value="AUD">AUD — Dólar Australiano</option>  {/* P1-W2-09 */}
            </select>
          </div>
          <div className="col-span-2">
            <label className="text-xs text-lia-text-secondary">Descrição</label>
            <textarea
              rows={2}
              className="mt-0.5 w-full rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm resize-none focus:border-lia-primary focus:outline-none"
              value={form.description}
              onChange={(e) => patch({ description: e.target.value })}
              placeholder="Descreva brevemente o objetivo desta política..."
            />
          </div>
        </div>

        {/* Sub-tabs */}
        <div className="flex border-b border-lia-border px-5 mt-3 gap-1 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`shrink-0 border-b-2 pb-2 pt-1 px-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-lia-primary text-lia-primary"
                  : "border-transparent text-lia-text-secondary hover:text-lia-text-primary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {activeTab === "bands" && (
            <SalaryBandsTab
              bands={form.salary_bands}
              onChange={(bands) => patch({ salary_bands: bands })}
            />
          )}
          {activeTab === "variable" && (
            <VariableCompTab
              items={form.variable_compensation.items}
              onChange={(items) => patch({ variable_compensation: { ...form.variable_compensation, items } })}
            />
          )}
          {activeTab === "equity" && (
            <div className="space-y-3">
              <p className="text-sm text-lia-text-secondary">
                Configure regras de equity (stock options, RSUs, phantom shares). Campo livre em formato JSON.
              </p>
              <label className="text-xs text-lia-text-secondary">Cliff (meses)</label>
              <input
                type="number" min={0}
                className="w-full rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                value={(form.equity_rules.cliff_months as number | undefined) ?? ""}
                onChange={(e) => patch({ equity_rules: { ...form.equity_rules, cliff_months: Number(e.target.value) } })}
                placeholder="12"
              />
              <label className="text-xs text-lia-text-secondary">Vesting (meses)</label>
              <input
                type="number" min={0}
                className="w-full rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm focus:border-lia-primary focus:outline-none"
                value={(form.equity_rules.vesting_months as number | undefined) ?? ""}
                onChange={(e) => patch({ equity_rules: { ...form.equity_rules, vesting_months: Number(e.target.value) } })}
                placeholder="48"
              />
              <label className="text-xs text-lia-text-secondary">Descrição do programa</label>
              <textarea
                rows={3}
                className="w-full rounded border border-lia-border bg-lia-surface px-3 py-1.5 text-sm resize-none focus:border-lia-primary focus:outline-none"
                value={(form.equity_rules.description as string | undefined) ?? ""}
                onChange={(e) => patch({ equity_rules: { ...form.equity_rules, description: e.target.value } })}
                placeholder="Ex: Stock options com cliff de 12 meses e vesting linear em 48 meses."
              />
            </div>
          )}
          {activeTab === "eligibility" && (
            <EligibilityTab
              departments={form.applicable_departments}
              seniority={form.applicable_seniority}
              roles={form.applicable_roles}
              onChangeDepts={(v) => patch({ applicable_departments: v })}
              onChangeSeniority={(v) => patch({ applicable_seniority: v })}
              onChangeRoles={(v) => patch({ applicable_roles: v })}
            />
          )}
          {activeTab === "validity" && (
            <ValidityTab policy={form} onChange={patch} />
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-lia-border px-5 py-3 flex items-center justify-between gap-3">
          {error && (
            <p className="text-sm text-status-error flex-1 truncate">{error}</p>
          )}
          {!error && <div className="flex-1" />}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-lia-border px-4 py-2 text-sm text-lia-text-secondary hover:bg-lia-muted/20"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSaving || !form.name.trim()}
              className="rounded-lg bg-lia-btn-primary-bg px-4 py-2 text-sm font-medium text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-60"
            >
              {isSaving ? "Salvando..." : isEdit ? `Salvar v${form.version + 1}` : "Criar Política"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  if (typeof document === "undefined") return null
  return createPortal(modalContent, document.body)
}
