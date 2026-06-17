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
    <div className="flex items-center justify-between bg-lia-bg-primary rounded-xl p-4">
      <div className="flex items-center gap-3">
        <SectionIcon className="w-5 h-5 text-lia-text-primary" />
        <div>
          <h2 className={textStyles.h3}>{title}</h2>
          <p className={textStyles.description}>{description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-lia-bg-tertiary text-lia-text-primary">
          {filled} de {total} campos
        </span>
        {isCreationMode ? (
          <Button
            onClick={onSave}
            disabled={isSaving}
            size="sm"
            className="gap-1.5 text-xs rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
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
              className="gap-1.5 text-xs rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
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
