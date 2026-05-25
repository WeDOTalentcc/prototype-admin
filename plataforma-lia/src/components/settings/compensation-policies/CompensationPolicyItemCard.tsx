"use client"

import { useState } from "react"
import { MoreVertical, Edit2, PowerOff, CheckCircle, Clock, Star } from "lucide-react"
import type { CompensationPolicyRecord } from "./compensation-policies-types"
import { VARIABLE_KIND_OPTIONS } from "./compensation-policies-types"

interface Props {
  policy: CompensationPolicyRecord
  onEdit: (p: CompensationPolicyRecord) => void
  onDeactivate: (p: CompensationPolicyRecord) => void
}

const POLICY_TYPE_LABELS: Record<string, string> = {
  hierarchical_bands: "Bandas Salariais",
  variable_only: "Variável Puro",
  mixed: "Misto",
}

export function CompensationPolicyItemCard({ policy, onEdit, onDeactivate }: Props) {
  const [menuOpen, setMenuOpen] = useState(false)
  const kinds = policy.variable_compensation?.items?.map((i) => i.kind) ?? []
  const kindLabels = VARIABLE_KIND_OPTIONS.filter((k) => kinds.includes(k.id as typeof k.id)).map((k) => k.label)

  const hasBands = (policy.salary_bands ?? []).length > 0
  const bandCount = policy.salary_bands?.length ?? 0
  const itemCount = policy.variable_compensation?.items?.length ?? 0

  return (
    <div className={`relative rounded-lg border p-4 transition-all ${policy.is_active ? "border-lia-border-default bg-lia-bg-elevated hover:border-wedo-cyan/40" : "border-lia-border-default/50 bg-lia-bg-elevated/60 opacity-60"}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-lia-text-primary truncate">{policy.name}</span>
            {policy.is_default && (
              <span className="inline-flex items-center gap-1 rounded-full bg-wedo-cyan/10 px-2 py-0.5 text-micro text-wedo-cyan">
                <Star className="h-3 w-3" /> Padrão
              </span>
            )}
            {!policy.is_active && (
              <span className="inline-flex items-center gap-1 rounded-full bg-lia-bg-tertiary/20 px-2 py-0.5 text-micro text-lia-text-secondary">
                Inativa
              </span>
            )}
          </div>
          {policy.description && (
            <p className="mt-0.5 text-sm text-lia-text-secondary line-clamp-1">{policy.description}</p>
          )}
        </div>

        {/* Menu */}
        <div className="relative shrink-0">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="rounded p-1 hover:bg-lia-bg-tertiary/20 text-lia-text-secondary"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          {menuOpen && (
            <div
              className="absolute right-0 top-7 z-10 min-w-[150px] rounded-lg border border-lia-border-default bg-lia-bg-elevated shadow-lg"
              onBlur={() => setMenuOpen(false)}
            >
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary/20"
                onClick={() => { setMenuOpen(false); onEdit(policy) }}
              >
                <Edit2 className="h-3.5 w-3.5" /> Editar
              </button>
              {policy.is_active && (
                <button
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-status-error hover:bg-status-error/10"
                  onClick={() => { setMenuOpen(false); onDeactivate(policy) }}
                >
                  <PowerOff className="h-3.5 w-3.5" /> Desativar
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tags */}
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {policy.policy_type && (
          <span className="rounded-full border border-lia-border-default px-2 py-0.5 text-lia-text-secondary">
            {POLICY_TYPE_LABELS[policy.policy_type] ?? policy.policy_type}
          </span>
        )}
        {policy.currency && policy.currency !== "BRL" && (
          <span className="rounded-full border border-lia-border-default px-2 py-0.5 text-lia-text-secondary">
            {policy.currency}
          </span>
        )}
        {hasBands && (
          <span className="rounded-full bg-wedo-cyan/10 border border-wedo-cyan/20 px-2 py-0.5 text-wedo-cyan">
            {bandCount} banda{bandCount !== 1 ? "s" : ""}
          </span>
        )}
        {kindLabels.map((label) => (
          <span key={label} className="rounded-full bg-wedo-cyan/10 border border-wedo-cyan/20 px-2 py-0.5 text-wedo-cyan">
            {label}
          </span>
        ))}
      </div>

      {/* Footer: vigência + versão */}
      <div className="mt-3 flex items-center justify-between text-xs text-lia-text-secondary">
        <div className="flex items-center gap-3">
          {policy.effective_from && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {new Date(policy.effective_from).toLocaleDateString("pt-BR")}
              {policy.effective_until && ` → ${new Date(policy.effective_until).toLocaleDateString("pt-BR")}`}
            </span>
          )}
          {(policy.applicable_seniority?.length ?? 0) > 0 && (
            <span>{policy.applicable_seniority?.join(", ")}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <CheckCircle className="h-3 w-3" />
          <span>v{policy.version}</span>
        </div>
      </div>
    </div>
  )
}
