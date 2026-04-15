"use client"

import React from "react"
import {
  Building, Heart, Code, Gift, Network, GitBranch, BarChart3, FileText,
  Loader2, RefreshCw, AlertCircle, CheckCircle, Upload,
} from "lucide-react"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { textStyles } from "@/lib/design-tokens"
import type { LucideIcon } from "lucide-react"

const ICON_MAP: Record<string, LucideIcon> = {
  Building,
  Heart,
  Code,
  Gift,
  Network,
  GitBranch,
  BarChart3,
  FileText,
  Upload,
}

export function MinhaEmpresaHub() {
  const {
    blocks,
    loading,
    error,
    successMessage,
    overallProgress,
    expandedBlocks,
    recentlyUpdated,
    editingField,
    isSavingField,
    toggleBlock,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll,
  } = useCompanySettingsCards()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        <span className={`ml-2 ${textStyles.body}`}>
          Carregando dados da empresa...
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {(error || successMessage) && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
          error
            ? "bg-status-error/10 text-status-error border border-status-error/30"
            : "bg-status-success/10 text-status-success border border-status-success/30"
        }`}>
          {error ? <AlertCircle className="w-4 h-4 flex-shrink-0" /> : <CheckCircle className="w-4 h-4 flex-shrink-0" />}
          <span>{error || successMessage}</span>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className={textStyles.h3}>Minha Empresa</h2>
            <p className={`${textStyles.description} mt-0.5`}>
              Converse com a LIA no chat lateral para preencher automaticamente. Ou edite diretamente nos cards.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={refreshAll}
              className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              aria-label="Atualizar dados"
            >
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
            </button>
            <span className={`${textStyles.metricSmall} flex-shrink-0`}>
              {overallProgress}% configurado
            </span>
            {overallProgress >= 80 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30 flex-shrink-0">
                <CheckCircle className="w-3 h-3 mr-1" />
                Quase completo
              </span>
            )}
          </div>
        </div>
        <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full transition-[width] duration-500 bg-lia-btn-primary-bg"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {blocks.map((block) => (
          <MinhaEmpresaCard
            key={block.key}
            block={block}
            IconComp={ICON_MAP[block.iconName]}
            isExpanded={expandedBlocks.has(block.key)}
            recentlyUpdated={recentlyUpdated}
            editingField={editingField}
            isSavingField={isSavingField}
            onToggle={() => toggleBlock(block.key)}
            onStartEditing={startEditing}
            onCancelEditing={cancelEditing}
            onSaveField={saveField}
          />
        ))}
      </div>
    </div>
  )
}
