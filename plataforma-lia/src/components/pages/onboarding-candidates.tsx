"use client"

import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Plus, Search, Eye, MoreHorizontal, MessageSquare
} from"lucide-react"
import type { OnboardingCandidate } from"./onboarding-page.types"
import { getStatusColor, getStatusLabel } from"./onboarding-page.types"

interface OnboardingCandidatesProps {
  filteredCandidates: OnboardingCandidate[]
  searchTerm: string
  setSearchTerm: (value: string) => void
  statusFilter: string
  setStatusFilter: (value: string) => void
  setSelectedCandidate: (candidate: OnboardingCandidate) => void
}

export function OnboardingCandidates({
  filteredCandidates,
  searchTerm,
  setSearchTerm,
  statusFilter,
  setStatusFilter,
  setSelectedCandidate
}: OnboardingCandidatesProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar colaboradores..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-lia-border-default rounded-xl bg-lia-bg-primary text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 w-80"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-lia-border-default rounded-xl bg-lia-bg-primary text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20"
          >
            <option value="all">Todos os Status</option>
            <option value="pending">Pendente</option>
            <option value="in_progress">Em Andamento</option>
            <option value="completed">Concluído</option>
            <option value="delayed">Atrasado</option>
          </select>
        </div>

        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Onboarding
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredCandidates.map(candidate => (
          <Card key={candidate.id} className="hover:transition-shadow cursor-pointer">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Avatar className="w-12 h-12">
                    <AvatarImage src={candidate.avatar} alt={candidate.name} />
                    <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                  </Avatar>
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{candidate.name}</h4>
                    <p className="text-sm text-lia-text-secondary">{candidate.position}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-lia-text-primary">Status:</span>
                  <Chip variant="neutral" muted className={getStatusColor(candidate.status)}>
                    {getStatusLabel(candidate.status)}
                  </Chip>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-lia-text-primary">Departamento:</span>
                  <span className="font-medium">{candidate.department}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-lia-text-primary">Gestor:</span>
                  <span className="font-medium">{candidate.manager}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-lia-text-primary">Início:</span>
                  <span className="font-medium">{new Date(candidate.startDate).toLocaleDateString('pt-BR')}</span>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-lia-text-primary">Progresso:</span>
                    <span className="font-medium">{candidate.progress}%</span>
                  </div>
                  <div className="w-full bg-lia-interactive-active rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        candidate.status === 'completed' ? 'bg-status-success' :
                        candidate.status === 'delayed' ? 'bg-status-error' : 'bg-lia-bg-inverse dark:bg-lia-text-tertiary'
                      }`}
                      style={{width: `${candidate.progress}%`}}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-lia-text-primary">Tarefas:</span>
                  <span className="font-medium">{candidate.completedTasks}/{candidate.totalTasks}</span>
                </div>

                <div className="text-sm text-lia-text-primary">
                  Última atividade: {candidate.lastActivity}
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 gap-2"
                  onClick={() => setSelectedCandidate(candidate)}
                >
                  <Eye className="w-4 h-4" />
                  Ver Detalhes
                </Button>
                <Button size="sm" variant="outline" className="gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Contato
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
