import { useState, useCallback } from 'react'

interface UseEditLockOptions {
  onSave?: () => Promise<void> | void
  onCancel?: () => void
}

interface UseEditLockReturn {
  isEditing: boolean
  isSaving: boolean
  startEditing: () => void
  cancelEditing: () => void
  saveAndExit: () => Promise<void>
  EditButton: React.FC<{ className?: string; size?: 'sm' | 'md' }>
  SaveCancelButtons: React.FC<{ className?: string; saveLabel?: string; cancelLabel?: string }>
}

export function useEditLock(options: UseEditLockOptions = {}): UseEditLockReturn {
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const startEditing = useCallback(() => {
    setIsEditing(true)
  }, [])

  const cancelEditing = useCallback(() => {
    setIsEditing(false)
    options.onCancel?.()
  }, [options])

  const saveAndExit = useCallback(async () => {
    setIsSaving(true)
    try {
      await options.onSave?.()
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }, [options])

  const EditButton: React.FC<{ className?: string; size?: 'sm' | 'md' }> = ({ className, size = 'sm' }) => {
    if (isEditing) return null
    
    const sizeClasses = size === 'sm' 
      ? 'py-1.5 px-3 text-xs gap-1.5' 
      : 'py-2 px-4 text-xs gap-2'
    
    return (
      <button
        onClick={startEditing}
        className={`inline-flex items-center font-medium rounded-2xl border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 transition-colors ${sizeClasses} ${className || ''}`}
       
      >
        <svg className={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
        Editar
      </button>
    )
  }

  const SaveCancelButtons: React.FC<{ className?: string; saveLabel?: string; cancelLabel?: string }> = ({ 
    className, 
    saveLabel = 'Salvar Alterações',
    cancelLabel = 'Cancelar'
  }) => {
    if (!isEditing) return null
    
    return (
      <div className={`flex items-center gap-2 ${className || ''}`}>
        <button
          onClick={cancelEditing}
          disabled={isSaving}
          className="inline-flex items-center py-1.5 px-3 text-xs font-medium rounded-2xl border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 transition-colors disabled:opacity-50"
         
        >
          {cancelLabel}
        </button>
        <button
          onClick={saveAndExit}
          disabled={isSaving}
          className="inline-flex items-center gap-1.5 py-1.5 px-3 text-xs font-medium rounded-2xl text-white transition-colors disabled:opacity-50 bg-gray-900"
        >
          {isSaving ? (
            <>
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Salvando...
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {saveLabel}
            </>
          )}
        </button>
      </div>
    )
  }

  return {
    isEditing,
    isSaving,
    startEditing,
    cancelEditing,
    saveAndExit,
    EditButton,
    SaveCancelButtons
  }
}

export type { UseEditLockReturn }
