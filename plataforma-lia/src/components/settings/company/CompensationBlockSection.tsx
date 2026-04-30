"use client"

import { useState, useEffect } from "react"
import { TrendingUp, ChevronRight, Plus, AlertCircle } from "lucide-react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { apiFetch } from "@/lib/api/api-fetch"
import type { CompensationPolicyRecord } from "@/components/settings/compensation-policies/compensation-policies-types"
import { VARIABLE_KIND_OPTIONS } from "@/components/settings/compensation-policies/compensation-policies-types"

interface Props {
  onNavigate?: () => void
}

export function CompensationBlockSection({ onNavigate }: Props) {
  const { companyId } = useCompanyId()
  const [policies, setPolicies] = useState<CompensationPolicyRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!companyId) return
    setIsLoading(true)
    apiFetch(
      `/api/backend-proxy/company/compensation-policies?company_id=${companyId}&active_only=true`
    )
      .then((data) => {
        setPolicies(Array.isArray(data) ? (data as CompensationPolicyRecord[]) : [])
      })
      .catch(() => setError("Erro ao carregar políticas"))
      .finally(() => setIsLoading(false))
  }, [companyId])

  const activePolicies = policies.filter((p) => p.is_active)
  const defaultPolicy = activePolicies.find((p) => p.is_default)

  // Summary of all variable comp kinds across active policies
  const allKinds = new Set(
    activePolicies.flatMap((p) => p.variable_compensation?.items?.map((i) => i.kind) ?? [])
  )
  const kindLabels = VARIABLE_KIND_OPTIONS.filter((k) => allKinds.has(k.id as typeof k.id)).map(
    (k) => k.label
  )

  return (
    <div className="rounded-xl border border-lia-border bg-lia-surface p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-lia-primary/10">
            <TrendingUp className="h-4 w-4 text-lia-primary" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-lia-text-primary">Remuneração Variável</h4>
            <p className="text-xs text-lia-text-secondary">Políticas PRV da empresa</p>
          </div>
        </div>
        {onNavigate && (
          <button
            onClick={onNavigate}
            className="flex items-center gap-1 text-xs text-lia-primary hover:underline"
          >
            Gerenciar <ChevronRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((n) => (
            <div key={n} className="h-6 rounded bg-lia-muted/20 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-xs text-red-500">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      ) : activePolicies.length === 0 ? (
        <div className="text-center py-3">
          <p className="text-xs text-lia-text-secondary mb-2">
            Nenhuma política de remuneração variável cadastrada.
          </p>
          {onNavigate && (
            <button
              onClick={onNavigate}
              className="flex items-center gap-1.5 mx-auto text-xs text-lia-primary hover:underline"
            >
              <Plus className="h-3.5 w-3.5" /> Criar política
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {/* Summary stats */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="rounded-lg bg-lia-bg-primary/60 px-3 py-2">
              <div className="text-lg font-semibold text-lia-text-primary">{activePolicies.length}</div>
              <div className="text-xs text-lia-text-secondary">
                {activePolicies.length === 1 ? "política ativa" : "políticas ativas"}
              </div>
            </div>
            <div className="rounded-lg bg-lia-bg-primary/60 px-3 py-2">
              <div className="text-lg font-semibold text-lia-text-primary">{allKinds.size}</div>
              <div className="text-xs text-lia-text-secondary">tipos de verba</div>
            </div>
          </div>

          {/* Verbas ativas */}
          {kindLabels.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {kindLabels.map((label) => (
                <span
                  key={label}
                  className="rounded-full bg-lia-primary/10 px-2 py-0.5 text-xs text-lia-primary"
                >
                  {label}
                </span>
              ))}
            </div>
          )}

          {/* Política padrão */}
          {defaultPolicy && (
            <div className="mt-2 rounded-lg border border-lia-border bg-lia-bg-primary/60 px-3 py-2">
              <div className="text-xs text-lia-text-secondary">Política padrão</div>
              <div className="text-sm font-medium text-lia-text-primary">{defaultPolicy.name}</div>
              {defaultPolicy.applicable_seniority.length > 0 && (
                <div className="text-xs text-lia-text-secondary mt-0.5">
                  {defaultPolicy.applicable_seniority.join(" · ")}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
