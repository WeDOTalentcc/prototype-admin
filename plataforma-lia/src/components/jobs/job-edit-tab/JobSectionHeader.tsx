import React from "react"
import { Button } from "@/components/ui/button"
import { Loader2, Save, Edit } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

interface JobSectionHeaderProps {
  SectionIcon: React.ElementType
  title: string
  description: string
  filled: number
  total: number
  isCreationMode?: boolean
  isEditing: boolean
  isSaving: boolean
  onSave: () => void
  onStartEditing: () => void
  onCancel: () => void
}

export function JobSectionHeader({
  SectionIcon,
  title,
  description,
  filled,
  total,
  isCreationMode,
  isEditing,
  isSaving,
  onSave,
  onStartEditing,
  onCancel,
}: JobSectionHeaderProps) {
  return (
    <div className="flex items-center justify-between bg-white dark:bg-lia-bg-secondary rounded-md p-4">
      <div className="flex items-center gap-3">
        <SectionIcon className="w-5 h-5 lia-text-700 dark:text-lia-text-secondary" />
        <div>
          <h2 className={textStyles.h3}>{title}</h2>
          <p className={textStyles.description}>{description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 lia-text-700 dark:bg-lia-bg-elevated dark:text-lia-text-secondary font-['Open_Sans',sans-serif]">
          {filled} de {total} campos
        </span>
        {isCreationMode ? (
          <Button
            onClick={onSave}
            disabled={isSaving}
            size="sm"
            className="gap-1.5 text-xs rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
          >
            {isSaving ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" />Salvando...</>
            ) : (
              <><Save className="w-3.5 h-3.5" />Salvar Seção</>
            )}
          </Button>
        ) : !isEditing ? (
          <Button
            onClick={onStartEditing}
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs rounded-md"
          >
            <Edit className="w-3.5 h-3.5" />
            Editar
          </Button>
        ) : (
          <div className="flex items-center gap-2">
            <Button
              onClick={onCancel}
              disabled={isSaving}
              variant="outline"
              size="sm"
              className="text-xs rounded-md"
            >
              Cancelar
            </Button>
            <Button
              onClick={onSave}
              disabled={isSaving}
              size="sm"
              className="gap-1.5 text-xs rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
            >
              {isSaving ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" />Salvando...</>
              ) : (
                <><Save className="w-3.5 h-3.5" />Salvar</>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
