"use client"

import { Plus, Sparkles, AlertCircle, CheckCircle } from "lucide-react"
import { CompensationPolicyItemCard } from "./CompensationPolicyItemCard"
import { CompensationPolicyFormModal } from "./CompensationPolicyFormModal"
import { useCompensationPoliciesTab } from "./useCompensationPoliciesTab"

export function CompensationPoliciesListSection() {
  const {
    policies,
    isLoading,
    isSaving,
    showModal,
    editingPolicy,
    successMessage,
    error,
    openCreate,
    openEdit,
    closeModal,
    savePolicy,
    deactivatePolicy,
    seedDefaults,
  } = useCompensationPoliciesTab()

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary">
            Políticas de Remuneração Variável
          </h3>
          <p className="text-xs text-lia-text-secondary mt-0.5">
            PLR, PPR, Bônus, Comissão e Equity — verbas tipadas por política
          </p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 rounded-lg bg-lia-btn-primary-bg px-3 py-1.5 text-xs font-medium text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
        >
          <Plus className="h-3.5 w-3.5" /> Nova política
        </button>
      </div>

      {/* Feedback */}
      {successMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-status-success/20 bg-status-success/10 px-3 py-2 text-sm text-status-success">
          <CheckCircle className="h-4 w-4 shrink-0" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-status-error/20 bg-status-error/10 px-3 py-2 text-sm text-status-error">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((n) => (
            <div key={n} className="h-24 rounded-lg bg-lia-bg-tertiary/20 animate-pulse" />
          ))}
        </div>
      ) : policies.length === 0 ? (
        <div className="rounded-xl border border-dashed border-lia-border-default bg-lia-bg-elevated p-6 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-wedo-cyan/40 mb-2" />
          <p className="text-sm font-medium text-lia-text-primary">
            Nenhuma política cadastrada ainda
          </p>
          <p className="text-xs text-lia-text-secondary mt-1 mb-4">
            Crie manualmente ou use os templates brasileiros padrão (PLR + Bônus Comercial).
          </p>
          <div className="flex justify-center gap-2">
            <button
              onClick={seedDefaults}
              disabled={isSaving}
              className="flex items-center gap-1.5 rounded-lg border border-wedo-cyan px-3 py-1.5 text-xs font-medium text-wedo-cyan hover:bg-wedo-cyan/10 disabled:opacity-60"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {isSaving ? "Criando..." : "Usar templates BR padrão"}
            </button>
            <button
              onClick={openCreate}
              className="flex items-center gap-1.5 rounded-lg bg-lia-btn-primary-bg px-3 py-1.5 text-xs font-medium text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
            >
              <Plus className="h-3.5 w-3.5" /> Criar do zero
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {policies.map((policy, idx) => (
            <CompensationPolicyItemCard
              key={policy.id ?? `policy-${idx}`}
              policy={policy}
              onEdit={openEdit}
              onDeactivate={deactivatePolicy}
            />
          ))}
        </div>
      )}

      {/* Modal */}
      <CompensationPolicyFormModal
        isOpen={showModal}
        initialData={editingPolicy}
        onClose={closeModal}
        onSave={savePolicy}
        isSaving={isSaving}
        error={error}
      />
    </div>
  )
}
