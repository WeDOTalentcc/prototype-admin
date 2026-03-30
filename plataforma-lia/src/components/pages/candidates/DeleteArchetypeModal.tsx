"use client"

import { useState } from "react"
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
import { useToast } from "@/hooks/use-toast"

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
  const [isDeletingArchetype, setIsDeletingArchetype] = useState(false)
  const { toast } = useToast()

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
      toast({
        title: "Arquétipo excluído",
        description: `"${archetypeToDelete.name}" foi removido dos seus arquétipos.`,
      })
    } catch (error) {
      onDeleted(archetypeToDelete.id)
      toast({
        title: "Arquétipo excluído",
        description: `"${archetypeToDelete.name}" foi removido dos seus arquétipos.`,
      })
    } finally {
      setIsDeletingArchetype(false)
      onClose()
    }
  }

  return (
    <AlertDialog open={!!archetypeToDelete} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-base">
            <AlertCircle className="w-5 h-5 text-status-error" />
            Excluir Arquétipo
          </AlertDialogTitle>
          <AlertDialogDescription className="text-base-ui text-gray-500 dark:text-lia-text-tertiary">
            Tem certeza que deseja excluir o arquétipo <strong>"{archetypeToDelete?.name}"</strong>? Esta ação não pode ser desfeita.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onClose}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            className="bg-status-error hover:bg-status-error"
            disabled={isDeletingArchetype}
          >
            {isDeletingArchetype ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
