"use client"

import React from "react"
import { CheckCircle2, AlertTriangle, Copy } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { BulkItemResult } from "@/lib/bulk"

interface BulkResultReportProps {
  isOpen: boolean
  onClose: () => void
  results: BulkItemResult[]
  actionLabel: string
}

/**
 * Relatório pós-envio em massa. Puramente apresentacional — sem lógica de negócio.
 * Abre DEPOIS do modal de comunicação fechar. DS v4.2.1 tokens.
 */
export function BulkResultReport({
  isOpen,
  onClose,
  results,
  actionLabel,
}: BulkResultReportProps) {
  if (!isOpen) return null

  const succeeded = results.filter((r) => r.ok)
  const failed = results.filter((r) => !r.ok)
  const pct = results.length > 0 ? Math.round((succeeded.length / results.length) * 100) : 0

  const handleCopyFailed = () => {
    const text = failed.map((r) => `${r.name}: ${r.reason ?? "falha"}`).join("\n")
    navigator.clipboard.writeText(text).catch(() => undefined)
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-lia-text-primary">
            {actionLabel} — {succeeded.length} de {results.length} enviados
          </DialogTitle>
        </DialogHeader>

        <div
          className="h-2 w-full rounded-full bg-lia-border overflow-hidden"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full bg-[#60BED1] transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>

        <ul className="mt-2 max-h-72 overflow-y-auto divide-y divide-lia-border text-sm">
          {results.map((r) => (
            <li key={r.id} className="flex items-center gap-2 py-2 px-1">
              {r.ok ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-status-success" aria-hidden />
              ) : (
                <AlertTriangle className="w-4 h-4 shrink-0 text-status-warning" aria-hidden />
              )}
              <span
                className={`flex-1 font-medium ${
                  r.ok ? "text-lia-text-primary" : "text-lia-text-secondary"
                }`}
              >
                {r.name}
              </span>
              {!r.ok && r.reason && (
                <span className="text-xs text-status-error">{r.reason}</span>
              )}
            </li>
          ))}
        </ul>

        <DialogFooter className="mt-2 gap-2">
          {failed.length > 0 && (
            <Button variant="outline" size="sm" onClick={handleCopyFailed} className="gap-1">
              <Copy className="w-3.5 h-3.5" />
              Copiar lista de falhas
            </Button>
          )}
          <Button variant="primary" size="sm" onClick={onClose}>
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
