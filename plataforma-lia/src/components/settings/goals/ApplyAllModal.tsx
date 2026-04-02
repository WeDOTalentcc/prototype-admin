import { Button } from "@/components/ui/button"
import { Save, X } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

interface ApplyAllModalProps {
  templateId: string
  applyAllValue: number
  applyAllMonths: boolean
  applyAllUsers: boolean
  isSaving: boolean
  setApplyAllValue: (v: number) => void
  setApplyAllMonths: (v: boolean) => void
  setApplyAllUsers: (v: boolean) => void
  setShowApplyAllModal: (v: string | null) => void
  applyValueToAll: (templateId: string, value: number, opts: { allMonths: boolean; allUsers: boolean }) => Promise<void>
}

export function ApplyAllModal({
  templateId,
  applyAllValue,
  applyAllMonths,
  applyAllUsers,
  isSaving,
  setApplyAllValue,
  setApplyAllMonths,
  setApplyAllUsers,
  setShowApplyAllModal,
  applyValueToAll,
}: ApplyAllModalProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-md p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className={textStyles.h4}>
            Aplicar Valor para Todos
          </h3>
          <Button variant="ghost" size="sm" onClick={() => setShowApplyAllModal(null)} className="h-6 w-6 p-0">
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className={`${textStyles.label} block mb-1`}>
              Valor da Meta
            </label>
            <input
              type="number"
              value={applyAllValue}
              onChange={(e) => setApplyAllValue(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary text-lia-text-primary text-sm font-['Open_Sans',sans-serif]"
            />
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={applyAllMonths}
                onChange={(e) => setApplyAllMonths(e.target.checked)}
                className="w-4 h-4 rounded-md border-lia-border-default accent-gray-900"
              />
              <span className={textStyles.bodySmall}>
                Aplicar mesmo valor a todos os meses
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={applyAllUsers}
                onChange={(e) => setApplyAllUsers(e.target.checked)}
                className="w-4 h-4 rounded-md border-lia-border-default accent-gray-900"
              />
              <span className={textStyles.bodySmall}>
                Aplicar a todos os usuários
              </span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setShowApplyAllModal(null)}>
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={async () => {
                setShowApplyAllModal(null)
                await applyValueToAll(templateId, applyAllValue, {
                  allMonths: applyAllMonths,
                  allUsers: applyAllUsers
                })
              }}
              className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
            >
              <Save className="w-3.5 h-3.5 mr-1.5" />
              Aplicar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
