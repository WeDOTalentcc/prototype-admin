"use client"

import { useState, useCallback, useMemo } from 'react'
import { useRecruitmentStages } from '@/hooks/recruitment/use-recruitment-stages'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Chip } from '@/components/ui/chip'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  ArrowRight, 
  XCircle, 
  Users, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Mail,
  Tag
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { REJECTION_REASONS } from '@/lib/recruitment-stages'
import { RECRUITMENT_STAGES, type RecruitmentStage } from '@/lib/recruitment/stages-data'
// REJECTION_REASONS kept as fallback for when DB sub-statuses are unavailable
import type { BulkActionType } from '@/components/ui/bulk-actions-bar'

export interface BulkActionCandidate {
  id: string
  name: string
  email?: string
  avatar?: string | null
  currentStage?: string
}

export interface BulkActionResult {
  candidateId: string
  success: boolean
  error?: string
}

interface BulkActionModalProps {
  isOpen: boolean
  onClose: () => void
  actionType: BulkActionType
  candidates: BulkActionCandidate[]
  stages?: RecruitmentStage[]
  jobTitle?: string
  onExecute: (data: BulkActionExecuteData) => Promise<BulkActionResult[]>
}

export interface BulkActionExecuteData {
  actionType: BulkActionType
  candidateIds: string[]
  targetStage?: string
  rejectionReason?: string
  rejectionNotes?: string
  message?: string
  tags?: string[]
}

interface ProgressState {
  total: number
  completed: number
  successful: number
  failed: number
  results: BulkActionResult[]
}

const ACTION_CONFIG: Record<BulkActionType, { title: string; description: string; icon: React.ReactNode }> = {
  move_stage: {
    title: 'Mover Candidatos de Etapa',
    description: 'Selecione a etapa de destino para os candidatos selecionados.',
    icon: <ArrowRight className="w-4 h-4 text-lia-text-secondary" />
  },
  reject: {
    title: 'Reprovar Candidatos',
    description: 'Informe o motivo da reprovação para os candidatos selecionados.',
    icon: <XCircle className="w-4 h-4 text-status-error" />
  },
  request_data: {
    title: 'Solicitar Dados',
    description: 'Envie uma solicitação de dados para os candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  send_message: {
    title: 'Enviar Mensagem',
    description: 'Envie uma mensagem para os candidatos selecionados.',
    icon: <Mail className="w-4 h-4 text-lia-text-secondary" />
  },
  export: {
    title: 'Exportar Candidatos',
    description: 'Exporte os dados dos candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  add_to_list: {
    title: 'Adicionar à Lista',
    description: 'Adicione os candidatos selecionados a uma lista.',
    icon: <Users className="w-4 h-4 text-lia-text-secondary" />
  },
  add_to_vacancy: {
    title: 'Adicionar à Vaga',
    description: 'Adicione os candidatos selecionados a uma vaga.',
    icon: <ArrowRight className="w-4 h-4 text-lia-text-secondary" />
  },
  share_search: {
    title: 'Compartilhar Busca',
    description: 'Compartilhe a busca com outros recrutadores.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  favorites: {
    title: 'Adicionar aos Favoritos',
    description: 'Adicione os candidatos selecionados aos favoritos.',
    icon: <Users className="w-4 h-4 text-lia-text-secondary" />
  },
  wsi_screening: {
    title: 'Triagem WSI',
    description: 'Aplique triagem WSI nos candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  hide: {
    title: 'Ocultar Candidatos',
    description: 'Oculte os candidatos selecionados da visualização.',
    icon: <XCircle className="w-4 h-4 text-lia-text-secondary" />
  },
  save_to_base: {
    title: 'Salvar na Base',
    description: 'Salve os candidatos selecionados na base de dados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  publish: {
    title: 'Publicar',
    description: 'Publique os candidatos selecionados.',
    icon: <ArrowRight className="w-4 h-4 text-lia-text-secondary" />
  },
  insights: {
    title: 'Ver Insights',
    description: 'Veja insights sobre os candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  duplicate: {
    title: 'Duplicar',
    description: 'Duplique os candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary" />
  },
  toggle_status: {
    title: 'Alternar Status',
    description: 'Alterne o status dos candidatos selecionados.',
    icon: <ArrowRight className="w-4 h-4 text-lia-text-secondary" />
  },
  assign_recruiter: {
    title: 'Atribuir Recrutador',
    description: 'Atribua um recrutador aos candidatos selecionados.',
    icon: <Users className="w-4 h-4 text-lia-text-secondary" />
  },
  add_tags: {
    title: 'Adicionar Tags',
    description: 'Adicione tags aos candidatos selecionados. Separe por vírgula.',
    icon: <Tag className="w-4 h-4 text-lia-text-secondary" />
  },
  remove_tags: {
    title: 'Remover Tags',
    description: 'Remova tags dos candidatos selecionados. Separe por vírgula.',
    icon: <Tag className="w-4 h-4 text-status-error" />
  },
}

