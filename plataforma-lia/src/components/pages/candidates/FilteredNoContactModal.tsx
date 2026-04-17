"use client"

import React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Download, ExternalLink } from "lucide-react"
import { useTranslations } from "next-intl"
import type { DiscardedCandidate } from "./hooks/useCandidatesExecuteSearch"

export interface FilteredNoContactModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  candidates: DiscardedCandidate[]
}

/**
 * Task #400: lista candidatos descartados pelo backend porque o enriquecimento
 * via Apify não retornou nem email nem telefone. Permite ao usuário inspecionar
 * quem ficou de fora e exportar para reaproveitamento manual posterior.
 */
export function FilteredNoContactModal({ open, onOpenChange, candidates }: FilteredNoContactModalProps) {
  const t = useTranslations('candidates')

  const handleExportCsv = React.useCallback(() => {
    if (!candidates.length) return
    const escape = (value: unknown): string => {
      const s = value == null ? "" : String(value)
      if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
      return s
    }
    const header = ["name", "headline", "current_title", "current_company", "location", "linkedin_url", "source"]
    const rows = candidates.map((c) => [
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
  }, [candidates])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col"
        data-testid="filtered-no-contact-modal"
      >
        <DialogHeader>
          <DialogTitle>{t('table.filteredNoContactModalTitle', { count: candidates.length })}</DialogTitle>
          <p className="text-sm text-lia-text-secondary mt-1">
            {t('table.filteredNoContactModalDescription')}
          </p>
        </DialogHeader>

        <div className="flex-1 overflow-auto border border-lia-border rounded-md">
          <table className="w-full text-sm">
            <thead className="bg-lia-bg-secondary sticky top-0">
              <tr>
                <th className="text-left p-2 font-medium">{t('table.col.name')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.title')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.company')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.location')}</th>
                <th className="text-left p-2 font-medium">{t('table.col.linkedin')}</th>
              </tr>
            </thead>
            <tbody>
              {candidates.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-lia-text-secondary">
                    {t('table.filteredNoContactModalEmpty')}
                  </td>
                </tr>
              ) : (
                candidates.map((c) => (
                  <tr key={c.id} className="border-t border-lia-border hover:bg-lia-bg-secondary/50">
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
                          className="inline-flex items-center gap-1 text-wedo-cyan hover:underline"
                        >
                          {t('table.openProfile')}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t('table.close')}
          </Button>
          <Button
            variant="primary"
            onClick={handleExportCsv}
            disabled={candidates.length === 0}
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
