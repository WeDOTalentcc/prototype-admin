"use client"

import React from "react"
import {
  Building, Heart, Code, Gift, Network, GitBranch, BarChart3, FileText,
  Loader2, RefreshCw, AlertCircle, CheckCircle, Upload,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { useSettingsConversational } from "@/hooks/settings/use-settings-conversational"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { LearningLoopsPanel } from "@/components/settings/LearningLoopsPanel"
import { LiaFieldsConfigPanel } from "@/components/settings/LiaFieldsConfigPanel"
import { AnalyzeWebsiteModal } from "@/components/settings/AnalyzeWebsiteModal"
import { textStyles } from "@/lib/design-tokens"
import { Globe } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

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

interface MinhaEmpresaHubProps {
  activeSubsection?: string
}

export function MinhaEmpresaHub({ activeSubsection }: MinhaEmpresaHubProps = {}) {
  // Subsection routing — quando activeSubsection é 'learning-loops', renderiza
  // o painel canonical de Learning Loops (Sprint B Phase 2). Caso contrário,
  // segue o fluxo padrão de cards de Minha Empresa.
  if (activeSubsection === "learning-loops") {
    return <LearningLoopsPanel />
  }

  // Audit 2026-05-20 Tema D / P1.8: 34 canonical LIA field definitions
  // mas UI só expunha 3. Painel canonical novo expõe todos.
  if (activeSubsection === "instrucoes-lia") {
    return <LiaFieldsConfigPanel />
  }

  const t = useTranslations("settings.minhaEmpresa")
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

  const { triggerAction, triggerPrefillSection } = useSettingsConversational()

  const BLOCK_TO_PREFILL: Record<string, "basic" | "culture" | "tech_stack" | "benefits" | "workforce" | "policy" | "compensation" | undefined> = {
    basic: "basic",
    culture: "culture",
    tech: "tech_stack",
    benefits: "benefits",
    workforce: "workforce",
    policy: "policy",
    documents: "compensation",
  }

  const pendingSections = React.useMemo(
    () => blocks.filter((b) => b.progress.total > 0 && b.progress.filled < b.progress.total),
    [blocks],
  )
  const totalPendingFields = React.useMemo(
    () => pendingSections.reduce((acc, b) => acc + (b.progress.total - b.progress.filled), 0),
    [pendingSections],
  )

  const handleJumpToBlock = React.useCallback((blockKey: string) => {
    if (typeof window === "undefined") return
    if (!expandedBlocks.has(blockKey)) toggleBlock(blockKey)
    setTimeout(() => {
      const target = document.querySelector(
        `[data-block-anchor="${blockKey}"]`,
      ) as HTMLElement | null
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" })
    }, 60)
  }, [expandedBlocks, toggleBlock])

  const basicBlock = React.useMemo(
    () => blocks.find((b) => b.key === "basic"),
    [blocks],
  )
  const getBasicField = React.useCallback(
    (key: string) =>
      basicBlock?.fields.find((f) => f.key === key)?.value as string | undefined,
    [basicBlock],
  )
  const websiteUrl = getBasicField("website")

  // Task #1180 — botão "Analisar nosso site" agora abre o modal pré-análise
  // (nome + website + linkedin + checkbox "atualizar existentes"), em vez de
  // disparar um prompt para o chat. Mantemos `triggerAction(analyze_website)`
  // como notificação ao onboarding orchestrator quando o modal aplica o save.
  const [analyzeModalOpen, setAnalyzeModalOpen] = React.useState(false)
  const handleAnalyzeWebsite = React.useCallback(() => {
    setAnalyzeModalOpen(true)
  }, [])

  const handleAnalyzeApplied = React.useCallback(() => {
    // Dispatch para o OnboardingActionOrchestrator marcar o step como done.
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("lia:settings-success", { detail: { actionId: "analyze_website" } }),
      )
    }
    refreshAll()
  }, [refreshAll])

  const existingBasic = React.useMemo(
    () => ({
      industry: getBasicField("industry"),
      employee_count: getBasicField("employee_count"),
      company_size: getBasicField("company_size"),
      headquarters_city: getBasicField("headquarters_city"),
      headquarters_state: getBasicField("headquarters_state"),
      founded_year: getBasicField("founded_year"),
      work_model: getBasicField("work_model"),
      linkedin_url: getBasicField("linkedin_url"),
      logo_url: getBasicField("logo_url"),
    }),
    [getBasicField],
  )
  const companyName = getBasicField("name") ?? ""

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-label={t("loading")}>
        <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        <span className={`ml-2 ${textStyles.body}`}>
          {t("loadingCompanyData")}
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
            <h2 className={textStyles.h3}>{t("title")}</h2>
            <p className={`${textStyles.description} mt-0.5`}>
              {t("description")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAnalyzeWebsite}
              data-testid="analyze-website-cta"
              title={t("analyzeWebsiteTitle")}
              className="[&_svg]:size-3.5"
            >
              <Globe className="text-wedo-cyan" aria-hidden />
              {t("analyzeWebsite")}
            </Button>
            <button
              onClick={refreshAll}
              className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              aria-label={t("refreshData")}
            >
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
            </button>
            <span className={`${textStyles.metricSmall} flex-shrink-0`}>
              {t("configuredSuffix", { progress: overallProgress })}
            </span>
            {overallProgress >= 80 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30 flex-shrink-0">
                <CheckCircle className="w-3 h-3 mr-1" />
                {t("almostComplete")}
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

      {totalPendingFields > 0 && (
        <div
          className="rounded-lg border border-lia-border-subtle bg-lia-bg-secondary/60 dark:bg-lia-bg-elevated px-3 py-2.5"
          data-testid="profile-progress-panel"
        >
          <div className="flex items-center justify-between mb-1.5">
            <p className={`${textStyles.captionBold} text-lia-text-primary`}>
              {t("profileCompletePending", { progress: overallProgress, count: totalPendingFields })}
            </p>
            <span className="text-micro text-lia-text-tertiary">
              {t("sectionsToReview", { count: pendingSections.length })}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {pendingSections.map((b) => {
              const remaining = b.progress.total - b.progress.filled
              const prefillKey = BLOCK_TO_PREFILL[b.key]
              return (
                <span key={b.key} className="inline-flex items-center gap-0.5">
                  <button
                    type="button"
                    onClick={() => handleJumpToBlock(b.key)}
                    data-testid={`pending-section-${b.key}`}
                    className="
                      inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium
                      bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle
                      text-lia-text-primary hover:border-lia-border-medium hover:bg-lia-bg-secondary
                      transition-colors motion-reduce:transition-none
                    "
                  >
                    {b.title}
                    <span className="text-lia-text-tertiary">({remaining})</span>
                  </button>
                  {prefillKey && (
                    <button
                      type="button"
                      onClick={() => triggerPrefillSection(prefillKey, b.progress.missingLabels)}
                      data-testid={`pending-prefill-${b.key}`}
                      className="
                        inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium
                        bg-lia-btn-primary-bg/10 text-lia-btn-primary-bg border border-lia-btn-primary-bg/30
                        hover:bg-lia-btn-primary-bg/20 transition-colors motion-reduce:transition-none
                      "
                      title={t("askLiaToFillTitle", { section: b.title })}
                    >
                      {t("askLiaShort")}
                    </button>
                  )}
                </span>
              )
            })}
          </div>
        </div>
      )}

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
            onLogoUploaded={refreshAll}
            onToggle={() => toggleBlock(block.key)}
            onStartEditing={startEditing}
            onCancelEditing={cancelEditing}
            onSaveField={saveField}
          />
        ))}
      </div>

      <AnalyzeWebsiteModal
        open={analyzeModalOpen}
        onClose={() => setAnalyzeModalOpen(false)}
        initial={{
          companyName,
          websiteUrl,
          linkedinUrl: existingBasic.linkedin_url,
          companyId: companyId ?? undefined,
          existingBasic,
        }}
        onApplied={handleAnalyzeApplied}
      />
    </div>
  )
}
