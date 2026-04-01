// @ts-nocheck
import { Button } from "@/components/ui/button"
import { Trash2, Loader2 } from "lucide-react"
import { getCategoryIcon } from "../goals"
import type { UserGoal } from "../use-goals-management"

interface DeleteConfirmModalProps {
  goal: UserGoal
  isDeleting: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function DeleteConfirmModal({ goal, isDeleting, onCancel, onConfirm }: DeleteConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-md w-full max-w-md mx-4 overflow-hidden">
        <div className="bg-status-error/10 px-6 py-4 border-b border-status-error/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-status-error/15 flex items-center justify-center">
              <Trash2 className="w-5 h-5 text-status-error" />
            </div>
            <div>
              <h3 className="text-lg font-semibold lia-text-950">Excluir Meta</h3>
              <p className="text-sm lia-text-600">Esta ação não pode ser desfeita</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-gray-50 rounded-md p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              {getCategoryIcon(goal.category)}
              <span className="font-medium lia-text-950">{goal.name}</span>
            </div>
            <p className="text-sm lia-text-600">{goal.description}</p>
            <div className="flex items-center gap-4 mt-3 text-xs lia-text-500">
              <span>Meta: {goal.target} {goal.unit}</span>
              <span>•</span>
              <span>{goal.period === "monthly" ? "Mensal" : goal.period === "quarterly" ? "Trimestral" : "Anual"}</span>
            </div>
          </div>

          <p className="text-sm lia-text-600 mb-6">
            Tem certeza que deseja excluir esta meta? O progresso registrado será perdido permanentemente.
          </p>

          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={onCancel} disabled={isDeleting}>
              Cancelar
            </Button>
            <Button onClick={onConfirm} disabled={isDeleting} className="bg-status-error hover:bg-status-error text-white">
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                  Excluindo...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Sim, Excluir
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
