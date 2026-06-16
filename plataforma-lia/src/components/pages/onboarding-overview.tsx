"use client"

import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  CheckCircle, Clock, UserPlus, TrendingUp
} from"lucide-react"
import { onboardingCandidates, getStatusColor, getStatusLabel } from"./onboarding-page.types"

export function OnboardingOverview() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-secondary">Total de Novos Colaboradores</p>
                <p className="text-2xl font-semibold text-lia-text-primary">{onboardingCandidates.length}</p>
                <p className="text-xs text-lia-text-primary">este mês</p>
              </div>
              <div className="w-12 h-12 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
                <UserPlus className="w-6 h-6 text-lia-text-secondary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-secondary">Em Andamento</p>
                <p className="text-2xl font-semibold text-lia-text-secondary">
                  {onboardingCandidates.filter(c => c.status === 'in_progress').length}
                </p>
                <p className="text-xs text-lia-text-primary">processos ativos</p>
              </div>
              <div className="w-12 h-12 bg-status-warning/15 rounded-md flex items-center justify-center">
                <Clock className="w-6 h-6 text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-secondary">Concluídos</p>
                <p className="text-2xl font-semibold text-status-success">
                  {onboardingCandidates.filter(c => c.status === 'completed').length}
                </p>
                <p className="text-xs text-lia-text-primary">com sucesso</p>
              </div>
              <div className="w-12 h-12 bg-status-success/15 rounded-md flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-secondary">Taxa de Sucesso</p>
                <p className="text-2xl font-semibold text-lia-text-primary">92%</p>
                <p className="text-xs text-lia-text-primary">últimos 3 meses</p>
              </div>
              <div className="w-12 h-12 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-xs">Processos Ativos de Onboarding</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {onboardingCandidates.filter(c => c.status === 'in_progress' || c.status === 'delayed').map(candidate => (
              <div key={candidate.id} className="p-4 border border-lia-border-subtle rounded-xl hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={candidate.avatar} alt={candidate.name} />
                      <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                    </Avatar>

                    <div>
                      <h4 className="font-medium text-lia-text-primary">{candidate.name}</h4>
                      <p className="text-sm text-lia-text-secondary">{candidate.position} • {candidate.department}</p>
                      <p className="text-sm text-lia-text-primary">Início: {new Date(candidate.startDate).toLocaleDateString('pt-BR')}</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <Chip variant="neutral" muted className={getStatusColor(candidate.status)}>
                      {getStatusLabel(candidate.status)}
                    </Chip>
                    <p className="text-sm text-lia-text-primary mt-1">{candidate.currentStep}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="w-24 bg-lia-interactive-active rounded-full h-2">
                        <div
                          className="bg-lia-bg-inverse dark:bg-lia-text-tertiary h-2 rounded-full"
                          style={{width: `${candidate.progress}%`}}
                        />
                      </div>
                      <span className="text-sm font-medium">{candidate.progress}%</span>
                    </div>
                    <p className="text-xs text-lia-text-primary mt-1">
                      {candidate.completedTasks}/{candidate.totalTasks} tarefas
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xs">Próximas Tarefas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { task: 'Configurar email corporativo', candidate: 'Carlos Santos', dueDate: 'Hoje', priority: 'high' },
              { task: 'Reunião de apresentação', candidate: 'Maria Oliveira', dueDate: 'Amanhã', priority: 'medium' },
              { task: 'Treinamento de segurança', candidate: 'Carlos Santos', dueDate: '2 dias', priority: 'medium' },
              { task: 'Entrega de equipamentos', candidate: 'Ana Pereira', dueDate: '3 dias', priority: 'high' }
            ].map((item, index) => (
              <div key={`${item.task}-${index}`} className="flex items-center justify-between p-3 bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    item.priority === 'high' ? 'bg-status-error' :
                    item.priority === 'medium' ? 'bg-status-warning' : 'bg-status-success'
                  }`} />
                  <div>
                    <p className="font-medium text-lia-text-primary">{item.task}</p>
                    <p className="text-sm text-lia-text-secondary">{item.candidate}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-lia-text-primary">{item.dueDate}</p>
                  <Chip density="relaxed" variant="neutral" >
                    {item.priority === 'high' ? 'Alta' : item.priority === 'medium' ? 'Média' : 'Baixa'}
                  </Chip>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
