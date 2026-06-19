"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { Search, X, Sparkles, MousePointerClick } from "lucide-react"
import dynamic from "next/dynamic"
import type { SearchSource, SearchMode, SearchMetadata, ParsedEntities } from "@/components/search/smart-search-input"
import type { ModalPearchSearchOptions } from "@/components/pages/candidates/CandidatesPageModals.types"
import type { VacancySearchMode, AutoConfig } from "@/hooks/search/useVacancySearch"

const SmartSearchInput = dynamic(
  () => import("@/components/search/smart-search-input").then(m => ({ default: m.SmartSearchInput })).catch(() => {
    return import("@/components/search/smart-search-input").then(m => ({ default: m.default }))
  }),
  { ssr: false }
)

type CreditEstimate = {
  base_cost: number
  insights_cost: number
  freshness_cost: number
  cost_per_candidate: number
  total_estimated: number
  limit: number
  cost_level: "low" | "medium" | "high" | "very-high"
} | null

interface VacancySearchModalProps {
  isOpen: boolean
  onClose: () => void
  vacancyTitle: string
  enrichedJD: string
  searchSource: SearchSource
  onSearchSourceChange: (s: SearchSource) => void
  requireEmails: boolean
  onRequireEmailsChange: (v: boolean) => void
  requirePhoneNumbers: boolean
  onRequirePhoneNumbersChange: (v: boolean) => void
  mode: VacancySearchMode
  onModeChange: (m: VacancySearchMode) => void
  autoConfig: AutoConfig
  onAutoConfigChange: (c: AutoConfig) => void
  onSubmit: (query: string, entities: ParsedEntities, mode: SearchMode, metadata: SearchMetadata) => void
  creditEstimate: CreditEstimate
  initialQuery?: string
  initialJdContent?: string
}

const COST_LEVEL_COLORS: Record<string, string> = {
  low: "text-status-success",
  medium: "text-status-warning",
  high: "text-wedo-orange",
  "very-high": "text-status-error",
}

