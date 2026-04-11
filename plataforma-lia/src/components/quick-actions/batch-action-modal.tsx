"use client"

import React, { useState } from "react"
import { useModalA11y } from "@/hooks/ui/use-modal-a11y"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ChevronRight, CheckCircle, X, User, Star, Zap } from "lucide-react"

interface Candidate {
  id: string; name: string; role: string; email: string; phone: string
  location: string; avatar?: string; score: number; status: string
  matchPercentage: number; riskLevel: string; culturalFit: number
  technicalMatch: number; experience: string; seniority: string
  availability: string; expectedSalary: string; preferredLocation: string
  linkedin?: string; portfolio?: string; skills: string[]
  lastActivity: string; source: string
}

interface BatchActionModalProps {
  isOpen: boolean
  onClose: () => void
  selectedCandidates: Candidate[]
  onBatchAction: (action: string, data: Record<string, unknown>) => void
}

export function BatchActionModal({ isOpen, onClose, selectedCandidates, onBatchAction }: BatchActionModalProps) {
  const [action, setAction] = useState('')
  const [stage, setStage] = useState('')
  const [comment, setComment] = useState('')
  const [assignTo, setAssignTo] = useState('')
  const [sendNotification, setSendNotification] = useState(true)
  const dialogRef = useModalA11y(isOpen, onClose)

  if (!isOpen || selectedCandidates.length === 0) return null

  const batchActions = [
    {
      id: 'move_stage',
      name: 'Mover Etapa',
      description: 'Mover candidatos para uma nova etapa do processo',
      icon: ChevronRight
    },
    {
      id: 'approve',
      name: 'Aprovar',
      description: 'Aprovar todos os candidatos selecionados',
      icon: CheckCircle
    },
    {
      id: 'reject',
      name: 'Rejeitar',
      description: 'Rejeitar todos os candidatos selecionados',
      icon: X
    },
    {
      id: 'assign',
      name: 'Atribuir Responsável',
      description: 'Atribuir um recrutador responsável',
      icon: User
    },
    {
      id: 'tag',
      name: 'Adicionar Tags',
      description: 'Adicionar tags de identificação',
      icon: Star
    }
  ]

  const stages = [
    'Triagem',
    'Entrevista Inicial',
    'Teste Técnico',
    'Entrevista Final',
    'Proposta',
    'Aprovado',
    'Rejeitado'
  ]

  const recruiters = [
    'Ana Silva - Recrutadora Sênior',
    'Carlos Mendes - Tech Lead',
    'Marina Costa - Gerente de Produto',
    'Roberto Santos - RH'
  ]

  const handleExecute = () => {
    const actionData = {
      action,
      stage,
      comment,
      assignTo,
      sendNotification,
      candidateIds: selectedCandidates.map(c => c.id)
    }

    onBatchAction(action, actionData)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay/70 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="batch-action-modal-title" className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 dark:border-lia-border-subtle">
          <div>
            <h3 id="batch-action-modal-title" className="text-lg font-semibold text-lia-text-primary">
              Ações em Lote
            </h3>
            <p className="text-sm text-lia-text-secondary">
              {selectedCandidates.length} candidatos selecionados
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Fechar ação em lote" data-dismiss="true">
            <X className="w-4 h-4" aria-hidden="true" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Candidatos Selecionados */}
          <div>
            <h4 className="text-sm font-medium text-lia-text-primary mb-3">
              Candidatos Selecionados
            </h4>
            <div className="max-h-32 overflow-y-auto border border-lia-border-subtle rounded-xl p-3">
              <div className="space-y-2">
                {selectedCandidates.map((candidate) => (
                  <div key={candidate.id} className="flex items-center gap-3">
                    <Avatar className="h-6 w-6">
                      <AvatarImage src={candidate.avatar} />
                      <AvatarFallback className="text-xs">{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                    </Avatar>
                    <span className="text-sm">{candidate.name}</span>
                    <span className="text-xs text-lia-text-primary">- {candidate.role}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Ação */}
          <div>
            <h4 className="text-sm font-medium text-lia-text-primary mb-3">
              Selecione a Ação
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {batchActions.map((actionItem) => (
                <button
                  key={actionItem.id}
                  onClick={() => setAction(actionItem.id)}
                  className={`p-4 border rounded-md text-left transition-colors motion-reduce:transition-none ${
 action === actionItem.id
                      ? 'border-lia-border-default bg-lia-bg-tertiary'
                      : 'border-lia-border-subtle hover:bg-lia-bg-secondary'
                  }`}
                >
                  <actionItem.icon className="w-5 h-5 mb-2" />
                  <div className="text-sm font-medium">{actionItem.name}</div>
                  <div className="text-xs text-lia-text-secondary">{actionItem.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Configurações específicas por ação */}
          {action === 'move_stage' && (
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Nova Etapa
              </label>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value)}
                className="w-full p-3 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
              >
                <option value="">Selecione a etapa</option>
                {stages.map((stageOption) => (
                  <option key={stageOption} value={stageOption}>{stageOption}</option>
                ))}
              </select>
            </div>
          )}

          {action === 'assign' && (
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">
                Atribuir para
              </label>
              <select
                value={assignTo}
                onChange={(e) => setAssignTo(e.target.value)}
                className="w-full p-3 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
              >
                <option value="">Selecione o responsável</option>
                {recruiters.map((recruiter) => (
                  <option key={recruiter} value={recruiter}>{recruiter}</option>
                ))}
              </select>
            </div>
          )}

          {/* Comentário */}
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-2">
              Comentário (opcional)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="w-full p-3 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
              placeholder="Adicione um comentário sobre esta ação..."
            />
          </div>

          {/* Notificação */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="notification"
              checked={sendNotification}
              onChange={(e) => setSendNotification(e.target.checked)}
              className="rounded-xl border-lia-border-subtle"
            />
            <label htmlFor="notification" className="text-sm text-lia-text-secondary">
              Enviar notificação para os candidatos sobre esta alteração
            </label>
          </div>

          {/* Ações */}
          <div className="flex justify-end gap-3 pt-6 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <Button variant="outline" onClick={onClose} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
              Cancelar
            </Button>
            <Button
              onClick={handleExecute}
              disabled={!action || (action === 'move_stage' && !stage) || (action === 'assign' && !assignTo)}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              <Zap className="w-4 h-4" />
              Executar Ação
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
