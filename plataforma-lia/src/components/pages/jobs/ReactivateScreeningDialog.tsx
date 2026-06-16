"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import type { Job } from "@/components/jobs"

interface ReactivateScreeningDialogProps {
  open: boolean
  jobs: Job[]
  endDate: string
  onEndDateChange: (date: string) => void
  onClose: () => void
  onReactivate: () => void
}

export function ReactivateScreeningDialog({
  open,
  jobs,
  endDate,
  onEndDateChange,
  onClose,
  onReactivate,
}: ReactivateScreeningDialogProps) {
  if (!open || jobs.length === 0) return null

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-sm rounded-xl bg-lia-bg-primary border border-lia-border-subtle dark:bg-lia-bg-primary dark:border-lia-border-subtle">
        <DialogHeader className="pb-3 dark:border-lia-border-subtle">
          <DialogTitle className="text-sm font-semibold text-lia-text-primary">
            Reativar Triagem?
          </DialogTitle>
        </DialogHeader>
        <div className="py-4 space-y-3">
          <p className="text-xs text-lia-text-secondary">
            {jobs.length === 1
              ? `A vaga "${jobs[0]?.title}" tinha a triagem ativa antes de ser pausada. Deseja reativar a triagem?`
              : `${jobs.length} vagas tinham triagem ativa antes de serem pausadas. Deseja reativá-las?`
            }
          </p>
          <div className="space-y-2">
            <Label className="text-xs font-medium text-lia-text-secondary">
              Nova data de término (opcional)
            </Label>
            <Input
              type="date"
              value={endDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => onEndDateChange(e.target.value)}
              className="h-8 text-xs border-lia-border-subtle dark:border-lia-border-default dark:bg-lia-bg-elevated"
            />
          </div>
        </div>
        <DialogFooter className="gap-2 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-8 px-4 text-xs border-lia-border-default dark:border-lia-border-default"
          >
            Não, manter pausada
          </Button>
          <Button
            onClick={onReactivate}
            className="h-8 px-4 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active"
          >
            Sim, reativar triagem
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
