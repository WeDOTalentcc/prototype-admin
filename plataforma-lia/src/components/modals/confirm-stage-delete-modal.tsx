"use client"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"

interface ConfirmStageDeleteModalProps {
  isOpen: boolean
  onClose: () => void
  candidateCount?: number
}

export function ConfirmStageDeleteModal({ isOpen, onClose, candidateCount }: ConfirmStageDeleteModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Etapa com candidatos
          </DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          {candidateCount
            ? `Esta etapa possui ${candidateCount} candidato(s).`
            : "Esta etapa possui candidatos."}
          {" "}Para excluí-la, responda no chat informando para qual etapa deseja mover os candidatos.
        </p>
        <div className="flex justify-end pt-2">
          <Button onClick={onClose}>Entendido — responder no chat</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
