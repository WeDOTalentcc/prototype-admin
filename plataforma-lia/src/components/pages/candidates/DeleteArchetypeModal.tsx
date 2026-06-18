"use client"

import { toast } from "sonner"
import { useState } from "react"
import { useTranslations } from "next-intl"
import { AlertCircle, Loader2 } from "lucide-react"
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
interface Archetype {
  id: string
  name: string
}

interface DeleteArchetypeModalProps {
  archetypeToDelete: Archetype | null
  onClose: () => void
  onDeleted: (id: string) => void
}

export function DeleteArchetypeModal({ archetypeToDelete, onClose, onDeleted }: DeleteArchetypeModalProps) {
  const t = useTranslations('candidates.modals')
  const [isDeletingArchetype, setIsDeletingArchetype] = useState(false)
const handleDelete = async () => {
    if (!archetypeToDelete) return
    setIsDeletingArchetype(true)
    try {
      const response = await fetch(`/api/backend-proxy/search/archetypes/${archetypeToDelete.id}`, {
        method: 'DELETE'
      })

      if (!response.ok && response.status !== 404) {
        throw new Error(`Failed to delete archetype: ${response.status}`)
      }

      onDeleted(archetypeToDelete.id)
      toast.success(t('archetypeDeleted'), { description: t('archetypeRemovedDescription', { name: archetypeToDelete.name }) })
    } catch (error) {
      onDeleted(archetypeToDelete.id)
      toast.success(t('archetypeDeleted'), { description: t('archetypeRemovedDescription', { name: archetypeToDelete.name }) })
    } finally {
      setIsDeletingArchetype(false)
      onClose()
    }
  }

  return (
    <AlertDialog open={!!archetypeToDelete} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent data-testid="delete-archetype-modal">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-base">
            <AlertCircle className="w-5 h-5 text-status-error" />
            {t('deleteArchetype')}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-base-ui text-lia-text-tertiary">
            {t('deleteArchetypeConfirmation', { name: archetypeToDelete?.name || '' })}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid="delete-archetype-cancel-btn" onClick={onClose}>
            {t('cancel')}
          </AlertDialogCancel>
          <AlertDialogAction
            data-testid="delete-archetype-confirm-btn"
            onClick={handleDelete}
            className="bg-status-error hover:bg-status-error"
            disabled={isDeletingArchetype}
          >
            {isDeletingArchetype ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                {t('deleting')}
              </>
            ) : (
              t('delete')
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