const getRandomAvatarUrl = (_candidateId: string, _name: string): string | undefined => {
  return undefined
}

export function BulkActionModal({
  isOpen,
  onClose,
  actionType,
  candidates,
  stages = RECRUITMENT_STAGES,
  jobTitle,
  onExecute,
}: BulkActionModalProps) {
  const { stages: companyPipelineStages } = useRecruitmentStages()

  // Sub-statuses do estágio"rejected" vindos do DB; fallback para REJECTION_REASONS estático
  const rejectionReasonOptions = useMemo(() => {
    const rejectedStage = companyPipelineStages.find(s => s.name === 'rejected')
    if (rejectedStage?.sub_statuses?.length) {
      return rejectedStage.sub_statuses.map(ss => ({ code: ss.name, displayName: ss.display_name }))
    }
    return REJECTION_REASONS.map(r => ({ code: r.code, displayName: r.displayName }))
  }, [companyPipelineStages])

  const [isExecuting, setIsExecuting] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [showAllCandidates, setShowAllCandidates] = useState(false)
  const [targetStage, setTargetStage] = useState<string>('')
  const [rejectionReason, setRejectionReason] = useState<string>('')
  const [rejectionNotes, setRejectionNotes] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [progress, setProgress] = useState<ProgressState>({
    total: 0,
    completed: 0,
    successful: 0,
    failed: 0,
    results: []
  })

  const config = ACTION_CONFIG[actionType]
  const displayedCandidates = showAllCandidates ? candidates : candidates.slice(0, 5)
  
  const availableStages = useMemo(() => {
    return stages.filter(s => s.stageType === 'active' && !s.isInitial)
  }, [stages])

  const canExecute = useMemo(() => {
    if (isExecuting) return false
    
    switch (actionType) {
      case 'move_stage':
        return !!targetStage
      case 'reject':
        return !!rejectionReason
      case 'add_tags':
      case 'remove_tags':
        return tagInput.trim().length > 0
      default:
        return true
    }
  }, [actionType, targetStage, rejectionReason, tagInput, isExecuting])

  const handleExecute = useCallback(async () => {
    if (!canExecute) return
    
    setIsExecuting(true)
    setProgress({
      total: candidates.length,
      completed: 0,
      successful: 0,
      failed: 0,
      results: []
    })

    try {
      const data: BulkActionExecuteData = {
        actionType,
        candidateIds: candidates.map(c => c.id),
        targetStage: actionType === 'move_stage' ? targetStage : undefined,
        rejectionReason: actionType === 'reject' ? rejectionReason : undefined,
        rejectionNotes: actionType === 'reject' ? rejectionNotes : undefined,
        tags: (actionType === 'add_tags' || actionType === 'remove_tags')
          ? tagInput.split(',').map(t => t.trim()).filter(Boolean)
          : undefined,
      }

      const results = await onExecute(data)
      
      const successful = results.filter(r => r.success).length
      const failed = results.filter(r => !r.success).length
      
      setProgress({
        total: candidates.length,
        completed: results.length,
        successful,
        failed,
        results
      })
      
      setIsComplete(true)
    } catch (error) {
      setProgress(prev => ({
        ...prev,
        completed: candidates.length,
        failed: candidates.length,
        results: candidates.map(c => ({ candidateId: c.id, success: false, error: 'Erro inesperado' }))
      }))
      setIsComplete(true)
    } finally {
      setIsExecuting(false)
    }
  }, [actionType, candidates, targetStage, rejectionReason, rejectionNotes, canExecute, onExecute])

  const handleClose = useCallback(() => {
    if (isExecuting) return
    
    setIsComplete(false)
    setProgress({ total: 0, completed: 0, successful: 0, failed: 0, results: [] })
    setTargetStage('')
    setRejectionReason('')
    setRejectionNotes('')
    setTagInput('')
    onClose()
  }, [isExecuting, onClose])

  const progressPercent = progress.total > 0 ? (progress.completed / progress.total) * 100 : 0

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto rounded-md" data-testid="bulk-action-modal">
        <DialogHeader className="pb-3">
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary">
            {config.icon}
            {config.title}
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-secondary">
            {config.description}
            {jobTitle && <span className="text-lia-text-secondary"> · {jobTitle}</span>}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium text-lia-text-primary flex items-center gap-2">
                <Users className="w-3 h-3 text-lia-text-secondary" />
                Candidatos Selecionados
              </Label>
              <Chip variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-secondary">
                {candidates.length}
              </Chip>
            </div>
            
            <ScrollArea className="border rounded-xl p-2 max-h-card-lg">
              <div className="space-y-1.5">
                {displayedCandidates.map((candidate) => {
                  const result = progress.results.find(r => r.candidateId === candidate.id)
                  const avatarUrl = candidate.avatar || getRandomAvatarUrl(candidate.id, candidate.name)
                  
                  return (
                    <div
                      key={candidate.id}
                      className={cn("flex items-center gap-2 p-2 rounded-md",
                        result?.success &&"bg-status-success/10 dark:bg-status-success/10",
                        result?.success === false &&"bg-status-error/10 dark:bg-status-error/10",
                        !result &&"bg-lia-bg-secondary/50"
                      )}
                    >
                      <Avatar className="w-7 h-7">
                        <AvatarImage src={avatarUrl} />
                        <AvatarFallback className="text-micro bg-lia-bg-tertiary text-lia-text-secondary">
                          {candidate.name?.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-lia-text-primary truncate">{candidate.name}</p>
                        {candidate.email && (
                          <p className="text-xs text-lia-text-secondary truncate">{candidate.email}</p>
                        )}
                      </div>
                      {result && (
                        result.success ? (
                          <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-status-error flex-shrink-0" />
                        )
                      )}
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
            
            {candidates.length > 5 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={() => setShowAllCandidates(!showAllCandidates)}
              >
                {showAllCandidates ? (
                  <>
                    <ChevronUp className="w-3 h-3 mr-1" />
                    Mostrar menos
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3 mr-1" />
                    Ver todos os {candidates.length} candidatos
                  </>
                )}
              </Button>
            )}
          </div>

          {actionType === 'move_stage' && !isComplete && (
            <div className="space-y-2">
              <Label className="text-xs font-medium text-lia-text-primary">Etapa de Destino</Label>
              <Select value={targetStage} onValueChange={setTargetStage}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione a etapa" />
                </SelectTrigger>
                <SelectContent className="z-select">
                  {availableStages.map((stage) => (
                    <SelectItem key={stage.name} value={stage.name}>
                      {stage.displayName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {(actionType === 'add_tags' || actionType === 'remove_tags') && !isComplete && (
            <div className="space-y-2">
              <Label className="text-xs font-medium text-lia-text-primary">
                {actionType === 'add_tags' ? 'Tags para adicionar' : 'Tags para remover'}
              </Label>
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                placeholder="ex: python, senior, disponível"
                className="text-xs"
              />
              <p className="text-xs text-lia-text-tertiary">Separe múltiplas tags por vírgula</p>
            </div>
          )}

          {actionType === 'reject' && !isComplete && (
            <>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-lia-text-primary">Motivo da Reprovação</Label>
                <Select value={rejectionReason} onValueChange={setRejectionReason}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o motivo" />
                  </SelectTrigger>
                  <SelectContent className="z-select">
                    {rejectionReasonOptions.map((reason) => (
                      <SelectItem key={reason.code} value={reason.code}>
                        {reason.displayName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-lia-text-primary">Observações (opcional)</Label>
                <Textarea
                  value={rejectionNotes}
                  onChange={(e) => setRejectionNotes(e.target.value)}
                  placeholder="Adicione observações sobre a reprovação..."
                  rows={3}
                />
              </div>
            </>
          )}

          {(isExecuting || isComplete) && (
            <div className="space-y-3 p-4 bg-lia-bg-secondary/50 rounded-xl">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium">Progresso</span>
                <span className="text-lia-text-secondary">
                  {progress.completed}/{progress.total} processados
                </span>
              </div>
              <Progress value={progressPercent} className="h-2" />
              
              {isComplete && (
                <div className="flex items-center gap-4 text-xs pt-2">
                  <div className="flex items-center gap-1 text-status-success">
                    <CheckCircle className="w-4 h-4" />
                    <span>{progress.successful} sucesso</span>
                  </div>
                  {progress.failed > 0 && (
                    <div className="flex items-center gap-1 text-status-error">
                      <AlertCircle className="w-4 h-4" />
                      <span>{progress.failed} erro{progress.failed !== 1 && 's'}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="border-t border-lia-border-subtle bg-lia-bg-secondary pt-3">
          {!isComplete ? (
            <>
              <Button variant="outline" onClick={handleClose} disabled={isExecuting} className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg text-lia-text-secondary">
                Cancelar
              </Button>
              <Button
                onClick={handleExecute}
                disabled={!canExecute}
                className={cn("h-9 px-4 text-xs font-medium",
                  actionType === 'reject' 
                    ?"bg-status-error hover:bg-status-error text-white" 
                    :"bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                )}
              >
                {isExecuting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                    Processando...
                  </>
                ) : (
                  <>
                    {actionType === 'move_stage' && 'Mover Candidatos'}
                    {actionType === 'reject' && 'Reprovar Candidatos'}
                    {actionType === 'request_data' && 'Solicitar Dados'}
                    {actionType === 'send_message' && 'Enviar Mensagem'}
                    {actionType === 'export' && 'Exportar'}
                    {actionType === 'add_to_list' && 'Adicionar'}
                    {actionType === 'add_tags' && 'Adicionar Tags'}
                    {actionType === 'remove_tags' && 'Remover Tags'}
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button onClick={handleClose} className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active">
              Concluído
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
