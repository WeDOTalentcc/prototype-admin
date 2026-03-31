import React from 'react'

interface EditButtonProps {
  className?: string
  size?: 'sm' | 'md'
  isEditing: boolean
  onStartEditing: () => void
}

export const EditButton = React.memo(function EditButton({
  className,
  size = 'sm',
  isEditing,
  onStartEditing,
}: EditButtonProps) {
  if (isEditing) return null

  const sizeClasses =
    size === 'sm' ? 'py-1.5 px-3 text-xs gap-1.5' : 'py-2 px-4 text-xs gap-2'

  return (
    <button
      onClick={onStartEditing}
      className={`inline-flex items-center font-medium rounded-xl border border-lia-border-default bg-lia-bg-primary hover:bg-gray-50 lia-text-base transition-colors motion-reduce:transition-none ${sizeClasses} ${className || ''}`}
    >
      <svg
        className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
        />
      </svg>
      Editar
    </button>
  )
})
EditButton.displayName = 'EditButton'

interface SaveCancelButtonsProps {
  className?: string
  saveLabel?: string
  cancelLabel?: string
  isEditing: boolean
  isSaving: boolean
  onCancel: () => void
  onSave: () => Promise<void>
}

export const SaveCancelButtons = React.memo(function SaveCancelButtons({
  className,
  saveLabel = 'Salvar Alterações',
  cancelLabel = 'Cancelar',
  isEditing,
  isSaving,
  onCancel,
  onSave,
}: SaveCancelButtonsProps) {
  if (!isEditing) return null

  return (
    <div className={`flex items-center gap-2 ${className || ''}`}>
      <button
        onClick={onCancel}
        disabled={isSaving}
        className="inline-flex items-center py-1.5 px-3 text-xs font-medium rounded-xl border border-lia-border-default bg-lia-bg-primary hover:bg-gray-50 lia-text-base transition-colors motion-reduce:transition-none disabled:opacity-50"
      >
        {cancelLabel}
      </button>
      <button
        onClick={onSave}
        disabled={isSaving}
        className="inline-flex items-center gap-1.5 py-1.5 px-3 text-xs font-medium rounded-xl text-white transition-colors motion-reduce:transition-none disabled:opacity-50 bg-gray-900"
      >
        {isSaving ? (
          <>
            <svg
              className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Salvando...
          </>
        ) : (
          <>
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            {saveLabel}
          </>
        )}
      </button>
    </div>
  )
})
SaveCancelButtons.displayName = 'SaveCancelButtons'
