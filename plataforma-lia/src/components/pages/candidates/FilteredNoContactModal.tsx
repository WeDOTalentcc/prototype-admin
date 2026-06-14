"use client"

import React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Download, ExternalLink, RefreshCw, CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import type { DiscardedCandidate } from "./hooks/useCandidatesExecuteSearch"

export interface DiscardedEnrichmentResult {
  candidate: DiscardedCandidate
  email?: string | null
  phone?: string | null
}

export interface FilteredNoContactModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  candidates: DiscardedCandidate[]
  /**
   * Task #402: callback chamado quando o re-enriquecimento de um candidato
   * descartado retornou email ou telefone. O parent deve mover o candidato
   * para a lista principal de resultados.
   */
  onCandidateEnriched?: (result: DiscardedEnrichmentResult) => void
}

type RowState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; email?: string | null; phone?: string | null }
  | { status: "no-contact"; message?: string }
  | { status: "error"; message?: string }

/**
 * Task #400: lista candidatos descartados pelo backend porque o enriquecimento
 * via Apify não retornou nem email nem telefone. Permite ao usuário inspecionar
 * quem ficou de fora e exportar para reaproveitamento manual posterior.
 *
 * Task #402: também permite forçar uma nova tentativa de enriquecimento (uma
 * por linha ou em lote para todos visíveis), e quando o Apify finalmente
 * encontra email/telefone o candidato é movido para a lista principal.
 */
