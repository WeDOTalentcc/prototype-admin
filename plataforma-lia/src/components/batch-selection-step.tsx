"use client"

import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Button } from"@/components/ui/button"
import {
  Search, Check, MapPin, Calendar, Users,
} from"lucide-react"
import { formatScorePercent } from"@/lib/design-tokens"
import {
  availableStages,
  getScoreColor,
  getPriorityColor,
  type BatchApprovalCandidate,
} from"@/hooks/candidates/use-batch-approval"

interface BatchSelectionStepProps {
  filteredCandidates: BatchApprovalCandidate[]
  selectedCandidates: Set<string>
  selectedCount: number
  searchTerm: string
  setSearchTerm: (v: string) => void
  filterCriteria: { stage: string; score: string; priority: string; department: string }
  setFilterCriteria: (v: { stage: string; score: string; priority: string; department: string }) => void
  toggleCandidateSelection: (id: string) => void
  selectAll: () => void
  deselectAll: () => void
}

export function BatchSelectionStep({
  filteredCandidates,
  selectedCandidates,
  selectedCount,
  searchTerm,
  setSearchTerm,
  filterCriteria,
  setFilterCriteria,
  toggleCandidateSelection,
  selectAll,
  deselectAll,
}: BatchSelectionStepProps) {
  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar candidatos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20"
            />
          </div>

          <select
            value={filterCriteria.stage}
            onChange={(e) => setFilterCriteria({...filterCriteria, stage: e.target.value})}
            className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm"
          >
            <option value="all">Todas as etapas</option>
            {availableStages.map(stage => (
              <option key={stage.id} value={stage.id}>{stage.name}</option>
            ))}
          </select>

          <select
            value={filterCriteria.score}
            onChange={(e) => setFilterCriteria({...filterCriteria, score: e.target.value})}
            className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm"
          >
            <option value="all">Todos os scores</option>
            <option value="high">Alto (85+)</option>
            <option value="medium">Médio (70-84)</option>
            <option value="low">Baixo (&lt;70)</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={selectAll}>
            Selecionar Todos
          </Button>
          <Button variant="outline" size="sm" onClick={deselectAll}>
            Limpar Seleção
          </Button>
          <span className="text-sm text-lia-text-secondary">
            {selectedCount} de {filteredCandidates.length} selecionados
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredCandidates.map((candidate) => (
          <Card
            key={candidate.id}
            className={`cursor-pointer transition-colors motion-reduce:transition-none duration-200 ${
selectedCandidates.has(candidate.id)
                ? 'ring-2 ring-lia-btn-primary-bg dark:ring-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-elevated'
                : 'hover:border-lia-border-default'
            }`}
            onClick={() => toggleCandidateSelection(candidate.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Avatar className="w-10 h-10">
                      <AvatarImage src={candidate.avatar} alt={candidate.name} />
                      <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-sm font-medium">
                        {candidate.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    {selectedCandidates.has(candidate.id) && (
                      <div className="absolute -top-1 -right-1 w-5 h-5 bg-lia-btn-primary-bg rounded-full flex items-center justify-center">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h4 className="font-semibold text-lia-text-primary text-sm">
                      {candidate.name}
                    </h4>
                    <p className="text-xs text-lia-text-secondary">
                      {candidate.position}
                    </p>
                  </div>
                </div>

                <Chip variant="neutral" muted className={`${getPriorityColor(candidate.priority)} text-xs`}>
                  {candidate.priority}
                </Chip>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-lia-text-secondary">Score IA:</span>
                  <Chip variant="neutral" muted className={`${getScoreColor(candidate.liaScore)} text-xs`}>
                    {formatScorePercent(candidate.liaScore)}
                  </Chip>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-lia-text-secondary">Etapa:</span>
                  <Chip density="relaxed" variant="neutral" >
                    {availableStages.find(s => s.id === candidate.currentStage)?.name || candidate.currentStage}
                  </Chip>
                </div>

                <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                  <MapPin className="w-3 h-3" />
                  {candidate.location}
                </div>

                <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                  <Calendar className="w-3 h-3" />
                  {new Date(candidate.appliedDate).toLocaleDateString('pt-BR')}
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex flex-wrap gap-1">
                  {candidate.skills.slice(0, 3).map((skill) => (
                    <Chip density="relaxed" key={skill} variant="neutral" muted className="px-1 py-0">
                      {skill}
                    </Chip>
                  ))}
                  {candidate.skills.length > 3 && (
                    <Chip density="relaxed" variant="neutral" className="px-1 py-0">
                      +{candidate.skills.length - 3}
                    </Chip>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredCandidates.length === 0 && (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
          <h3 className="text-lg font-medium text-lia-text-primary mb-2">
            Nenhum candidato encontrado
          </h3>
          <p className="text-lia-text-secondary">
            Ajuste os filtros para encontrar candidatos
          </p>
        </div>
      )}
    </div>
  )
}
