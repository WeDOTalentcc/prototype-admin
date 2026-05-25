'use client'

import { useState, useCallback, memo } from 'react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { 
  X, 
  ChevronDown, 
  RefreshCw, 
  Briefcase, 
  Mail, 
  PlayCircle,
  FileSpreadsheet, 
  Trash2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react'
import liaApi, {
  BulkOperationResult,
  JobVacancy,
  EmailTemplate
} from '@/services/lia-api'
import { ShareSearchModal } from '@/components/modals/share-search-modal'
import { Share2 } from 'lucide-react'
import { toast } from "sonner"
interface BulkActionsBarProps {
  selectedCount: number
  selectedIds: string[]
  onClearSelection: () => void
  onActionComplete: () => void
  jobVacancies?: JobVacancy[]
  emailTemplates?: EmailTemplate[]
}

const STATUS_OPTIONS = [
  { value: 'new', label: 'Novo', color: 'bg-lia-bg-tertiary text-lia-text-primary' },
  { value: 'screening', label: 'Em Triagem', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-wedo-cyan-dark' },
  { value: 'interview', label: 'Entrevista', color: 'bg-wedo-purple/15 text-wedo-purple' },
  { value: 'offer', label: 'Proposta', color: 'bg-status-warning/15 text-status-warning' },
  { value: 'hired', label: 'Contratado', color: 'bg-status-success/15 text-status-success' },
  { value: 'rejected', label: 'Recusado', color: 'bg-status-error/15 text-status-error' },
]

const BulkActionsBar = memo(function BulkActionsBar({
  selectedCount,
  selectedIds,
  onClearSelection,
  onActionComplete,
  jobVacancies = [],
  emailTemplates = [],
}: BulkActionsBarProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [progressModal, setProgressModal] = useState(false)
  const [progressValue, setProgressValue] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [operationResult, setOperationResult] = useState<BulkOperationResult | null>(null)
  
  const [confirmDeleteModal, setConfirmDeleteModal] = useState(false)
  const [assignJobModal, setAssignJobModal] = useState(false)
  const [sendEmailModal, setSendEmailModal] = useState(false)
  const [confirmScreeningModal, setConfirmScreeningModal] = useState(false)
  const [shareSelectionModal, setShareSelectionModal] = useState(false)
  
  const [selectedJobId, setSelectedJobId] = useState<string>('')
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [exportFormat, setExportFormat] = useState<'csv' | 'xlsx'>('csv')

  const showResultToast = useCallback((result: BulkOperationResult, action: string) => {
    if (result.success && result.failed === 0) {
      toast.success('Operação concluída', { description: `${action}: ${result.processed} candidato(s) processado(s) com sucesso.` })
    } else if (result.failed > 0) {
      toast.error('Operação parcial', { description: `${action}: ${result.processed - result.failed} sucesso, ${result.failed} erro(s).` })
    }
  }, [])

  const handleUpdateStatus = useCallback(async (newStatus: string) => {
    if (selectedIds.length === 0) return
    
    setIsProcessing(true)
    setProgressModal(true)
    setProgressValue(10)
    setProgressMessage(`Atualizando status para "${STATUS_OPTIONS.find(s => s.value === newStatus)?.label}"...`)
    
    try {
      const result = await liaApi.bulkUpdateStatus({
        candidate_ids: selectedIds,
        new_status: newStatus,
      })
      
      setProgressValue(100)
      setOperationResult(result)
      showResultToast(result, 'Atualização de status')
      
      if (result.success) {
        setTimeout(() => {
          setProgressModal(false)
          setOperationResult(null)
          onClearSelection()
          onActionComplete()
        }, 1500)
      }
    } catch (error: unknown) {
      toast.error('Erro na operação', { description: error instanceof Error ? error.message : 'Falha ao atualizar status.' })
      setProgressModal(false)
    } finally {
      setIsProcessing(false)
    }
  }, [selectedIds, onClearSelection, onActionComplete, showResultToast])

  const handleAssignJob = useCallback(async () => {
    if (!selectedJobId || selectedIds.length === 0) return
    
    setAssignJobModal(false)
    setIsProcessing(true)
    setProgressModal(true)
    setProgressValue(10)
    setProgressMessage('Atribuindo candidatos à vaga...')
    
    try {
      const result = await liaApi.bulkAssignJob({
        candidate_ids: selectedIds,
        job_id: selectedJobId,
      })
      
      setProgressValue(100)
      setOperationResult(result)
      showResultToast(result, 'Atribuição à vaga')
      
      if (result.success) {
        setTimeout(() => {
          setProgressModal(false)
          setOperationResult(null)
          setSelectedJobId('')
          onClearSelection()
          onActionComplete()
        }, 1500)
      }
    } catch (error: unknown) {
      toast.error('Erro na operação', { description: error instanceof Error ? error.message : 'Falha ao atribuir à vaga.' })
      setProgressModal(false)
    } finally {
      setIsProcessing(false)
    }
  }, [selectedJobId, selectedIds, onClearSelection, onActionComplete, showResultToast])

  const handleSendEmail = useCallback(async () => {
    if (!selectedTemplateId || selectedIds.length === 0) return
    
    setSendEmailModal(false)
    setIsProcessing(true)
    setProgressModal(true)
    setProgressValue(10)
    setProgressMessage('Enviando emails para candidatos...')
    
    try {
      const result = await liaApi.bulkSendEmail({
        candidate_ids: selectedIds,
        template_id: selectedTemplateId,
      })
      
      setProgressValue(100)
      setOperationResult(result)
      showResultToast(result, 'Envio de emails')
      
      if (result.success) {
        setTimeout(() => {
          setProgressModal(false)
          setOperationResult(null)
          setSelectedTemplateId('')
          onClearSelection()
          onActionComplete()
        }, 1500)
      }
    } catch (error: unknown) {
      toast.error('Erro na operação', { description: error instanceof Error ? error.message : 'Falha ao enviar emails.' })
      setProgressModal(false)
    } finally {
      setIsProcessing(false)
    }
  }, [selectedTemplateId, selectedIds, onClearSelection, onActionComplete, showResultToast])

  const handleStartScreening = useCallback(async () => {
    if (selectedIds.length === 0) return
    
    setConfirmScreeningModal(false)
    setIsProcessing(true)
    setProgressModal(true)
    setProgressValue(10)
    setProgressMessage('Iniciando triagem dos candidatos...')
    
    try {
      const result = await liaApi.bulkStartScreening({
        candidate_ids: selectedIds,
      })
      
      setProgressValue(100)
      setOperationResult(result)
      showResultToast(result, 'Início de triagem')
      
      if (result.success) {
        setTimeout(() => {
          setProgressModal(false)
          setOperationResult(null)
          onClearSelection()
          onActionComplete()
        }, 1500)
      }
    } catch (error: unknown) {
      toast.error('Erro na operação', { description: error instanceof Error ? error.message : 'Falha ao iniciar triagem.' })
      setProgressModal(false)
    } finally {
      setIsProcessing(false)
    }
  }, [selectedIds, onClearSelection, onActionComplete, showResultToast])

  const handleExport = useCallback(async (format: 'csv' | 'xlsx') => {
    if (selectedIds.length === 0) return
    
    setIsProcessing(true)
    setProgressModal(true)
    setProgressValue(10)
    setProgressMessage(`Exportando candidatos para ${format.toUpperCase()}...`)
    
    try {
      const result = await liaApi.bulkExport({
        candidate_ids: selectedIds,
        format,
      })
      
      if (result instanceof Blob) {
        const url = window.URL.createObjectURL(result)
        const a = document.createElement('a')
        a.href = url
        a.download = `candidatos_${new Date().toISOString().split('T')[0]}.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        toast.success('Exportação concluída', { description: `${selectedIds.length} candidato(s) exportado(s) com sucesso.` })
      } else {
        showResultToast(result as BulkOperationResult, 'Exportação')
      }
      
      setProgressValue(100)
      setTimeout(() => {
        setProgressModal(false)
        setOperationResult(null)
      }, 1000)
    } catch (error: unknown) {
      toast.error('Erro na exportação', { description: error instanceof Error ? error.message : 'Falha ao exportar candidatos.' })
      setProgressModal(false)
    } finally {
      setIsProcessing(false)
    }
  }, [selectedIds, showResultToast])

  const handleDelete = useCallback(async () => {
    if (selectedIds.length === 0) return
    
    setConfirmDeleteModal(false)
    setIsProcessing(true)
    setProgressModal(true)
    setProgressValue(10)
    setProgressMessage('Excluindo candidatos selecionados...')
    
    try {
      const result = await liaApi.bulkDelete({
        candidate_ids: selectedIds,
        hard_delete: false,
      })
      
      setProgressValue(100)
      setOperationResult(result)
      showResultToast(result, 'Exclusão')
      
      if (result.success) {
        setTimeout(() => {
          setProgressModal(false)
          setOperationResult(null)
          onClearSelection()
          onActionComplete()
        }, 1500)
      }
    } catch (error: unknown) {
      toast.error('Erro na operação', { description: error instanceof Error ? error.message : 'Falha ao excluir candidatos.' })
      setProgressModal(false)
    } finally {
      setIsProcessing(false)
    }
  }, [selectedIds, onClearSelection, onActionComplete, showResultToast])

  if (selectedCount === 0) return null

  return (
    <>
      <div 
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-300"
       
      >
        <div className="flex items-center gap-3 px-4 py-3 bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-xl border border-lia-border-strong">
          <div className="flex items-center gap-2 pr-4">
            <span className="text-sm font-medium" aria-live="polite" aria-atomic="true">
              {selectedCount} candidato{selectedCount !== 1 ? 's' : ''} selecionado{selectedCount !== 1 ? 's' : ''}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-inverse text-lia-text-secondary hover:text-white"
              onClick={onClearSelection}
              disabled={isProcessing}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm"
                className="text-white hover:bg-lia-bg-inverse"
                disabled={isProcessing}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Alterar Status
                <ChevronDown className="h-4 w-4 ml-1" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-48">
              {STATUS_OPTIONS.map((status) => (
                <DropdownMenuItem
                  key={status.value}
                  onClick={() => handleUpdateStatus(status.value)}
                >
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-micro font-medium ${status.color} mr-2`}>
                    {status.label}
                  </span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Button 
            variant="ghost" 
            size="sm"
            className="text-white hover:bg-lia-bg-inverse"
            onClick={() => setAssignJobModal(true)}
            disabled={isProcessing || jobVacancies.length === 0}
          >
            <Briefcase className="h-4 w-4 mr-2" />
            Atribuir à Vaga
          </Button>

          <Button 
            variant="ghost" 
            size="sm"
            className="text-white hover:bg-lia-bg-inverse"
            onClick={() => setSendEmailModal(true)}
            disabled={isProcessing || emailTemplates.length === 0}
          >
            <Mail className="h-4 w-4 mr-2" />
            Enviar Email
          </Button>

          <Button 
            variant="ghost" 
            size="sm"
            className="text-white hover:bg-lia-bg-inverse"
            onClick={() => setConfirmScreeningModal(true)}
            disabled={isProcessing}
          >
            <PlayCircle className="h-4 w-4 mr-2" />
            Iniciar Triagem
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm"
                className="text-white hover:bg-lia-bg-inverse"
                disabled={isProcessing}
              >
                <FileSpreadsheet className="h-4 w-4 mr-2" />
                Exportar
                <ChevronDown className="h-4 w-4 ml-1" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem onClick={() => handleExport('csv')}>
                Exportar CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('xlsx')}>
                Exportar Excel
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-lia-bg-inverse"
            onClick={() => setShareSelectionModal(true)}
            disabled={isProcessing}
          >
            <Share2 className="h-4 w-4 mr-2" />
            Compartilhar Seleção
          </Button>

          

          <Button
            variant="ghost"
            size="sm"
            className="text-status-error hover:text-status-error hover:bg-status-error/30"
            onClick={() => setConfirmDeleteModal(true)}
            disabled={isProcessing}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Excluir
          </Button>
        </div>
      </div>

      <Dialog open={confirmDeleteModal} onOpenChange={setConfirmDeleteModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-status-error">
              <AlertTriangle className="h-5 w-5" />
              Confirmar Exclusão
            </DialogTitle>
            <DialogDescription>
              Você está prestes a excluir <strong>{selectedCount} candidato{selectedCount !== 1 ? 's' : ''}</strong>. 
              Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setConfirmDeleteModal(false)}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
            >
              Excluir Candidatos
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={assignJobModal} onOpenChange={setAssignJobModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-lia-text-secondary" />
              Atribuir à Vaga
            </DialogTitle>
            <DialogDescription>
              Selecione uma vaga para atribuir os {selectedCount} candidato{selectedCount !== 1 ? 's' : ''} selecionado{selectedCount !== 1 ? 's' : ''}.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedJobId} onValueChange={setSelectedJobId}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione uma vaga" />
              </SelectTrigger>
              <SelectContent>
                {jobVacancies.map((job) => (
                  <SelectItem key={job.id} value={job.id}>
                    {job.title} {job.department ? `- ${job.department}` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setAssignJobModal(false)
                setSelectedJobId('')
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleAssignJob}
              disabled={!selectedJobId}
            >
              Atribuir Candidatos
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={sendEmailModal} onOpenChange={setSendEmailModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-lia-text-secondary" />
              Enviar Email
            </DialogTitle>
            <DialogDescription>
              Selecione um modelo de email para enviar aos {selectedCount} candidato{selectedCount !== 1 ? 's' : ''} selecionado{selectedCount !== 1 ? 's' : ''}.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedTemplateId} onValueChange={setSelectedTemplateId}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um modelo" />
              </SelectTrigger>
              <SelectContent>
                {emailTemplates.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setSendEmailModal(false)
                setSelectedTemplateId('')
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSendEmail}
              disabled={!selectedTemplateId}
            >
              Enviar Emails
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmScreeningModal} onOpenChange={setConfirmScreeningModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <PlayCircle className="h-5 w-5 text-status-success" />
              Iniciar Triagem
            </DialogTitle>
            <DialogDescription>
              Você deseja iniciar a triagem automática para {selectedCount} candidato{selectedCount !== 1 ? 's' : ''}?
              Isso irá enviar convites de triagem por email.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setConfirmScreeningModal(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleStartScreening}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              Iniciar Triagem
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={progressModal} onOpenChange={(open) => {
        if (!isProcessing) setProgressModal(open)
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {operationResult ? (
                operationResult.failed === 0 ? (
                  <span className="flex items-center gap-2 text-status-success">
                    <CheckCircle className="h-5 w-5" />
                    Operação Concluída
                  </span>
                ) : (
                  <span className="flex items-center gap-2 text-status-warning">
                    <AlertTriangle className="h-5 w-5" />
                    Operação Parcial
                  </span>
                )
              ) : (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none" />
                  Processando...
                </span>
              )}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <Progress value={progressValue} className="h-2" />
            <p className="text-sm text-lia-text-secondary">{progressMessage}</p>
            
            {operationResult && (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-status-success" />
                  <span>{operationResult.processed - operationResult.failed} processado(s) com sucesso</span>
                </div>
                {operationResult.failed > 0 && (
                  <>
                    <div className="flex items-center gap-2 text-status-error">
                      <XCircle className="h-4 w-4" />
                      <span>{operationResult.failed} erro(s)</span>
                    </div>
                    {operationResult.errors && operationResult.errors.length > 0 && (
                      <div className="mt-2 p-2 bg-status-error/10 rounded-xl border border-status-error/30 max-h-32 overflow-y-auto">
                        {operationResult.errors.slice(0, 5).map((err, idx) => (
                          <p key={idx} className="text-xs text-status-error">
                            ID {err.id}: {err.error}
                          </p>
                        ))}
                        {operationResult.errors.length > 5 && (
                          <p className="text-xs text-status-error mt-1">
                            + {operationResult.errors.length - 5} erro(s) adicional(is)
                          </p>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
          {operationResult && operationResult.failed > 0 && (
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setProgressModal(false)
                  setOperationResult(null)
                  onClearSelection()
                  onActionComplete()
                }}
              >
                Fechar
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal Compartilhar Seleção (H.3b) */}
      <ShareSearchModal
        open={shareSelectionModal}
        onClose={() => setShareSelectionModal(false)}
        shareType="list"
        title={`Seleção de ${selectedCount} candidatos`}
        candidateIds={selectedIds}
        candidateCount={selectedCount}
      />
    </>
  )
})

export default BulkActionsBar

// Vue migration prep: displayName for DevTools compatibility
BulkActionsBar.displayName = 'BulkActionsBar'
