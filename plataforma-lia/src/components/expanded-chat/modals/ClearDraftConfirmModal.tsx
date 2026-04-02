"use client"

/**
 * ClearDraftConfirmModal — confirmação de limpeza de rascunho.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.3 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit('close'), emit('confirm').
 */

import { Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ClearDraftConfirmModalProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
}

export function ClearDraftConfirmModal({ open, onClose, onConfirm }: ClearDraftConfirmModalProps) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-overlay flex items-center justify-center bg-black/50">
          <div className="bg-lia-bg-primary rounded-xl w-panel-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-status-error/10 rounded-full flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-status-error" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-lia-text-primary">
                  Começar do zero?
                </h3>
              </div>
            </div>
            <p className="text-sm lia-text-secondary mb-4">
              Isso irá <strong>apagar todo o rascunho</strong> da vaga atual, incluindo todas as informações preenchidas até agora.
            </p>
            <p className="text-xs lia-text-secondary mb-4">
              Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1 h-10 rounded-md border-lia-border-default text-lia-text-secondary"
              >
                Cancelar
              </Button>
              <Button
                onClick={onConfirm}
                className="flex-1 h-10 rounded-md bg-status-error text-white"
              >
                <Trash2 className="w-4 h-4 mr-1.5" />
                Limpar tudo
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
