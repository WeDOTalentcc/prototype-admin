"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Plus, Users, CheckCircle, Clock, Search, Download,
  UserPlus, MoreHorizontal, Timer
} from"lucide-react"
import { type ApprovedCandidate, kanbanStages } from"./onboarding-premium-types"

interface OnboardingKanbanViewProps {
  filteredCandidates: ApprovedCandidate[]
  searchTerm: string
  stageFilter: string
  onSearchChange: (value: string) => void
  onStageFilterChange: (value: string) => void
  onCandidateClick: (candidate: ApprovedCandidate) => void
  onDragStart: (e: React.DragEvent, candidate: ApprovedCandidate) => void
  onDragOver: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, targetStage: string) => void
  approvedCandidates: ApprovedCandidate[]
}

export function OnboardingKanbanView({
  filteredCandidates,
  searchTerm,
  stageFilter,
  onSearchChange,
  onStageFilterChange,
  onCandidateClick,
  onDragStart,
  onDragOver,
  onDrop,
  approvedCandidates,
}: OnboardingKanbanViewProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-secondary">Novos Colaboradores</p>
                <p className="text-2xl font-semibold text-lia-text-primary">{approvedCandidates.length}</p>
                <p className="text-xs text-lia-text-primary">em onboarding</p>
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
                <p className="text-2xl font-semibold text-status-warning">
                  {approvedCandidates.filter(c => c.stage !== 'completed').length}
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
                  {approvedCandidates.filter(c => c.stage === 'completed').length}
                </p>
                <p className="text-xs text-lia-text-primary">este mês</p>
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
                <p className="text-sm font-medium text-lia-text-secondary">Tempo Médio</p>
                <p className="text-2xl font-semibold text-lia-text-primary">12d</p>
                <p className="text-xs text-lia-text-primary">para conclusão</p>
              </div>
              <div className="w-12 h-12 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <Timer className="w-6 h-6 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar colaboradores..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10 pr-4 py-2 border border-lia-border-default rounded-xl bg-lia-bg-primary text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 w-80"
            />
          </div>

          <select
            value={stageFilter}
            onChange={(e) => onStageFilterChange(e.target.value)}
            className="px-3 py-2 border border-lia-border-default rounded-xl bg-lia-bg-primary text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20"
          >
            <option value="all">Todas as Etapas</option>
            {kanbanStages.map(stage => (
              <option key={stage.id} value={stage.id}>{stage.name}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Exportar
          </Button>
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            Adicionar Colaborador
          </Button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="flex gap-6 min-w-max pb-6">
          {kanbanStages.map(stage => (
            <div
              key={stage.id}
              className="flex-shrink-0 w-80 bg-lia-bg-primary rounded-xl border border-lia-border-subtle"
              onDragOver={onDragOver}
              onDrop={(e) => onDrop(e, stage.id)}
            >
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Chip variant="neutral" muted className={stage.color}>
                      {stage.name}
                    </Chip>
                    <span className="text-sm font-medium text-lia-text-secondary">
                      {filteredCandidates.filter(c => c.stage === stage.id).length}
                    </span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-lia-text-primary mt-1">{stage.description}</p>
              </div>

              <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                {filteredCandidates
                  .filter(candidate => candidate.stage === stage.id)
                  .map(candidate => (
                    <CandidateKanbanCard
                      key={candidate.id}
                      candidate={candidate}
                      onDragStart={onDragStart}
                      onClick={() => onCandidateClick(candidate)}
                    />
                  ))}

                {filteredCandidates.filter(c => c.stage === stage.id).length === 0 && (
                  <div className="text-center py-8 text-lia-text-primary">
                    <Users className="w-8 h-8 mx-auto mb-2 opacity-50 text-lia-text-secondary" />
                    <p className="text-sm">Nenhum colaborador</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

interface CandidateKanbanCardProps {
  candidate: ApprovedCandidate
  onDragStart: (e: React.DragEvent, candidate: ApprovedCandidate) => void
  onClick: () => void
}

function CandidateKanbanCard({ candidate, onDragStart, onClick }: CandidateKanbanCardProps) {
  const daysUntilStart = Math.ceil((new Date(candidate.startDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))

  return (
    <Card
      className="cursor-move transition-colors motion-reduce:transition-none duration-200 border-l-4 border-l-lia-border-medium dark:border-l-lia-border-medium"
      draggable
      onDragStart={(e) => onDragStart(e, candidate)}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <Avatar className="w-10 h-10">
            <AvatarImage src={candidate.avatar} alt={candidate.name} />
            <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-sm text-lia-text-primary truncate">
              {candidate.name}
            </h4>
            <p className="text-xs text-lia-text-secondary">{candidate.position}</p>
            <p className="text-xs text-lia-text-primary">{candidate.department}</p>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-secondary">Progresso:</span>
            <span className="font-medium">{candidate.progress}%</span>
          </div>
          <div className="w-full bg-lia-interactive-active rounded-full h-2">
            <div
              className="bg-lia-bg-inverse dark:bg-lia-text-tertiary h-2 rounded-full"
              style={{width: `${candidate.progress}%`}}
            />
          </div>
        </div>

        <div className="mt-3 space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-secondary">Início:</span>
            <span className="font-medium">{new Date(candidate.startDate).toLocaleDateString('pt-BR')}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-secondary">Gestor:</span>
            <span className="font-medium">{candidate.manager}</span>
          </div>
          {daysUntilStart > 0 && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-lia-text-secondary">Faltam:</span>
              <Chip density="relaxed" variant="neutral" >
                {daysUntilStart} dias
              </Chip>
            </div>
          )}
        </div>

        <div className="flex gap-1 mt-3">
          {candidate.documents.length > 0 && (
            <div className="w-2 h-2 bg-status-warning rounded-full" title="Documentos pendentes" />
          )}
          {candidate.medicalExams.length > 0 && (
            <div className="w-2 h-2 bg-wedo-magenta rounded-full" title="Exames médicos" />
          )}
          {candidate.communications.length > 0 && (
            <div className="w-2 h-2 bg-status-success rounded-full" title="Comunicações enviadas" />
          )}
        </div>
      </CardContent>
    </Card>
  )
}
