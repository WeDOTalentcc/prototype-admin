"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Check, Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { LIST_COLORS } from "./use-lists-tab"
import { ListFormModalProps, DeleteListDialogProps } from "./lists-tab-types"

export function ListFormModal({
  open,
  editingList,
  formName,
  formDescription,
  formColor,
  saving,
  onFormNameChange,
  onFormDescriptionChange,
  onFormColorChange,
  onSave,
  onClose,
}: ListFormModalProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="">
            {editingList ? 'Editar Lista' : 'Nova Lista'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-lia-text-primary">
              Nome da lista <span className="text-status-error">*</span>
            </label>
            <Input
              placeholder="Ex: Candidatos para entrevista"
              value={formName}
              onChange={(e) => onFormNameChange(e.target.value)}
              className="h-9"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-lia-text-primary">
              Descrição
            </label>
            <Textarea
              placeholder="Descreva o propósito desta lista..."
              value={formDescription}
              onChange={(e) => onFormDescriptionChange(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-lia-text-primary">
              Cor
            </label>
            <div className="flex flex-wrap gap-2">
              {LIST_COLORS.map((color) => (
                <button
                  key={color.value}
                  type="button"
                  onClick={() => onFormColorChange(color.value)}
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-[width,height] ${
formColor === color.value
                      ? 'ring-2 ring-offset-2 ring-lia-border-medium'
                      : 'hover:scale-110'
                  }`}
                  style={{backgroundColor: color.value}}
                  title={color.name}
                >
                  {formColor === color.value && (
                    <Check className="w-4 h-4 text-white" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={saving}
          >
            Cancelar
          </Button>
          <Button
            onClick={onSave}
            disabled={saving || !formName.trim()}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                Salvando...
              </>
            ) : editingList ? (
              'Salvar alterações'
            ) : (
              'Criar lista'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function DeleteListDialog({
  listToDelete,
  deleting,
  onDelete,
  onCancel,
}: DeleteListDialogProps) {
  return (
    <AlertDialog open={!!listToDelete} onOpenChange={(open: boolean) => !open && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="">
            Excluir lista?
          </AlertDialogTitle>
          <AlertDialogDescription>
            Tem certeza que deseja excluir a lista <strong>"{listToDelete?.name}"</strong>?
            {listToDelete && listToDelete.candidate_count > 0 && (
              <span className="block mt-2 text-status-warning" aria-live="polite" aria-atomic="true">
                Esta lista contém {listToDelete.candidate_count} {listToDelete.candidate_count === 1 ? 'candidato' : 'candidatos'}.
                Os candidatos não serão excluídos, apenas a associação com esta lista.
              </span>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={onDelete}
            disabled={deleting}
            className="bg-status-error hover:bg-status-error"
          >
            {deleting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                Excluindo...
              </>
            ) : (
              'Excluir'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
