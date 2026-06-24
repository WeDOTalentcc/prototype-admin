"use client"

import { useState, useEffect, useRef } from "react"
import { createPortal } from "react-dom"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"
import { 
  Briefcase, 
  Users, 
  Check, 
  X, 
  MessageSquare,
  ChevronRight,
  Brain
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles } from '@/lib/design-tokens'
import { usePipelineStageTemplates, flattenTemplates } from "@/hooks/pipeline/use-pipeline-stage-templates"

export interface CreateJobWithCandidatesModalProps {
  open: boolean
  onClose: () => void
  candidateIds: string[]
  candidateNames?: string[]
  feedbackComments?: Map<string, string>
  sharedSearchId?: string
  onSuccess?: (jobId: string) => void
  onProceed?: (config: CreateJobWithCandidatesConfig) => void
}

export interface CreateJobWithCandidatesConfig {
  candidateIds: string[]
  candidateNames: string[]
  initialStage: string
  includeComments: boolean
  feedbackComments?: Map<string, string>
  sharedSearchId?: string
}

// Audit 2026-05-20 Sprint 2 F4: catalogo dinamico canonical via
// usePipelineStageTemplates. Fallback PT-BR mantido apenas para o caso
// de loading/error (resiliencia UX).
const DEFAULT_STAGES_FALLBACK = [
  'Triagem',
  'Entrevista RH',
  'Entrevista Técnica',
  'Entrevista Gestor',
  'Proposta'
]

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export function CreateJobWithCandidatesModal({
  open,
  onClose,
  candidateIds,
  candidateNames = [],
  feedbackComments,
  sharedSearchId,
  onSuccess,
  onProceed
}: CreateJobWithCandidatesModalProps) {
  const [mounted, setMounted] = useState(false)
  const [selectedStage, setSelectedStage] = useState('Triagem')
  const [includeComments, setIncludeComments] = useState(!!feedbackComments && feedbackComments.size > 0)
  const modalRef = useRef<HTMLDivElement>(null)

  // Sprint 2 F4 canonical: catalogo dinamico per-tenant (master + custom).
  // Filtra is_default_in_pipeline=true, ordena por data.order asc.
  const { templates: stageTemplates, isLoading: stagesLoading } = usePipelineStageTemplates({ includeMaster: true })
  const availableStages = (() => {
    if (stagesLoading || !stageTemplates.length) {
      return DEFAULT_STAGES_FALLBACK
    }
    const flat = flattenTemplates(stageTemplates)
      .filter((s) => s.is_default_in_pipeline)
      .sort((a, b) => a.order - b.order)
    if (!flat.length) return DEFAULT_STAGES_FALLBACK
    return flat.map((s) => s.display_name)
  })()

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  useEffect(() => {
    if (open) {
      setSelectedStage('Triagem')
      setIncludeComments(!!feedbackComments && feedbackComments.size > 0)
    }
  }, [open, feedbackComments])

  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = originalOverflow
    }
  }, [open])

  const handleProceed = () => {
    const config: CreateJobWithCandidatesConfig = {
      candidateIds,
      candidateNames,
      initialStage: selectedStage,
      includeComments,
      feedbackComments: includeComments ? feedbackComments : undefined,
      sharedSearchId
    }
    
    onProceed?.(config)
    onClose()
  }

  const candidateCount = candidateIds.length
  const displayNames = candidateNames.slice(0, 8)
  const remainingCount = candidateCount > 8 ? candidateCount - 8 : 0
  const hasComments = feedbackComments && feedbackComments.size > 0

  if (!open || !mounted) return null

  const modalContent = (
    <div
      className="fixed inset-0 z-modal flex items-center justify-center"
     
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-job-with-candidates-modal-title"
    >
      <div
        className="absolute inset-0 bg-lia-overlay/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={modalRef}
        className="relative bg-lia-btn-primary-bg border border-lia-border-medium rounded-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col"
      >
        <div className=" p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-lia-bg-tertiary">
                <Brain className="w-5 h-5 text-wedo-cyan" />
              </div>
              <div>
                <h2 
                  id="create-job-with-candidates-modal-title" 
                  className="text-sm font-semibold text-lia-text-inverse"
                 
                >
                  Criar vaga com candidatos
                </h2>
                <p className="text-xs text-lia-text-muted">
                  Os candidatos serão adicionados após a criação
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-lia-btn-primary-hover text-lia-text-disabled hover:text-lia-text-inverse transition-colors motion-reduce:transition-none"
              aria-label="Fechar modal"
              data-dismiss="true"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-5 space-y-5 flex-1 overflow-hidden flex flex-col">
          <div className="bg-lia-btn-primary-bg/50 border border-lia-border-medium rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-4 h-4 text-lia-text-secondary" />
              <span className="text-xs font-medium text-lia-text-inverse">
                {candidateCount} candidato{candidateCount !== 1 ? 's' : ''} selecionado{candidateCount !== 1 ? 's' : ''}
              </span>
            </div>
            
            <p className="text-xs text-lia-text-muted mb-3">
              Serão adicionados automaticamente à vaga após sua criação
            </p>
            
            {displayNames.length > 0 && (
              <ScrollArea className="max-h-[140px]">
                <div className="space-y-2">
                  {displayNames.map((name, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-2 p-2 bg-lia-btn-primary-bg rounded-xl border border-lia-border-medium"
                    >
                      <Avatar className="w-6 h-6">
                        <AvatarFallback className="text-micro bg-lia-bg-tertiary text-lia-text-secondary">
                          {getInitials(name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-xs text-lia-text-inverse truncate flex-1">
                        {name}
                      </span>
                      <Check className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                    </div>
                  ))}
                  {remainingCount > 0 && (
                    <div className="text-xs text-lia-text-tertiary text-center py-1">
                      +{remainingCount} candidato{remainingCount !== 1 ? 's' : ''}
                    </div>
                  )}
                </div>
              </ScrollArea>
            )}
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-medium text-lia-text-tertiary">
                Etapa inicial
              </Label>
              <Select value={selectedStage} onValueChange={setSelectedStage}>
                <SelectTrigger className="w-full bg-lia-btn-primary-bg border-lia-border-medium text-lia-text-inverse text-xs focus:ring-lia-btn-primary-bg focus:ring-offset-0">
                  <SelectValue placeholder="Selecione a etapa" />
                </SelectTrigger>
                <SelectContent className="bg-lia-btn-primary-bg border-lia-border-medium">
                  {availableStages.map((stage) => (
                    <SelectItem
                      key={stage}
                      value={stage}
                      className="text-xs text-lia-text-inverse focus:bg-lia-btn-primary-bg focus:text-lia-text-inverse"
                    >
                      {stage}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {hasComments && (
              <div className="flex items-start space-x-3 p-3 bg-lia-btn-primary-bg/50 rounded-xl border border-lia-border-medium">
                <Checkbox
                  id="include-comments"
                  checked={includeComments}
                  onCheckedChange={(checked) => setIncludeComments(checked === true)}
                  className="mt-0.5 border-lia-border-medium data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="include-comments"
                    className="text-xs font-medium text-lia-text-inverse cursor-pointer flex items-center gap-1.5"
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-lia-text-muted" />
                    Incluir comentários como notas
                  </Label>
                  <p className="text-micro text-lia-text-tertiary mt-1">
                    Os feedbacks serão adicionados como notas iniciais dos candidatos
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="bg-lia-bg-tertiary border border-lia-border-subtle rounded-xl p-3 mt-auto">
            <div className="flex items-start gap-2">
              <Briefcase className="w-4 h-4 text-lia-text-secondary flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-lia-text-secondary font-medium">
                  Próximo passo
                </p>
                <p className="text-micro text-lia-text-muted mt-1">
                  A IA vai te guiar na criação da vaga. Após finalizar, os candidatos serão adicionados automaticamente.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-lia-border-medium p-4 flex items-center justify-end gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-transparent border-lia-border-medium text-lia-text-tertiary hover:bg-lia-btn-primary-hover hover:text-lia-text-inverse hover:border-lia-border-medium"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleProceed}
            className="h-9 px-5 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            Criar Vaga
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
