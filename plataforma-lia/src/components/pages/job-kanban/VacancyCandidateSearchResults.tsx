"use client"

import { useTranslations } from "next-intl"
import { X, Loader2, ThumbsUp, ThumbsDown, CheckSquare, Square, Users, Home, Zap, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { SearchResultsHeader } from "@/components/pages/candidates/SearchResultsHeader"
import type { ParsedEntities } from "@/components/search/smart-search-input"
import type { VacancySearchMode, AutoConfig } from "@/hooks/search/useVacancySearch"

interface VacancyCandidateSearchResultsProps {
  isOpen: boolean
  onClose: () => void
  vacancyTitle: string
  mode: VacancySearchMode
  autoConfig: AutoConfig
  isSearching: boolean
  searchProgress: number
  searchResults: Record<string, unknown>[]
  totalResults: number
  selectedIds: Set<string>
  searchFeedbacks: Record<string, "like" | "dislike">
  onToggleSelect: (id: string) => void
  onSelectAll: () => void
  onClearSelection: () => void
  onFeedback: (id: string, type: "like" | "dislike") => void
  onAddToVacancy: () => void
  onAddAuto: () => void
  onLoadMore: () => void
  onEditSearch: () => void
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  showAutoConfirm: boolean
  autoQualifyingPreview: Record<string, unknown>[]
  onConfirmAutoAdd: () => void
  onCancelAutoAdd: () => void
}

/* ------------------------------------------------------------------ */
/*  Progress bar sub-component                                         */
/* ------------------------------------------------------------------ */

function SearchProgressBar({ progress, searchSource }: { progress: number; searchSource: string }) {
  const sourceLabel =
    searchSource === "local"  ? { icon: <Home className="w-3.5 h-3.5" />,  text: "Base Local" } :
    searchSource === "hybrid" ? { icon: <Zap  className="w-3.5 h-3.5" />,  text: "Busca Híbrida" } :
                                { icon: <Globe className="w-3.5 h-3.5" />, text: "Base Global" }

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-5">
      <div className="text-center space-y-1.5">
        <p className="text-sm font-semibold text-lia-text-primary">Buscando candidatos...</p>
        <p className="text-xs text-lia-text-tertiary">Buscas na base global podem levar até 1 minuto</p>
      </div>

      {/* Animated progress bar */}
      <div className="w-80 max-w-full space-y-1.5">
        <div className="w-full h-2 bg-lia-bg-tertiary rounded-full overflow-hidden">
          <div
            className="h-full bg-wedo-cyan rounded-full transition-[width] duration-500 ease-out"
            style={{ width: `${Math.max(progress, 3)}%` }}
          />
        </div>
        <p className="text-xs text-lia-text-secondary text-center font-medium tabular-nums">
          {Math.round(progress)}%
        </p>
      </div>

      {/* Source indicator */}
      <div className="flex items-center gap-1.5 text-xs text-lia-text-tertiary">
        {sourceLabel.icon}
        <span>{sourceLabel.text}</span>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Auto-confirm overlay sub-component                                 */
/* ------------------------------------------------------------------ */

function AutoConfirmOverlay({
  preview,
  minScore,
  onConfirm,
  onCancel,
}: {
  preview: Record<string, unknown>[]
  minScore: number
  onConfirm: () => void
  onCancel: () => void
}) {
  const total = preview.length
  const top5 = preview.slice(0, 5)
  const remaining = total - top5.length

  return (
    <div className="flex-shrink-0 border-t border-lia-border-subtle bg-lia-bg-secondary px-4 py-4">
      <div className="max-w-2xl mx-auto space-y-3">
        {/* Title */}
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-status-success" />
          <p className="text-sm font-semibold text-lia-text-primary">
            {`Encontramos ${total} candidato${total !== 1 ? "s" : ""} com score ≥ ${minScore}`}
          </p>
        </div>

        {/* Preview list */}
        <div className="space-y-1.5">
          {top5.map((c, idx) => {
            const name = (c.name || c.full_name || "—") as string
            const score = Number(c.lia_score || c.score || c.match_percentage || 0)
            const company = (c.current_company || c.company || "") as string
            const scoreColor = score >= 80 ? "text-status-success" : score >= 60 ? "text-status-warning" : "text-lia-text-tertiary"
            return (
              <div key={String(c.id ?? idx)} className="flex items-center justify-between text-xs px-3 py-1.5 rounded-lg bg-lia-bg-primary border border-lia-border-subtle">
                <span className="font-medium text-lia-text-primary truncate max-w-[200px]">{name}</span>
                <div className="flex items-center gap-3">
                  {company && <span className="text-lia-text-tertiary truncate max-w-[140px]">{company}</span>}
                  <span className={`font-semibold tabular-nums ${scoreColor}`}>{Math.round(score)}</span>
                </div>
              </div>
            )
          })}
          {remaining > 0 && (
            <p className="text-xs text-lia-text-tertiary text-center">
              {`e mais ${remaining} candidato${remaining !== 1 ? "s" : ""}...`}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 pt-1">
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancelar
          </Button>
          <Button
            size="sm"
            onClick={onConfirm}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white gap-1.5"
          >
            {`Adicionar ${total} à vaga`}
          </Button>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export function VacancyCandidateSearchResults({
  isOpen, onClose, vacancyTitle, mode, autoConfig,
  isSearching, searchProgress, searchResults, totalResults,
  selectedIds, searchFeedbacks,
  onToggleSelect, onSelectAll, onClearSelection,
  onFeedback, onAddToVacancy, onAddAuto, onLoadMore, onEditSearch,
  lastSearchQuery, lastSearchEntities,
  showAutoConfirm, autoQualifyingPreview, onConfirmAutoAdd, onCancelAutoAdd,
}: VacancyCandidateSearchResultsProps) {
  const t = useTranslations("vacancySearch")

  if (!isOpen) return null

  const autoQualifying = mode === "auto"
    ? searchResults.filter(c => {
        const score = Number(c.lia_score || c.score || c.match_percentage || 0)
        return score >= autoConfig.minScore
      }).slice(0, autoConfig.maxCandidates)
    : []

  /* Detect dominant search source for the progress indicator */
  const dominantSource = (() => {
    if (searchResults.length === 0) return "global"
    const sources = searchResults.map(c => (c.source_type || c.source || "global") as string)
    const localCount = sources.filter(s => s === "local").length
    const globalCount = sources.filter(s => s === "global").length
    if (localCount > 0 && globalCount > 0) return "hybrid"
    return localCount > globalCount ? "local" : "global"
  })()

  return (
    <div className="fixed inset-0 z-50 bg-lia-bg-primary flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-lia-border-subtle">
        <div className="flex items-center justify-between px-4 py-3 gap-2">
          {/* SearchResultsHeader replaces the old back + title row */}
          <SearchResultsHeader
            lastSearchQuery={lastSearchQuery}
            lastSearchEntities={lastSearchEntities}
            onBack={onClose}
            onOpenEditQueryModal={(_q) => onEditSearch()}
            onOpenAdvancedSearch={onEditSearch}
          />

          <div className="flex items-center gap-2 flex-shrink-0">
            <Chip variant="neutral" muted className="text-micro px-2 py-0.5 whitespace-nowrap">{vacancyTitle}</Chip>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg border border-lia-border-subtle flex items-center justify-center text-lia-text-tertiary hover:bg-lia-bg-tertiary transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 pb-2">
          <div className="flex items-center gap-2">
            {mode === "manual" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={selectedIds.size === searchResults.length ? onClearSelection : onSelectAll}
                className="gap-1.5 text-xs"
              >
                {selectedIds.size === searchResults.length
                  ? <CheckSquare className="w-3.5 h-3.5" />
                  : <Square className="w-3.5 h-3.5" />
                }
                {selectedIds.size > 0
                  ? `${selectedIds.size} selecionados`
                  : "Selecionar Todos"
                }
              </Button>
            )}
            <span className="text-xs text-lia-text-tertiary">
              {t("resultsCount", { shown: searchResults.length, total: totalResults })}
            </span>
          </div>
          {isSearching && searchResults.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {t("analyzing", { done: searchResults.length, total: totalResults })}
            </div>
          )}
        </div>
      </div>

      {/* Loading state — progress bar */}
      {isSearching && searchResults.length === 0 && (
        <SearchProgressBar progress={searchProgress} searchSource={dominantSource} />
      )}

      {/* No results */}
      {!isSearching && searchResults.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <p className="text-sm font-medium text-lia-text-primary">{t("noResults")}</p>
          <p className="text-xs text-lia-text-tertiary">{t("noResultsDesc")}</p>
          <Button variant="outline" size="sm" onClick={onEditSearch}>{t("editFilters")}</Button>
        </div>
      )}

      {/* Results table */}
      {searchResults.length > 0 && (
        <div className="flex-1 overflow-auto">
          <table className="w-full text-xs">
            <thead className="bg-lia-bg-secondary sticky top-0 z-10">
              <tr className="border-b border-lia-border-subtle">
                {mode === "manual" && <th className="w-10 px-3 py-2" />}
                <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">FEEDBACK</th>
                <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">SCORE IA</th>
                <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">FONTE</th>
                <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">CANDIDATO</th>
                <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">CARGO ATUAL</th>
                <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">EMPRESA ATUAL</th>
              </tr>
            </thead>
            <tbody>
              {searchResults.map((c) => {
                const id = String(c.id)
                const score = Number(c.lia_score || c.score || c.match_percentage || 0)
                const name = (c.name || c.full_name || "—") as string
                const title = (c.current_title || c.title || "—") as string
                const company = (c.current_company || c.company || "—") as string
                const source = (c.source_type || c.source || "global") as string
                const feedback = searchFeedbacks[id]
                const isSelected = selectedIds.has(id)
                const scoreColor = score >= 80 ? "text-status-success" : score >= 60 ? "text-status-warning" : "text-lia-text-tertiary"
                const sourceIcon = source === "local" ? "🏠" : source === "hybrid" ? "⚡" : "🌐"

                return (
                  <tr
                    key={id}
                    className={`border-b border-lia-border-subtle hover:bg-lia-bg-secondary transition-colors ${
                      isSelected ? "bg-lia-bg-tertiary" : ""
                    } ${feedback === "dislike" ? "opacity-40" : ""}`}
                  >
                    {mode === "manual" && (
                      <td className="px-3 py-2">
                        <button onClick={() => onToggleSelect(id)} className="w-5 h-5 flex items-center justify-center">
                          {isSelected
                            ? <CheckSquare className="w-4 h-4 text-lia-text-primary" />
                            : <Square className="w-4 h-4 text-lia-text-tertiary" />
                          }
                        </button>
                      </td>
                    )}
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => onFeedback(id, "like")}
                          className={`w-6 h-6 rounded flex items-center justify-center transition-colors ${
                            feedback === "like" ? "bg-status-success/15 text-status-success" : "hover:bg-lia-bg-tertiary text-lia-text-tertiary"
                          }`}
                        >
                          <ThumbsUp className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => onFeedback(id, "dislike")}
                          className={`w-6 h-6 rounded flex items-center justify-center transition-colors ${
                            feedback === "dislike" ? "bg-status-error/15 text-status-error" : "hover:bg-lia-bg-tertiary text-lia-text-tertiary"
                          }`}
                        >
                          <ThumbsDown className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      {score > 0 ? (
                        <span className={`font-semibold ${scoreColor}`}>{Math.round(score)}</span>
                      ) : (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-lia-text-tertiary" />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <span title={source}>{sourceIcon}</span>
                    </td>
                    <td className="px-3 py-2 font-medium text-lia-text-primary max-w-[200px] truncate">{name}</td>
                    <td className="px-3 py-2 text-lia-text-secondary max-w-[200px] truncate">{title}</td>
                    <td className="px-3 py-2 text-lia-text-secondary max-w-[150px] truncate">{company}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {/* Load more */}
          {searchResults.length < totalResults && (
            <div className="flex justify-center py-4">
              <Button variant="outline" size="sm" onClick={onLoadMore} disabled={isSearching} className="gap-1.5">
                {isSearching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                {t("loadMore")}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Auto-confirm overlay — replaces the CTA bar when active */}
      {showAutoConfirm && mode === "auto" && autoQualifyingPreview.length > 0 ? (
        <AutoConfirmOverlay
          preview={autoQualifyingPreview}
          minScore={autoConfig.minScore}
          onConfirm={onConfirmAutoAdd}
          onCancel={onCancelAutoAdd}
        />
      ) : (
        /* Sticky CTA bar */
        searchResults.length > 0 && (
          <div className="flex-shrink-0 border-t border-lia-border-subtle px-4 py-3 flex items-center justify-between bg-lia-bg-primary">
            <span className="text-xs text-lia-text-tertiary">
              {t("resultsCount", { shown: searchResults.length, total: totalResults })}
            </span>

            {mode === "manual" && selectedIds.size > 0 && (
              <Button
                size="sm"
                onClick={onAddToVacancy}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white gap-1.5"
              >
                {t("addToVacancy", { count: selectedIds.size })}
              </Button>
            )}

            {mode === "auto" && !isSearching && (
              <Button
                size="sm"
                onClick={onAddAuto}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white gap-1.5"
              >
                {t("autoConfirmAdd", { count: autoQualifying.length })}
              </Button>
            )}
          </div>
        )
      )}
    </div>
  )
}
