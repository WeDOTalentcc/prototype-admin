"use client"

import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  CheckCircle, Calendar, Mail, Phone, User
} from"lucide-react"
import type { OnboardingCandidate } from"./onboarding-page.types"
import { onboardingTemplates, getStatusColor, getStatusLabel } from"./onboarding-page.types"

interface CandidateDetailModalProps {
  candidate: OnboardingCandidate
  onClose: () => void
}

export function CandidateDetailModal({ candidate, onClose }: CandidateDetailModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-4xl h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarImage src={candidate.avatar} alt={candidate.name} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-xl font-semibold text-lia-text-primary">{candidate.name}</h2>
              <p className="text-lia-text-secondary">{candidate.position} • {candidate.department}</p>
              <Chip variant="neutral" muted className={`mt-1 ${getStatusColor(candidate.status)}`}>
                {getStatusLabel(candidate.status)}
              </Chip>
            </div>
          </div>
          <Button variant="ghost" onClick={onClose}>
            ×
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Informações Pessoais</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">{candidate.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">{candidate.phone}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">Gestor: {candidate.manager}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-lia-text-secondary" />
                    <span className="text-sm">Início: {new Date(candidate.startDate).toLocaleDateString('pt-BR')}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Progresso</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-lia-text-secondary">Progresso Geral</span>
                      <span className="text-sm font-medium">{candidate.progress}%</span>
                    </div>
                    <div className="w-full bg-lia-interactive-active rounded-full h-3">
                      <div
                        className="bg-lia-bg-inverse dark:bg-lia-text-tertiary h-3 rounded-full"
                        style={{width: `${candidate.progress}%`}}
                      />
                    </div>
                    <div className="flex justify-between text-sm text-lia-text-secondary">
                      <span>{candidate.completedTasks} de {candidate.totalTasks} tarefas</span>
                      <span>{candidate.lastActivity}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Tarefas de Onboarding</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {onboardingTemplates[0].tasks.map((task) => (
                      <div key={task.id} className="flex items-start gap-3 p-3 border border-lia-border-subtle rounded-xl">
                        <CheckCircle className={`w-5 h-5 mt-0.5 ${task.isCompleted ? 'text-status-success' : 'text-lia-text-secondary'}`} />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-medium text-lia-text-primary">{task.title}</h4>
                            <div className="flex items-center gap-2">
                              <Chip density="relaxed" variant="neutral" >
                                {task.assignedTo === 'candidate' ? 'Colaborador' :
                                 task.assignedTo === 'hr' ? 'RH' :
                                 task.assignedTo === 'manager' ? 'Gestor' :
                                 task.assignedTo === 'it' ? 'TI' : 'Admin'}
                              </Chip>
                              <Chip density="relaxed" variant={task.priority === 'critical' ? 'danger' : 'neutral'} >
                                {task.priority === 'critical' ? 'Crítica' :
                                 task.priority === 'high' ? 'Alta' :
                                 task.priority === 'medium' ? 'Média' : 'Baixa'}
                              </Chip>
                            </div>
                          </div>
                          <p className="text-sm text-lia-text-secondary mb-2">{task.description}</p>
                          <div className="flex items-center gap-4 text-xs text-lia-text-primary">
                            <span>Prazo: Dia {task.dueDate}</span>
                            <span>Tempo estimado: {task.estimatedTime}min</span>
                            {task.completedDate && (
                              <span className="text-status-success">
                                Concluído em {new Date(task.completedDate).toLocaleDateString('pt-BR')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
