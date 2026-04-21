"use client"

import React from "react"
import {
  Building, Heart, Code, Gift, Network, GitBranch, BarChart3, FileText,
  Loader2, RefreshCw, AlertCircle, CheckCircle, Upload, ArrowRight,
} from "lucide-react"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { useSettingsConversational } from "@/hooks/settings/use-settings-conversational"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { textStyles } from "@/lib/design-tokens"
import { Globe } from "lucide-react"
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
    benefits,
    companyId,
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

  const { triggerAction } = useSettingsConversational()

  const handleOpenDepartments = React.useCallback(() => {
    if (typeof window === "undefined") return
    try {
      sessionStorage.setItem(
        "settings-pending-subtab",
        JSON.stringify({ section: "usuarios-departamentos", tab: "departments" }),
      )
    } catch { /* sessionStorage pode estar indisponivel */ }
    window.dispatchEvent(new CustomEvent("settings-open-subtab", { detail: { section: "usuarios-departamentos", tab: "departments" } }))
    window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "usuarios-departamentos" }))
  }, [])

  const handleAnalyzeWebsite = React.useCallback(() => {
    triggerAction("analyze_website", {
      section: "minha-empresa",
      prompt:
        "Analise nosso site institucional e extraia missão, valores, cultura, " +
        "tech stack e benefícios. Mostre os campos extraídos para eu revisar antes de gravar.",
      source: "ui",
    })
  }, [triggerAction])

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
              type="button"
              onClick={handleAnalyzeWebsite}
              data-testid="analyze-website-cta"
              className="
                inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                bg-lia-bg-secondary dark:bg-lia-bg-elevated
                text-lia-text-primary border border-lia-border-subtle
                hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none
              "
              title="Pedir para a LIA analisar nosso site"
            >
              <Globe className="w-3.5 h-3.5 text-wedo-cyan" aria-hidden />
              Analisar nosso site
            </button>
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

      <div className="flex items-center justify-between rounded-lg border border-lia-border-subtle bg-lia-bg-secondary/50 dark:bg-lia-bg-elevated px-3 py-2">
        <div className="flex items-center gap-2 min-w-0">
          <Network className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" aria-hidden />
          <div className="min-w-0">
            <p className={`${textStyles.description} truncate`}>
              Departamentos são gerenciados em Usuários & Departamentos.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleOpenDepartments}
          data-testid="open-departments-shortcut"
          className="inline-flex items-center gap-1 text-sm font-medium text-wedo-cyan hover:underline focus:outline-none focus:ring-1 focus:ring-lia-border-medium rounded-md px-1.5 py-0.5"
        >
          Gerenciar departamentos
          <ArrowRight className="w-3.5 h-3.5" aria-hidden />
        </button>
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
            benefits={benefits}
            companyId={companyId}
            onBenefitsChanged={refreshAll}
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
