"use client"

import React from "react"
import { Archive, ArchiveRestore, Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface ConfirmArchiveDialogProps {
  open: boolean
  mode: "archive" | "unarchive"
  jobCount: number
  isLoading: boolean
  onCancel: () => void
  onConfirm: () => Promise<void>
}

export function ConfirmArchiveDialog({
  open,
  mode,
  jobCount,
  isLoading,
  onCancel,
  onConfirm,
}: ConfirmArchiveDialogProps) {
  const isArchive = mode === "archive"
  const plural = jobCount !== 1

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v && !isLoading) onCancel() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            {isArchive
              ? <Archive className="w-5 h-5 text-lia-text-secondary" />
              : <ArchiveRestore className="w-5 h-5 text-lia-text-secondary" />}
            <DialogTitle>
              {isArchive
                ? `Arquivar ${jobCount} vaga${plural ? "s" : ""}?`
                : `Desarquivar ${jobCount} vaga${plural ? "s" : ""}?`}
            </DialogTitle>
          </div>
          <DialogDescription className="text-sm leading-relaxed">
            {isArchive ? (
              <>
                As vagas ficarão <strong>ocultas</strong> desta lista, mas não serão excluídas.
                Candidatos, triagens e histórico são preservados.
                <br className="my-1" />
                Para recuperar, acesse a aba <strong>Arquivadas</strong>.
              </>
            ) : (
              <>
                As vagas voltarão para a lista principal com status <strong>Rascunho</strong>.
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
            className="w-full sm:w-auto"
          >
            Cancelar
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            className="w-full sm:w-auto"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {isArchive ? "Arquivando..." : "Desarquivando..."}
              </>
            ) : (
              isArchive ? "Arquivar" : "Desarquivar"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