export function VacancySearchModal({
  isOpen, onClose, vacancyTitle, enrichedJD,
  searchSource, onSearchSourceChange,
  requireEmails, onRequireEmailsChange,
  requirePhoneNumbers, onRequirePhoneNumbersChange,
  mode, onModeChange,
  autoConfig, onAutoConfigChange,
  onSubmit,
  creditEstimate,
  initialQuery,
  initialJdContent,
}: VacancySearchModalProps) {
  const t = useTranslations("vacancySearch")
  const [value, setValue] = useState("")

  useEffect(() => {
    if (isOpen) setValue(initialQuery || "")
  }, [isOpen, initialQuery])

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose()
  }

  const pearchOptions: ModalPearchSearchOptions = {
    requireEmails,
    requirePhoneNumbers,
  }

  const renderCreditsFooter = () => {
    if (searchSource === "local") {
      return (
        <p className="text-xs text-status-success">
          {t("creditsLocal")}
        </p>
      )
    }

    if (!creditEstimate) {
      return (
        <p className="text-xs text-lia-text-tertiary animate-pulse">
          Calculando créditos...
        </p>
      )
    }

    const colorClass = COST_LEVEL_COLORS[creditEstimate.cost_level] || "text-lia-text-tertiary"

    return (
      <div className="flex items-center justify-between">
        <p className="text-xs text-lia-text-tertiary">
          {"Custo estimado: "}
          <span className={`font-semibold ${colorClass}`}>
            {creditEstimate.total_estimated} créditos
          </span>
          <span className="text-lia-text-quaternary ml-1">
            ({creditEstimate.cost_per_candidate} por candidato)
          </span>
        </p>
        {creditEstimate.cost_level === "very-high" && (
          <span className="text-[10px] text-status-error font-medium">
            Custo elevado
          </span>
        )}
      </div>
    )
  }

  return (
    <div
      data-testid="vacancy-search-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 p-6 pb-3 flex items-start justify-between">
          <div>
            <h2 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <Search className="w-4 h-4 text-lia-text-secondary" />
              {t("title")}
            </h2>
            <p className="text-xs text-lia-text-tertiary mt-1">{t("subtitle")}</p>
            <span className="inline-flex items-center gap-1.5 mt-2 bg-lia-bg-tertiary border border-lia-border-subtle rounded-full px-3 py-1 text-xs text-lia-text-secondary">
              📋 {vacancyTitle}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg border border-lia-border-subtle flex items-center justify-center text-lia-text-tertiary hover:bg-lia-bg-tertiary transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Mode selector */}
        <div className="px-6 pb-3 flex gap-2">
          <button
            onClick={() => onModeChange("manual")}
            className={`flex-1 flex items-center gap-3 p-3 rounded-xl border-2 transition-colors ${
              mode === "manual"
                ? "border-lia-text-primary bg-lia-bg-secondary"
                : "border-lia-border-subtle hover:border-lia-border-default"
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              mode === "manual" ? "bg-lia-btn-primary-bg text-white" : "bg-lia-bg-tertiary text-lia-text-tertiary"
            }`}>
              <MousePointerClick className="w-4 h-4" />
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-lia-text-primary">{t("modeManual")}</div>
              <div className="text-[10px] text-lia-text-tertiary">{t("modeManualDesc")}</div>
            </div>
          </button>
          <button
            onClick={() => onModeChange("auto")}
            className={`flex-1 flex items-center gap-3 p-3 rounded-xl border-2 transition-colors ${
              mode === "auto"
                ? "border-lia-text-primary bg-lia-bg-secondary"
                : "border-lia-border-subtle hover:border-lia-border-default"
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              mode === "auto" ? "bg-lia-btn-primary-bg text-white" : "bg-lia-bg-tertiary text-lia-text-tertiary"
            }`}>
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5">
                {t("modeAuto")}
                <span className="text-[9px] font-medium bg-status-success/15 text-status-success px-1.5 py-0.5 rounded-full">
                  {t("modeAutoRecommended")}
                </span>
              </div>
              <div className="text-[10px] text-lia-text-tertiary">{t("modeAutoDesc")}</div>
            </div>
          </button>
        </div>

        {/* SmartSearchInput */}
        <div className="flex-1 px-6 pb-3 overflow-auto">
          <SmartSearchInput
            value={value}
            onChange={setValue}
            onSubmit={(query: string, entities: ParsedEntities, sMode?: SearchMode, metadata?: SearchMetadata) => {
              if (query.trim()) {
                onSubmit(query.trim(), entities, sMode || "natural", metadata || { mode: "natural" })
              }
            }}
            onCancel={onClose}
            placeholder="Ex: desenvolvedor python com 5 anos de experiência em machine learning"
            searchSource={searchSource}
            onSearchSourceChange={onSearchSourceChange}
            requireEmails={requireEmails}
            onRequireEmailsChange={onRequireEmailsChange}
            requirePhoneNumbers={requirePhoneNumbers}
            onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
            initialJdContent={initialJdContent}
          />
        </div>

        {/* Auto config fields */}
        {mode === "auto" && (
          <div className="px-6 pb-3">
            <div className="border-t border-lia-border-subtle pt-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-lia-text-primary">{t("maxCandidates")}</label>
                  <div className="mt-1 flex items-center gap-2 border border-lia-border-subtle rounded-lg px-3 py-2">
                    <span className="text-sm">👥</span>
                    <input
                      type="number"
                      min={1}
                      max={30}
                      value={autoConfig.maxCandidates}
                      onChange={(e) => onAutoConfigChange({ ...autoConfig, maxCandidates: Math.min(30, Math.max(1, Number(e.target.value) || 1)) })}
                      className="w-16 bg-transparent text-sm font-semibold text-lia-text-primary outline-none"
                    />
                  </div>
                  <p className="text-[10px] text-lia-text-tertiary mt-1">{t("maxCandidatesHint")}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-lia-text-primary">{t("minScore")}</label>
                  <div className="mt-1 flex items-center gap-2 border border-lia-border-subtle rounded-lg px-3 py-2">
                    <span className="text-sm">🎯</span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={autoConfig.minScore}
                      onChange={(e) => onAutoConfigChange({ ...autoConfig, minScore: Math.min(100, Math.max(0, Number(e.target.value) || 0)) })}
                      className="w-16 bg-transparent text-sm font-semibold text-lia-text-primary outline-none"
                    />
                  </div>
                  <p className="text-[10px] text-lia-text-tertiary mt-1">{t("minScoreHint")}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer: credits */}
        <div className="flex-shrink-0 border-t border-lia-border-subtle px-6 py-3">
          {renderCreditsFooter()}
        </div>
      </div>
    </div>
  )
}