export function FilteredNoContactModal({
  open,
  onOpenChange,
  candidates,
  onCandidateEnriched,
}: FilteredNoContactModalProps) {
  const t = useTranslations('candidates')
  const [rowStates, setRowStates] = React.useState<Record<string, RowState>>({})
  const [bulkRunning, setBulkRunning] = React.useState(false)
  const [bulkProgress, setBulkProgress] = React.useState<{ done: number; total: number; ok: number }>(
    { done: 0, total: 0, ok: 0 }
  )

  // Removidos = candidatos já enriquecidos com sucesso (saíram para a lista
  // principal). Mantemos no Set para filtrar mesmo que o pai ainda não tenha
  // atualizado o array `candidates`.
  const [removedIds, setRemovedIds] = React.useState<Set<string>>(new Set())

  React.useEffect(() => {
    if (!open) {
      setRowStates({})
      setBulkRunning(false)
      setBulkProgress({ done: 0, total: 0, ok: 0 })
      setRemovedIds(new Set())
    }
  }, [open])

  const visibleCandidates = React.useMemo(
    () => candidates.filter((c) => !removedIds.has(c.id)),
    [candidates, removedIds]
  )

  const setRow = React.useCallback((id: string, state: RowState) => {
    setRowStates((prev) => ({ ...prev, [id]: state }))
  }, [])

  const enrichOne = React.useCallback(
    async (candidate: DiscardedCandidate): Promise<RowState> => {
      if (!candidate.linkedin_url) {
        return { status: "error", message: t('table.discardedRetryNoUrl') }
      }
      setRow(candidate.id, { status: "loading" })
      try {
        const response = await fetch('/api/backend-proxy/search/enrich-discarded', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            linkedin_url: candidate.linkedin_url,
            candidate_id: candidate.id,
            candidate_name: candidate.name,
          }),
        })
        const data = await response.json().catch(() => ({}))
        if (!response.ok || !data?.success) {
          const next: RowState = {
            status: "error",
            message: typeof data?.error === 'string' ? data.error : (data?.message || ''),
          }
          setRow(candidate.id, next)
          return next
        }
        const email: string | null | undefined = data.email
        const phone: string | null | undefined = data.phone
        if (data.has_contact && (email || phone)) {
          const next: RowState = { status: "success", email, phone }
          setRow(candidate.id, next)
          setRemovedIds((prev) => {
            const copy = new Set(prev)
            copy.add(candidate.id)
            return copy
          })
          onCandidateEnriched?.({ candidate, email: email ?? null, phone: phone ?? null })
          return next
        }
        const next: RowState = {
          status: "no-contact",
          message: typeof data?.message === 'string' ? data.message : '',
        }
        setRow(candidate.id, next)
        return next
      } catch (err) {
        const message = err instanceof Error ? err.message : ''
        const next: RowState = { status: "error", message }
        setRow(candidate.id, next)
        return next
      }
    },
    [onCandidateEnriched, setRow, t]
  )

  const handleRetryRow = React.useCallback(
    async (candidate: DiscardedCandidate) => {
      const result = await enrichOne(candidate)
      if (result.status === 'success') {
        toast.success(t('table.discardedRetrySuccess', { name: candidate.name }))
      } else if (result.status === 'no-contact') {
        toast.info(t('table.discardedRetryNoContact', { name: candidate.name }))
      } else if (result.status === 'error') {
        toast.error(t('table.discardedRetryError', { name: candidate.name }))
      }
    },
    [enrichOne, t]
  )

  const handleRetryAll = React.useCallback(async () => {
    const targets = visibleCandidates.filter((c) => {
      if (!c.linkedin_url) return false
      const state = rowStates[c.id]
      return !state || state.status === 'idle' || state.status === 'error' || state.status === 'no-contact'
    })
    if (targets.length === 0) return
    setBulkRunning(true)
    setBulkProgress({ done: 0, total: targets.length, ok: 0 })
    let okCount = 0
    let doneCount = 0
    for (const cand of targets) {
      const result = await enrichOne(cand)
      doneCount += 1
      if (result.status === 'success') okCount += 1
      setBulkProgress({ done: doneCount, total: targets.length, ok: okCount })
    }
    setBulkRunning(false)
    if (okCount > 0) {
      toast.success(t('table.discardedRetryBulkSuccess', { count: okCount }))
    } else {
      toast.info(t('table.discardedRetryBulkEmpty'))
    }
  }, [enrichOne, rowStates, t, visibleCandidates])

  const handleExportCsv = React.useCallback(() => {
    if (!visibleCandidates.length) return
    const escape = (value: unknown): string => {
      const s = value == null ? "" : String(value)
      if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
      return s
    }
    const header = ["name", "headline", "current_title", "current_company", "location", "linkedin_url", "source"]
    const rows = visibleCandidates.map((c) => [
      c.name, c.headline ?? "", c.current_title ?? "", c.current_company ?? "",
      c.location ?? "", c.linkedin_url ?? "", c.source ?? "",
    ])
    const csv = [header, ...rows].map((r) => r.map(escape).join(",")).join("\n")
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${t('table.discardedCsvFilename')}-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [visibleCandidates, t])

  const retryableCount = visibleCandidates.filter((c) => !!c.linkedin_url).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col"
        data-testid="filtered-no-contact-modal"
      >
        <DialogHeader>
          <DialogTitle>{t('table.filteredNoContactModalTitle', { count: visibleCandidates.length })}</DialogTitle>
          <p className="text-sm text-lia-text-secondary mt-1">
            {t('table.filteredNoContactModalDescription')}
          </p>
        </DialogHeader>

        {bulkRunning && (
          <div
            className="flex items-center gap-2 px-3 py-2 bg-status-info/10 border border-status-info/20 rounded-md text-sm text-status-info"
            role="status"
            aria-live="polite"
            data-testid="filtered-no-contact-bulk-progress"
          >
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>
              {t('table.discardedRetryBulkProgress', {
                done: bulkProgress.done,
                total: bulkProgress.total,
                ok: bulkProgress.ok,
              })}
            </span>
          </div>
        )}

        <div className="flex-1 overflow-auto border border-lia-border-default rounded-md">
          <table className="w-full text-sm">
            <thead className="bg-lia-bg-secondary sticky top-0">
              <tr>
                <th className="text-left p-2 font-medium">{t('table.col.name')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.title')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.company')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.location')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.linkedin')}</th>
                <th className="text-right p-2 font-medium">{t('table.col.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {visibleCandidates.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-lia-text-secondary">
                    {t('table.filteredNoContactModalEmpty')}
                  </td>
                </tr>
              ) : (
                visibleCandidates.map((c) => {
                  const state: RowState = rowStates[c.id] ?? { status: 'idle' }
                  const isLoading = state.status === 'loading'
                  const noUrl = !c.linkedin_url
                  return (
                    <tr key={c.id} className="border-t border-lia-border-default hover:bg-lia-bg-secondary/50">
                      <td className="p-2 align-top">{c.name}</td>
                      <td className="p-2 align-top">{c.current_title || c.headline || "—"}</td>
                      <td className="p-2 align-top">{c.current_company || "—"}</td>
                      <td className="p-2 align-top">{c.location || "—"}</td>
                      <td className="p-2 align-top">
                        {c.linkedin_url ? (
                          <a
                            href={c.linkedin_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-lia-text-secondary hover:underline"
                          >
                            {t('table.openProfile')}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="p-2 align-top text-right">
                        <div className="inline-flex items-center gap-2 justify-end">
                          {state.status === 'no-contact' && (
                            <span className="inline-flex items-center gap-1 text-xs text-status-warning">
                              <XCircle className="h-3.5 w-3.5" />
                              {t('table.discardedRetryNoContactBadge')}
                            </span>
                          )}
                          {state.status === 'error' && (
                            <span className="inline-flex items-center gap-1 text-xs text-status-error">
                              <XCircle className="h-3.5 w-3.5" />
                              {t('table.discardedRetryErrorBadge')}
                            </span>
                          )}
                          {state.status === 'success' && (
                            <span className="inline-flex items-center gap-1 text-xs text-status-success">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              {t('table.discardedRetrySuccessBadge')}
                            </span>
                          )}
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            className="h-7"
                            onClick={() => handleRetryRow(c)}
                            disabled={isLoading || bulkRunning || noUrl}
                            data-testid={`filtered-no-contact-retry-${c.id}`}
                            aria-label={t('table.discardedRetryAriaLabel', { name: c.name })}
                          >
                            {isLoading ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <RefreshCw className="h-3.5 w-3.5" />
                            )}
                            <span className="ml-1">{t('table.discardedRetry')}</span>
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t('table.close')}
          </Button>
          <Button
            variant="outline"
            onClick={handleRetryAll}
            disabled={bulkRunning || retryableCount === 0}
            data-testid="filtered-no-contact-retry-all"
          >
            {bulkRunning ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            {t('table.discardedRetryAll', { count: retryableCount })}
          </Button>
          <Button
            variant="primary"
            onClick={handleExportCsv}
            disabled={visibleCandidates.length === 0}
            data-testid="filtered-no-contact-export-csv"
          >
            <Download className="h-4 w-4 mr-2" />
            {t('table.exportCsv')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
