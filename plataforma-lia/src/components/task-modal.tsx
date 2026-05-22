"use client"

import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { X, CheckCircle, Clock, Users, FileText } from"lucide-react"

export interface TaskModalProps {
  task: {
    id: number
    title: string
    description: string
    category: string
    priority: string
  } | null
  isOpen: boolean
  onClose: () => void
  onComplete: (taskId: number) => void
}

export function TaskModal({ task, isOpen, onClose, onComplete }: TaskModalProps) {
  if (!isOpen || !task) return null

  const handleComplete = () => {
    onComplete(task.id)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case"high": return"border-status-error/30"
      case"medium": return"border-status-warning/30"
      case"low": return"border-status-success/30"
      default: return"border-lia-border-subtle bg-lia-bg-secondary text-lia-text-primary"
    }
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4 rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{task.title}</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Chip
              variant="neutral"
              className={`text-xs ${getPriorityColor(task.priority)}`}
            >
              {task.priority ==="high" ?"Alta" : task.priority ==="medium" ?"Média" :"Baixa"}
            </Chip>
            <Chip density="relaxed" variant="neutral" >
              {task.category}
            </Chip>
          </div>

          <p className="text-sm text-lia-text-secondary">
            {task.description}
          </p>

          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleComplete}
              className="flex-1 gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              <CheckCircle className="w-4 h-4" />
              Marcar como Concluída
            </Button>
            <Button
              variant="outline"
              onClick={onClose}
              className="dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
            >
              Fechar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
