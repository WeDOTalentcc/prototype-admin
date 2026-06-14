"use client"

import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  CheckCircle, XCircle, ArrowRight, MessageSquare,
  Bell, Mail, Calendar, Star,
} from"lucide-react"
import { formatScorePercent } from"@/lib/design-tokens"
import {
  availableStages,
  actionTemplates,
  getScoreColor,
  type BatchApprovalAction,
  type BatchApprovalCandidate,
} from"@/hooks/candidates/use-batch-approval"

const ICON_MAP = {
  CheckCircle,
  XCircle,
  ArrowRight,
  MessageSquare,
} as const

interface BatchActionStepProps {
  selectedCount: number
  batchAction: BatchApprovalAction
  setBatchAction: (action: BatchApprovalAction) => void
}

export function BatchActionStep({
  selectedCount,
  batchAction,
  setBatchAction,
}: BatchActionStepProps) {
  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-lia-text-primary mb-2">
            Escolha a Ação para {selectedCount} Candidatos
          </h3>
          <p className="text-lia-text-secondary">
            Selecione a ação que deseja aplicar aos candidatos selecionados
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          {actionTemplates.map((template) => {
            const IconComponent = ICON_MAP[template.icon]
            return (
              <Card
                key={template.id}
                className={`cursor-pointer transition-colors motion-reduce:transition-none duration-200 ${
batchAction.type === template.type
                    ? 'ring-2 ring-lia-btn-primary-bg dark:ring-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-elevated'
                    : 'hover:border-lia-border-default'
                }`}
                onClick={() => setBatchAction({
                  ...batchAction,
                  type: template.type,
                  comment: template.defaultComment
                })}
              >
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-md flex items-center justify-center ${template.color}`}>
                      <IconComponent className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-lia-text-primary">
                        {template.name}
                      </h4>
                      <p className="text-sm text-lia-text-secondary">
                        {template.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Configurações da Ação</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {batchAction.type === 'move' && (
              <div>
                <label className="block text-sm font-medium text-lia-text-primary mb-2">
                  Mover para Etapa
                </label>
                <select
                  value={batchAction.targetStage || ''}
                  onChange={(e) => setBatchAction({...batchAction, targetStage: e.target.value})}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary"
                >
                  <option value="">Selecione uma etapa</option>
                  {availableStages.map(stage => (
                    <option key={stage.id} value={stage.id}>{stage.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Comentário Geral
              </label>
              <textarea
                value={batchAction.comment}
                onChange={(e) => setBatchAction({...batchAction, comment: e.target.value})}
                placeholder="Adicione um comentário sobre esta ação em lote..."
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary h-24 resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover">
                <input
                  type="checkbox"
                  checked={batchAction.notifyTeam}
                  onChange={(e) => setBatchAction({...batchAction, notifyTeam: e.target.checked})}
                  className="rounded-xl border-lia-border-default"
                />
                <Bell className="w-4 h-4 text-lia-text-secondary" />
                <span className="text-sm text-lia-text-primary">Notificar equipe</span>
              </label>

              <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover">
                <input
                  type="checkbox"
                  checked={batchAction.sendEmail}
                  onChange={(e) => setBatchAction({...batchAction, sendEmail: e.target.checked})}
                  className="rounded-xl border-lia-border-default"
                />
                <Mail className="w-4 h-4 text-status-success" />
                <span className="text-sm text-lia-text-primary">Enviar email aos candidatos</span>
              </label>

              <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover">
                <input
                  type="checkbox"
                  checked={batchAction.scheduleInterview}
                  onChange={(e) => setBatchAction({...batchAction, scheduleInterview: e.target.checked})}
                  className="rounded-xl border-lia-border-default"
                />
                <Calendar className="w-4 h-4 text-wedo-purple" />
                <span className="text-sm text-lia-text-primary">Agendar entrevistas automaticamente</span>
              </label>

              <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover">
                <input
                  type="checkbox"
                  checked={batchAction.addToTalentPool}
                  onChange={(e) => setBatchAction({...batchAction, addToTalentPool: e.target.checked})}
                  className="rounded-xl border-lia-border-default"
                />
                <Star className="w-4 h-4 text-wedo-orange" />
                <span className="text-sm text-lia-text-primary">Adicionar ao banco de talentos</span>
              </label>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

interface BatchReviewStepProps {
  selectedCount: number
  batchAction: BatchApprovalAction
  selectedCandidates: Set<string>
  candidates: BatchApprovalCandidate[]
}

export function BatchReviewStep({
  selectedCount,
  batchAction,
  selectedCandidates,
  candidates,
}: BatchReviewStepProps) {
  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-lia-text-primary mb-2">
            Revisar Ação em Lote
          </h3>
          <p className="text-lia-text-secondary">
            Confirme os detalhes antes de processar
          </p>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-semibold text-lia-text-primary mb-1">{selectedCount}</div>
              <div className="text-sm text-lia-text-secondary">Candidatos Selecionados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-semibold text-status-success mb-1">
                {batchAction.type === 'approve' ? selectedCount : 0}
              </div>
              <div className="text-sm text-lia-text-secondary">Serão Aprovados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-semibold text-status-error mb-1">
                {batchAction.type === 'reject' ? selectedCount : 0}
              </div>
              <div className="text-sm text-lia-text-secondary">Serão Rejeitados</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-semibold text-wedo-purple-text mb-1">
                {batchAction.type === 'move' ? selectedCount : 0}
              </div>
              <div className="text-sm text-lia-text-secondary">Serão Movidos</div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Detalhes da Ação</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-lia-text-primary">Tipo de Ação:</label>
                <p className="text-lia-text-primary capitalize">
                  {batchAction.type === 'approve' ? 'Aprovar' :
                   batchAction.type === 'reject' ? 'Rejeitar' :
                   batchAction.type === 'move' ? 'Mover para ' + (availableStages.find(s => s.id === batchAction.targetStage)?.name || '') :
                   'Adicionar Notas'}
                </p>
              </div>

              {batchAction.comment && (
                <div>
                  <label className="text-sm font-medium text-lia-text-primary">Comentário:</label>
                  <p className="text-lia-text-primary">{batchAction.comment}</p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-lia-text-primary">Ações Adicionais:</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {batchAction.notifyTeam && (
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary flex items-center gap-1">
                      <Bell className="w-3 h-3" />
                      Notificar equipe
                    </Chip>
                  )}
                  {batchAction.sendEmail && (
                    <Chip variant="neutral" muted className="flex items-center gap-1">
                      <Mail className="w-3 h-3" />
                      Enviar emails
                    </Chip>
                  )}
                  {batchAction.scheduleInterview && (
                    <Chip variant="neutral" muted className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Agendar entrevistas
                    </Chip>
                  )}
                  {batchAction.addToTalentPool && (
                    <Chip variant="neutral" muted className="flex items-center gap-1">
                      <Star className="w-3 h-3" />
                      Banco de talentos
                    </Chip>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Candidatos Selecionados ({selectedCount})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {Array.from(selectedCandidates).map(candidateId => {
                const candidate = candidates.find(c => c.id === candidateId)
                if (!candidate) return null

                return (
                  <div key={candidateId} className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={candidate.avatar} alt={candidate.name} />
                        <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-xs">
                          {candidate.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium text-lia-text-primary text-sm">
                          {candidate.name}
                        </div>
                        <div className="text-xs text-lia-text-secondary">
                          {candidate.position} • Score: {formatScorePercent(candidate.liaScore)}
                        </div>
                      </div>
                    </div>

                    <Chip variant="neutral" muted className={`${getScoreColor(candidate.liaScore)} text-xs`}>
                      {formatScorePercent(candidate.liaScore)}
                    </Chip>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
