"use client"

import React, { useState, useRef, useCallback, useEffect, Suspense } from "react"
import { useTranslations } from "next-intl"
import {
  X, Loader2, ThumbsUp, ThumbsDown, CheckSquare, Square, Users,
  Home, Zap, Globe, Mail, Phone, ArrowUpDown, ChevronUp, ChevronDown,
  Settings2, Eye, EyeOff,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { SearchResultsHeader } from "@/components/pages/candidates/SearchResultsHeader"
import type { ParsedEntities } from "@/components/search/smart-search-input"
import type { VacancySearchMode, AutoConfig, RevealedContacts } from "@/hooks/search/useVacancySearch"
import { isGlobalSource } from "@/lib/utils/source-detection"

const CandidatePreviewLazy = React.lazy(() =>
  import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })))

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type SortColumn = "score" | "name" | "title" | "company" | null
type SortDirection = "asc" | "desc"

interface ColumnDef {
  key: string
  label: string
  visible: boolean
  sortable: boolean
}

const DEFAULT_COLUMNS: ColumnDef[] = [
  { key: "checkbox", label: "", visible: true, sortable: false },
  { key: "feedback", label: "FEEDBACK", visible: true, sortable: false },
  { key: "score", label: "SCORE IA", visible: true, sortable: true },
  { key: "source", label: "FONTE", visible: true, sortable: false },
  { key: "name", label: "CANDIDATO", visible: true, sortable: true },
  { key: "title", label: "CARGO ATUAL", visible: true, sortable: true },
  { key: "company", label: "EMPRESA ATUAL", visible: true, sortable: true },
  { key: "email", label: "EMAIL", visible: true, sortable: false },
  { key: "phone", label: "TELEFONE", visible: true, sortable: false },
]

interface VacancyCandidateSearchResultsProps {
  isOpen: boolean
  onClose: () => void
  vacancyId: string
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
  revealedContacts: RevealedContacts
  isRevealing: boolean
  onRevealContact: (candidateId: string, candidateName: string, type: "email" | "phone", linkedinUrl?: string) => void
}

/* ------------------------------------------------------------------ */
/*  Progress bar                                                       */
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
      <div className="w-80 max-w-full space-y-1.5">
        <div className="w-full h-2 bg-lia-bg-tertiary rounded-full overflow-hidden">
          <div className="h-full bg-wedo-cyan rounded-full transition-[width] duration-500 ease-out" style={{ width: `${Math.max(progress, 3)}%` }} />
        </div>
        <p className="text-xs text-lia-text-secondary text-center font-medium tabular-nums">{Math.round(progress)}%</p>
      </div>
      <div className="flex items-center gap-1.5 text-xs text-lia-text-tertiary">
        {sourceLabel.icon}
        <span>{sourceLabel.text}</span>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Auto-confirm overlay                                               */
/* ------------------------------------------------------------------ */

