"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { X, CheckCircle, Clock, Users, FileText } from "lucide-react"

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
      case "high": return "border-red-200 bg-red-50 text-red-700"
      case "medium": return "border-yellow-200 bg-yellow-50 text-yellow-700"
      case "low": return "border-green-200 bg-green-50 text-green-700"
      default: return "border-gray-200 bg-gray-50 text-gray-800 dark:text-gray-200"
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4 rounded-md dark:bg-gray-800 dark:border-gray-700">
        <CardHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg dark:text-gray-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>{task.title}</CardTitle>
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
            <Badge
              variant="outline"
              className={`text-xs ${getPriorityColor(task.priority)}`}
            >
              {task.priority === "high" ? "Alta" : task.priority === "medium" ? "Média" : "Baixa"}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {task.category}
            </Badge>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400">
            {task.description}
          </p>

          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleComplete}
              className="flex-1 gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              <CheckCircle className="w-4 h-4" />
              Marcar como Concluída
            </Button>
            <Button
              variant="outline"
              onClick={onClose}
              className="dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              Fechar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
