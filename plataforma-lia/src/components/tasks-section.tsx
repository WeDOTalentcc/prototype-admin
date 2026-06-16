"use client"

import { useState } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { CheckCircle2, ArrowRight, Plus, MoreHorizontal, Zap, Users, FileText, MessageSquare } from"lucide-react"
import { TaskModal } from"@/components/task-modal"

const tasks = [
  {
    id: 1,
    title:"Crie uma nova vaga",
    description:"Configure nova posição no sistema com requisitos e descrição detalhada",
    icon: Plus,
    priority:"high",
    category:"setup"
  },
  {
    id: 2,
    title:"Solicite aprovação de nova vaga",
    description:"Encaminhe documentação para aprovação gerencial com justificativa",
    icon: FileText,
    priority:"high",
    category:"approval"
  },
  {
    id: 3,
    title:"Compartilhe candidatos com gestor",
    description:"Envie relatório com perfis aprovados e recomendações",
    icon: Users,
    priority:"high",
    category:"review"
  },
  {
    id: 4,
    title:"Solicite feedback de entrevista",
    description:"Colete avaliação detalhada pós-entrevista do gestor",
    icon: MessageSquare,
    priority:"high",
    category:"feedback"
  },
  {
    id: 5,
    title:"Consulte sobre candidato",
    description:"Obtenha informações específicas e histórico completo",
    icon: MessageSquare,
    priority:"high",
    category:"inquiry"
  },
  {
    id: 6,
    title:"Adicione novo candidato",
    description:"Cadastre perfil completo no banco de talentos",
    icon: Users,
    priority:"high",
    category:"registration"
  },
  {
    id: 7,
    title:"Reagende uma entrevista",
    description:"Altere horário e notifique automaticamente participantes",
    icon: FileText,
    priority:"high",
    category:"scheduling"
  },
  {
    id: 8,
    title:"Atualize status do candidato",
    description:"Modifique situação no processo e envie notificações",
    icon: FileText,
    priority:"high",
    category:"update"
  }
]

export function TasksSection() {
  const [selectedTask, setSelectedTask] = useState<typeof tasks[0] | null>(null)
  const [completedTasks, setCompletedTasks] = useState<number[]>([])

  const handleTaskClick = (task: typeof tasks[0]) => {
    setSelectedTask(task)
  }

  const markAsCompleted = (taskId: number) => {
    setCompletedTasks([...completedTasks, taskId])
    setSelectedTask(null)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case"high": return"border-status-error/30"
      case"medium": return"border-status-warning/30"
      case"low": return"border-status-success/30"
      default: return"border-lia-border-subtle bg-lia-bg-secondary text-lia-text-primary"
    }
  }

  const activeTasks = tasks.filter(task => !completedTasks.includes(task.id))

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-lia-text-primary">
            Próximas Tarefas
          </h2>
          <p className="text-xs text-lia-text-secondary">
            {activeTasks.length} tarefas pendentes
          </p>
        </div>
        <Button variant="outline" size="sm" className="gap-1 h-6 px-2 text-xs">
          <Plus className="w-3 h-3" />
          Nova Tarefa
        </Button>
      </div>

      {activeTasks.length > 0 ? (
        <div className="space-y-1">
          {activeTasks.slice(0, 6).map((task) => (
            <Card
              key={task.id}
              className="group cursor-pointer transition-colors motion-reduce:transition-none duration-200 hover:border-lia-border-default dark:border-lia-border-default border"
              onClick={() => handleTaskClick(task)}
            >
              <CardContent className="p-2">
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 w-6 h-6 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
 <task.icon className="w-3 h-3 text-lia-text-secondary" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
 <h3 className="text-xs font-medium text-lia-text-primary group-hover:text-lia-text-secondary transition-colors motion-reduce:transition-none">
                          {task.title}
                        </h3>
                        <p className="text-xs text-lia-text-secondary mt-0.5 line-clamp-2">
                          {task.description}
                        </p>
                      </div>

                      <div className="flex items-center gap-1 ml-2">
                        <Chip
                          variant="neutral"
                          className={`text-xs h-3.5 px-1 ${getPriorityColor(task.priority)}`}
                        >
                          {task.priority ==="high" ?"Alta" : task.priority ==="medium" ?"Média" :"Baixa"}
                        </Chip>
                        <ArrowRight className="w-2.5 h-2.5 text-lia-text-secondary group-hover:text-lia-text-secondary transition-colors motion-reduce:transition-none" />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-6 text-center">
          <CheckCircle2 className="w-8 h-8 mx-auto mb-3 text-status-success" />
          <h3 className="text-base font-medium text-lia-text-primary mb-1">
            Todas as tarefas concluídas!
          </h3>
          <p className="text-sm text-lia-text-secondary">
            Excelente trabalho! Você completou todas as suas tarefas.
          </p>
        </Card>
      )}

      {activeTasks.length > 6 && (
        <Button variant="ghost" className="w-full text-sm text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse">
          Ver mais {activeTasks.length - 6} tarefas
        </Button>
      )}

      {/* Task Modal */}
      <TaskModal
        task={selectedTask}
        isOpen={!!selectedTask}
        onClose={() => setSelectedTask(null)}
        onComplete={(taskId) => markAsCompleted(taskId)}
      />
    </div>
  )
}