function AutoConfirmOverlay({ preview, minScore, onConfirm, onCancel }: {
  preview: Record<string, unknown>[]; minScore: number; onConfirm: () => void; onCancel: () => void
}) {
  const total = preview.length
  const top5 = preview.slice(0, 5)
  const remaining = total - top5.length
  return (
    <div className="flex-shrink-0 border-t border-lia-border-subtle bg-lia-bg-secondary px-4 py-4">
      <div className="max-w-2xl mx-auto space-y-3">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-status-success" />
          <p className="text-sm font-semibold text-lia-text-primary">
            {`Encontramos ${total} candidato${total !== 1 ? "s" : ""} com score ≥ ${minScore}`}
          </p>
        </div>
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
          {remaining > 0 && <p className="text-xs text-lia-text-tertiary text-center">{`e mais ${remaining} candidato${remaining !== 1 ? "s" : ""}...`}</p>}
        </div>
        <div className="flex items-center justify-end gap-2 pt-1">
          <Button variant="outline" size="sm" onClick={onCancel}>Cancelar</Button>
          <Button size="sm" onClick={onConfirm} className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white gap-1.5">
            {`Adicionar ${total} à vaga`}
          </Button>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Column config dropdown                                             */
/* ------------------------------------------------------------------ */

function ColumnConfigDropdown({ columns, onToggle }: { columns: ColumnDef[]; onToggle: (key: string) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const toggleable = columns.filter(c => c.key !== "checkbox" && c.key !== "name")
  const visibleCount = toggleable.filter(c => c.visible).length

  return (
    <div ref={ref} className="relative">
      <Button variant="ghost" size="sm" onClick={() => setOpen(p => !p)} className="gap-1.5 text-xs">
        <Settings2 className="w-3.5 h-3.5" />
        {`Colunas ${visibleCount}`}
      </Button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lg z-50 py-1">
          {toggleable.map(col => (
            <button
              key={col.key}
              onClick={() => onToggle(col.key)}
              className="w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-lia-bg-secondary transition-colors"
            >
              {col.visible ? <Eye className="w-3.5 h-3.5 text-lia-text-primary" /> : <EyeOff className="w-3.5 h-3.5 text-lia-text-tertiary" />}
              <span className={col.visible ? "text-lia-text-primary" : "text-lia-text-tertiary"}>{col.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Sortable column header                                             */
/* ------------------------------------------------------------------ */

function SortableHeader({ label, columnKey, sortColumn, sortDirection, onSort }: {
  label: string; columnKey: SortColumn; sortColumn: SortColumn; sortDirection: SortDirection; onSort: (col: SortColumn) => void
}) {
  const isActive = sortColumn === columnKey
  return (
    <th
      className="px-3 py-2 text-left font-medium text-lia-text-secondary cursor-pointer select-none hover:text-lia-text-primary transition-colors group"
      onClick={() => onSort(columnKey)}
    >
      <div className="flex items-center gap-1">
        <span>{label}</span>
        {isActive ? (
          sortDirection === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
        ) : (
          <ArrowUpDown className="w-3 h-3 opacity-0 group-hover:opacity-40 transition-opacity" />
        )}
      </div>
    </th>
  )
}

/* ------------------------------------------------------------------ */
/*  Preview panel                                                      */
/* ------------------------------------------------------------------ */

const PANEL_MIN = 380
const PANEL_MAX = 700
const PANEL_DEFAULT = 480

function PreviewPanel({ candidate, candidates, currentIndex, vacancyId, isMaximized, onClose, onToggleMaximize, onNavigate, panelWidth, onResizeStart }: {
  candidate: Record<string, unknown>
  candidates: Record<string, unknown>[]
  currentIndex: number
  vacancyId: string
  isMaximized: boolean
  onClose: () => void
  onToggleMaximize: () => void
  onNavigate: (idx: number) => void
  panelWidth: number
  onResizeStart: (e: React.MouseEvent) => void
}) {
  return (
    <div className="flex-shrink-0 h-full flex border-l border-lia-border-subtle" style={{ width: isMaximized ? PANEL_MAX : panelWidth }}>
      <div
        className="w-1.5 flex-shrink-0 cursor-col-resize group flex items-center justify-center hover:bg-lia-border-medium/40 transition-colors rounded-l-md"
        onMouseDown={onResizeStart}
        title="Arraste para redimensionar"
      >
        <div className="w-0.5 h-8 rounded-full bg-lia-border-medium group-hover:bg-lia-text-disabled transition-colors" />
      </div>
      <div className="flex-1 bg-lia-bg-primary rounded-xl overflow-hidden">
        <Suspense fallback={<div className="flex items-center justify-center h-full"><Loader2 className="w-5 h-5 animate-spin text-lia-text-tertiary" /></div>}>
          <CandidatePreviewLazy
            candidate={candidate}
            isOpen={true}
            onClose={onClose}
            isMaximized={isMaximized}
            onToggleMaximize={onToggleMaximize}
            candidates={candidates}
            currentIndex={currentIndex}
            onNavigateCandidate={onNavigate}
            jobId={vacancyId}
          />
        </Suspense>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Sorting helper                                                     */
/* ------------------------------------------------------------------ */

function extractSortValue(c: Record<string, unknown>, col: SortColumn): string | number {
  switch (col) {
    case "score": return Number(c.lia_score || c.score || c.match_percentage || 0)
    case "name": return ((c.name || c.full_name || "") as string).toLowerCase()
    case "title": return ((c.current_title || c.title || "") as string).toLowerCase()
    case "company": return ((c.current_company || c.company || "") as string).toLowerCase()
    default: return 0
  }
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export function VacancyCandidateSearchResults({
  isOpen, onClose, vacancyId, vacancyTitle, mode, autoConfig,
  isSearching, searchProgress, searchResults, totalResults,
  selectedIds, searchFeedbacks,
  onToggleSelect, onSelectAll, onClearSelection,
  onFeedback, onAddToVacancy, onAddAuto, onLoadMore, onEditSearch,
  lastSearchQuery, lastSearchEntities,
  showAutoConfirm, autoQualifyingPreview, onConfirmAutoAdd, onCancelAutoAdd,
  revealedContacts, isRevealing, onRevealContact,
}: VacancyCandidateSearchResultsProps) {
  const t = useTranslations("vacancySearch")

  // ---- preview state ----
  const [previewCandidate, setPreviewCandidate] = useState<Record<string, unknown> | null>(null)
  const [isPreviewMaximized, setIsPreviewMaximized] = useState(false)
  const [panelWidth, setPanelWidth] = useState(PANEL_DEFAULT)
  const isDragging = useRef(false)
  const dragStartX = useRef(0)
  const dragStartWidth = useRef(0)

  const onResizeStart = useCallback((e: React.MouseEvent) => {
    isDragging.current = true
    dragStartX.current = e.clientX
    dragStartWidth.current = panelWidth
    document.body.style.cursor = "col-resize"
    e.preventDefault()
  }, [panelWidth])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const delta = dragStartX.current - e.clientX
      setPanelWidth(Math.min(PANEL_MAX, Math.max(PANEL_MIN, dragStartWidth.current + delta)))
    }
    const onMouseUp = () => { if (isDragging.current) { isDragging.current = false; document.body.style.cursor = "" } }
    document.addEventListener("mousemove", onMouseMove)
    document.addEventListener("mouseup", onMouseUp)
    return () => { document.removeEventListener("mousemove", onMouseMove); document.removeEventListener("mouseup", onMouseUp) }
  }, [])

  const handleRowClick = useCallback((candidate: Record<string, unknown>) => {
    setPreviewCandidate(prev => prev && String(prev.id) === String(candidate.id) ? null : candidate)
  }, [])

  const handleNavigatePreview = useCallback((index: number) => {
    if (searchResults[index]) setPreviewCandidate(searchResults[index])
  }, [searchResults])

  const previewIndex = previewCandidate ? searchResults.findIndex(c => String(c.id) === String(previewCandidate.id)) : -1

  // ---- sort state ----
  const [sortColumn, setSortColumn] = useState<SortColumn>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc")

  const handleSort = useCallback((col: SortColumn) => {
    if (sortColumn === col) {
      setSortDirection(d => d === "asc" ? "desc" : "asc")
    } else {
      setSortColumn(col)
      setSortDirection(col === "score" ? "desc" : "asc")
    }
  }, [sortColumn])

  const sortedResults = React.useMemo(() => {
    if (!sortColumn) return searchResults
    const sorted = [...searchResults].sort((a, b) => {
      const va = extractSortValue(a, sortColumn)
      const vb = extractSortValue(b, sortColumn)
      if (typeof va === "number" && typeof vb === "number") return va - vb
      return String(va).localeCompare(String(vb))
    })
    return sortDirection === "desc" ? sorted.reverse() : sorted
  }, [searchResults, sortColumn, sortDirection])

  // ---- column config ----
  const [columns, setColumns] = useState<ColumnDef[]>(DEFAULT_COLUMNS)

  const toggleColumn = useCallback((key: string) => {
    setColumns(prev => prev.map(c => c.key === key ? { ...c, visible: !c.visible } : c))
  }, [])

  const isVisible = useCallback((key: string) => columns.find(c => c.key === key)?.visible ?? true, [columns])

  // ---- reset preview when results change ----
  useEffect(() => { setPreviewCandidate(null) }, [searchResults])

  if (!isOpen) return null

  const autoQualifying = mode === "auto"
    ? searchResults.filter(c => Number(c.lia_score || c.score || c.match_percentage || 0) >= autoConfig.minScore).slice(0, autoConfig.maxCandidates)
    : []

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
          <SearchResultsHeader
            lastSearchQuery={lastSearchQuery}
            lastSearchEntities={lastSearchEntities}
            onBack={onClose}
            onOpenEditQueryModal={(_q) => onEditSearch()}
            onOpenAdvancedSearch={onEditSearch}
          />
          <div className="flex items-center gap-2 flex-shrink-0">
            <Chip variant="neutral" muted className="text-micro px-2 py-0.5 whitespace-nowrap">{vacancyTitle}</Chip>
            <button onClick={onClose} className="w-8 h-8 rounded-lg border border-lia-border-subtle flex items-center justify-center text-lia-text-tertiary hover:bg-lia-bg-tertiary transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 pb-2">
          <div className="flex items-center gap-2">
            {mode === "manual" && (
              <Button variant="ghost" size="sm" onClick={selectedIds.size === searchResults.length ? onClearSelection : onSelectAll} className="gap-1.5 text-xs">
                {selectedIds.size === searchResults.length ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
                {selectedIds.size > 0 ? `${selectedIds.size} selecionados` : "Selecionar Todos"}
              </Button>
            )}
            <span className="text-xs text-lia-text-tertiary">{t("resultsCount", { shown: searchResults.length, total: totalResults })}</span>
          </div>
          <div className="flex items-center gap-1">
            {isSearching && searchResults.length > 0 && (
              <div className="flex items-center gap-2 text-xs text-lia-text-secondary mr-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {dominantSource === "local"
                  ? <span className="flex items-center gap-1"><Globe className="w-3 h-3" />Buscando na base global...</span>
                  : t("analyzing", { done: searchResults.length, total: totalResults })}
              </div>
            )}
            <ColumnConfigDropdown columns={columns} onToggle={toggleColumn} />
          </div>
        </div>
      </div>

      {/* Loading state */}
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

      {/* Results: table + preview panel */}
      {searchResults.length > 0 && (
        <div className="flex-1 flex overflow-hidden">
          {/* Table */}
          <div className="flex-1 overflow-auto">
            <table className="w-full text-xs">
              <thead className="bg-lia-bg-secondary sticky top-0 z-10">
                <tr className="border-b border-lia-border-subtle">
                  {mode === "manual" && <th className="w-10 px-3 py-2" />}
                  {isVisible("feedback") && <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">FEEDBACK</th>}
                  {isVisible("score") && (
                    <SortableHeader label="SCORE IA" columnKey="score" sortColumn={sortColumn} sortDirection={sortDirection} onSort={handleSort} />
                  )}
                  {isVisible("source") && <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">FONTE</th>}
                  <SortableHeader label="CANDIDATO" columnKey="name" sortColumn={sortColumn} sortDirection={sortDirection} onSort={handleSort} />
                  {isVisible("title") && (
                    <SortableHeader label="CARGO ATUAL" columnKey="title" sortColumn={sortColumn} sortDirection={sortDirection} onSort={handleSort} />
                  )}
                  {isVisible("company") && (
                    <SortableHeader label="EMPRESA ATUAL" columnKey="company" sortColumn={sortColumn} sortDirection={sortDirection} onSort={handleSort} />
                  )}
                  {isVisible("email") && <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">EMAIL</th>}
                  {isVisible("phone") && <th className="px-3 py-2 text-left font-medium text-lia-text-secondary">TELEFONE</th>}
                </tr>
              </thead>
              <tbody>
                {sortedResults.map((c) => {
                  const id = String(c.id)
                  const score = Number(c.lia_score || c.score || c.match_percentage || 0)
                  const name = (c.name || c.full_name || "—") as string
                  const title = (c.current_title || c.title || "—") as string
                  const company = (c.current_company || c.company || "—") as string
                  const source = (c.source_type || c.source || "global") as string
                  const feedback = searchFeedbacks[id]
                  const isSelected = selectedIds.has(id)
                  const isPreviewing = previewCandidate && String(previewCandidate.id) === id
                  const scoreColor = score >= 80 ? "text-status-success" : score >= 60 ? "text-status-warning" : "text-lia-text-tertiary"
                  const sourceIcon = source === "local" ? "🏠" : source === "hybrid" ? "⚡" : "🌐"

                  return (
                    <tr
                      key={id}
                      onClick={() => handleRowClick(c)}
                      className={`border-b border-lia-border-subtle cursor-pointer transition-colors ${
                        isPreviewing ? "bg-wedo-cyan/8 border-l-2 border-l-wedo-cyan" :
                        isSelected ? "bg-lia-bg-tertiary" : "hover:bg-lia-bg-secondary"
                      } ${feedback === "dislike" ? "opacity-40" : ""}`}
                    >
                      {mode === "manual" && (
                        <td className="px-3 py-2">
                          <button onClick={(e) => { e.stopPropagation(); onToggleSelect(id) }} className="w-5 h-5 flex items-center justify-center">
                            {isSelected ? <CheckSquare className="w-4 h-4 text-lia-text-primary" /> : <Square className="w-4 h-4 text-lia-text-tertiary" />}
                          </button>
                        </td>
                      )}
                      {isVisible("feedback") && (
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={(e) => { e.stopPropagation(); onFeedback(id, "like") }}
                              className={`w-6 h-6 rounded flex items-center justify-center transition-colors ${
                                feedback === "like" ? "bg-status-success/15 text-status-success" : "hover:bg-lia-bg-tertiary text-lia-text-tertiary"
                              }`}
                            >
                              <ThumbsUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); onFeedback(id, "dislike") }}
                              className={`w-6 h-6 rounded flex items-center justify-center transition-colors ${
                                feedback === "dislike" ? "bg-status-error/15 text-status-error" : "hover:bg-lia-bg-tertiary text-lia-text-tertiary"
                              }`}
                            >
                              <ThumbsDown className="w-3 h-3" />
                            </button>
                          </div>
                        </td>
                      )}
                      {isVisible("score") && (
                        <td className="px-3 py-2">
                          {score > 0 ? <span className={`font-semibold ${scoreColor}`}>{Math.round(score)}</span> : <Loader2 className="w-3.5 h-3.5 animate-spin text-lia-text-tertiary" />}
                        </td>
                      )}
                      {isVisible("source") && (
                        <td className="px-3 py-2"><span title={source}>{sourceIcon}</span></td>
                      )}
                      <td className="px-3 py-2 font-medium text-lia-text-primary max-w-[200px] truncate">{name}</td>
                      {isVisible("title") && <td className="px-3 py-2 text-lia-text-secondary max-w-[200px] truncate">{title}</td>}
                      {isVisible("company") && <td className="px-3 py-2 text-lia-text-secondary max-w-[150px] truncate">{company}</td>}
                      {isVisible("email") && (
                        <td className="px-3 py-2">
                          {(() => {
                            const email = (revealedContacts[id]?.email || c.email || "") as string
                            const src = (c.source_type || c.source || "") as string
                            const canReveal = isGlobalSource(src, Boolean(c.pearch_profile_id)) && c.has_email !== false
                            if (email) return <span className="text-xs text-lia-text-primary truncate max-w-[180px] block">{email}</span>
                            if (canReveal) return (
                              <button
                                onClick={(e) => { e.stopPropagation(); onRevealContact(id, name, "email", (c.linkedin_url || "") as string) }}
                                disabled={isRevealing}
                                className="inline-flex items-center gap-1.5 px-2 py-0.5 text-micro font-medium rounded-full bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active transition-colors disabled:opacity-50"
                              >
                                <Mail className="w-3 h-3" /><span>Revelar</span>
                              </button>
                            )
                            return <span className="text-xs text-lia-text-tertiary">—</span>
                          })()}
                        </td>
                      )}
                      {isVisible("phone") && (
                        <td className="px-3 py-2">
                          {(() => {
                            const phone = (revealedContacts[id]?.phone || c.phone || c.mobile_phone || "") as string
                            const src = (c.source_type || c.source || "") as string
                            const canReveal = isGlobalSource(src, Boolean(c.pearch_profile_id)) && c.has_phone !== false
                            if (phone) return <span className="text-xs text-lia-text-primary">{phone}</span>
                            if (canReveal) return (
                              <button
                                onClick={(e) => { e.stopPropagation(); onRevealContact(id, name, "phone", (c.linkedin_url || "") as string) }}
                                disabled={isRevealing}
                                className="inline-flex items-center gap-1.5 px-2 py-0.5 text-micro font-medium rounded-full bg-status-success/10 text-status-success hover:bg-status-success/15 transition-colors disabled:opacity-50"
                              >
                                <Phone className="w-3 h-3" /><span>Revelar</span>
                              </button>
                            )
                            return <span className="text-xs text-lia-text-tertiary">—</span>
                          })()}
                        </td>
                      )}
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

          {/* Preview panel */}
          {previewCandidate && (
            <PreviewPanel
              candidate={previewCandidate}
              candidates={sortedResults}
              currentIndex={previewIndex}
              vacancyId={vacancyId}
              isMaximized={isPreviewMaximized}
              onClose={() => setPreviewCandidate(null)}
              onToggleMaximize={() => setIsPreviewMaximized(p => !p)}
              onNavigate={handleNavigatePreview}
              panelWidth={panelWidth}
              onResizeStart={onResizeStart}
            />
          )}
        </div>
      )}

      {/* Auto-confirm overlay / Sticky CTA bar */}
      {showAutoConfirm && mode === "auto" && autoQualifyingPreview.length > 0 ? (
        <AutoConfirmOverlay preview={autoQualifyingPreview} minScore={autoConfig.minScore} onConfirm={onConfirmAutoAdd} onCancel={onCancelAutoAdd} />
      ) : (
        searchResults.length > 0 && (
          <div className="flex-shrink-0 border-t border-lia-border-subtle px-4 py-3 flex items-center justify-between bg-lia-bg-primary">
            <span className="text-xs text-lia-text-tertiary">{t("resultsCount", { shown: searchResults.length, total: totalResults })}</span>
            {mode === "manual" && selectedIds.size > 0 && (
              <Button size="sm" onClick={onAddToVacancy} className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white gap-1.5">
                {t("addToVacancy", { count: selectedIds.size })}
              </Button>
            )}
            {mode === "auto" && !isSearching && (
              <Button size="sm" onClick={onAddAuto} className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white gap-1.5">
                {t("autoConfirmAdd", { count: autoQualifying.length })}
              </Button>
            )}
          </div>
        )
      )}
    </div>
  )
}
