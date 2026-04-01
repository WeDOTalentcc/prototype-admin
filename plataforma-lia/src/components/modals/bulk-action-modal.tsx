"use client"

import { useState, useCallback, useMemo } from 'react'
import { useRecruitmentStages } from '@/hooks/use-recruitment-stages'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
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
  Mail
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { RECRUITMENT_STAGES, REJECTION_REASONS, type RecruitmentStage } from '@/lib/recruitment-stages'
// REJECTION_REASONS kept as fallback for when DB sub-statuses are unavailable
import type { BulkActionType } from '@/components/ui/bulk-selection-bar'

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
}

interface ProgressState {
  total: number
  completed: number
  successful: number
  failed: number
  results: BulkActionResult[]
}

// @ts-ignore TODO: fix type — Type '{ move_stage: { title: string; description: string; icon: Element; }; reje
const ACTION_CONFIG: Record<BulkActionType, { title: string; description: string; icon: React.ReactNode }> = {
  move_stage: {
    title: 'Mover Candidatos de Etapa',
    description: 'Selecione a etapa de destino para os candidatos selecionados.',
    icon: <ArrowRight className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
  },
  reject: {
    title: 'Reprovar Candidatos',
    description: 'Informe o motivo da reprovação para os candidatos selecionados.',
    icon: <XCircle className="w-4 h-4 text-status-error" />
  },
  request_data: {
    title: 'Solicitar Dados',
    description: 'Envie uma solicitação de dados para os candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
  },
  send_message: {
    title: 'Enviar Mensagem',
    description: 'Envie uma mensagem para os candidatos selecionados.',
    icon: <Mail className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
  },
  export: {
    title: 'Exportar Candidatos',
    description: 'Exporte os dados dos candidatos selecionados.',
    icon: <FileText className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
  },
  add_to_list: {
    title: 'Adicionar à Lista',
    description: 'Adicione os candidatos selecionados a uma lista.',
    icon: <Users className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
  },
}

const getRandomAvatarUrl = (candidateId: string, name: string): string => {
  let hash = 0
  const str = candidateId + name
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  const avatarIndex = Math.abs(hash % 70) + 1
  const gender = Math.abs(hash % 2) === 0 ? 'men' : 'women'
  return `https://randomuser.me/api/portraits/${gender}/${avatarIndex}.jpg`
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

  // Sub-statuses do estágio "rejected" vindos do DB; fallback para REJECTION_REASONS estático
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
      default:
        return true
    }
  }, [actionType, targetStage, rejectionReason, isExecuting])

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
    onClose()
  }, [isExecuting, onClose])

  const progressPercent = progress.total > 0 ? (progress.completed / progress.total) * 100 : 0

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto rounded-md dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <DialogHeader className="border-b border-lia-border-subtle dark:border-lia-border-subtle pb-3">
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">
            {config.icon}
            {config.title}
          </DialogTitle>
          <DialogDescription className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
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
              <Badge variant="secondary" className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary">
                {candidates.length}
              </Badge>
            </div>
            
            <ScrollArea className="border rounded-md p-2 max-h-card-lg">
              <div className="space-y-1.5">
                {displayedCandidates.map((candidate) => {
                  const result = progress.results.find(r => r.candidateId === candidate.id)
                  const avatarUrl = candidate.avatar || getRandomAvatarUrl(candidate.id, candidate.name)
                  
                  return (
                    <div
                      key={candidate.id}
                      className={cn(
                        "flex items-center gap-2 p-2 rounded-md",
                        result?.success && "bg-status-success/10 dark:bg-status-success/10",
                        result?.success === false && "bg-status-error/10 dark:bg-status-error/10",
                        !result && "bg-gray-50 dark:bg-lia-bg-secondary/50"
                      )}
                    >
                      <Avatar className="w-7 h-7">
                        <AvatarImage src={avatarUrl} />
                        <AvatarFallback className="text-micro bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-tertiary">
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
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
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

        <DialogFooter className="border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle pt-3">
          {!isComplete ? (
            <>
              <Button variant="outline" onClick={handleClose} disabled={isExecuting} className="h-9 px-4 text-xs font-medium bg-white border border-lia-border-default hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-gray-700 text-lia-text-secondary dark:text-lia-text-primary">
                Cancelar
              </Button>
              <Button
                onClick={handleExecute}
                disabled={!canExecute}
                className={cn(
                  "h-9 px-4 text-xs font-medium",
                  actionType === 'reject' 
                    ? "bg-status-error hover:bg-status-error text-white" 
                    : "bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
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
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button onClick={handleClose} className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200">
              Concluído
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
