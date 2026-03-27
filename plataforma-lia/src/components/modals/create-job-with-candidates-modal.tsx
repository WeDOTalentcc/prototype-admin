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

const DEFAULT_STAGES = [
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
      className="fixed inset-0 z-[9999] flex items-center justify-center"
     
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-job-with-candidates-modal-title"
    >
      <div
        className="absolute inset-0 bg-black/50 dark:bg-gray-950/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={modalRef}
        className="relative bg-gray-900 border border-gray-700 rounded-md w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col"
      >
        <div className="border-b border-gray-700 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-gray-100 dark:bg-gray-800">
                <Brain className="w-5 h-5 text-wedo-cyan" />
              </div>
              <div>
                <h2 
                  id="create-job-with-candidates-modal-title" 
                  className="text-sm font-semibold text-gray-100"
                 
                >
                  Criar vaga com candidatos
                </h2>
                <p className="text-xs text-gray-400">
                  Os candidatos serão adicionados após a criação
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
              aria-label="Fechar modal"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-5 space-y-5 flex-1 overflow-hidden flex flex-col">
          <div className="bg-gray-800/50 border border-gray-700 rounded-md p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-xs font-medium text-gray-200">
                {candidateCount} candidato{candidateCount !== 1 ? 's' : ''} selecionado{candidateCount !== 1 ? 's' : ''}
              </span>
            </div>
            
            <p className="text-xs text-gray-400 mb-3">
              Serão adicionados automaticamente à vaga após sua criação
            </p>
            
            {displayNames.length > 0 && (
              <ScrollArea className="max-h-[140px]">
                <div className="space-y-2">
                  {displayNames.map((name, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-2 p-2 bg-gray-800 rounded-md border border-gray-700"
                    >
                      <Avatar className="w-6 h-6">
                        <AvatarFallback className="text-micro bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                          {getInitials(name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-xs text-gray-200 truncate flex-1">
                        {name}
                      </span>
                      <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    </div>
                  ))}
                  {remainingCount > 0 && (
                    <div className="text-xs text-gray-500 text-center py-1">
                      +{remainingCount} candidato{remainingCount !== 1 ? 's' : ''}
                    </div>
                  )}
                </div>
              </ScrollArea>
            )}
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-medium text-gray-300">
                Etapa inicial
              </Label>
              <Select value={selectedStage} onValueChange={setSelectedStage}>
                <SelectTrigger className="w-full bg-gray-800 border-gray-700 text-gray-200 text-xs focus:ring-gray-900 focus:ring-offset-0">
                  <SelectValue placeholder="Selecione a etapa" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {DEFAULT_STAGES.map((stage) => (
                    <SelectItem 
                      key={stage} 
                      value={stage} 
                      className="text-xs text-gray-200 focus:bg-gray-700 focus:text-gray-100"
                    >
                      {stage}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {hasComments && (
              <div className="flex items-start space-x-3 p-3 bg-gray-800/50 rounded-md border border-gray-700">
                <Checkbox
                  id="include-comments"
                  checked={includeComments}
                  onCheckedChange={(checked) => setIncludeComments(checked === true)}
                  className="mt-0.5 border-gray-600 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="include-comments"
                    className="text-xs font-medium text-gray-200 cursor-pointer flex items-center gap-1.5"
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-gray-400" />
                    Incluir comentários como notas
                  </Label>
                  <p className="text-micro text-gray-500 mt-1">
                    Os feedbacks serão adicionados como notas iniciais dos candidatos
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-100 border border-gray-200 rounded-md p-3 mt-auto">
            <div className="flex items-start gap-2">
              <Briefcase className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                  Próximo passo
                </p>
                <p className="text-micro text-gray-400 mt-1">
                  A LIA vai te guiar na criação da vaga. Após finalizar, os candidatos serão adicionados automaticamente.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-700 p-4 flex items-center justify-end gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-transparent border-gray-600 text-gray-300 hover:bg-gray-800 hover:text-gray-100 hover:border-gray-500"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleProceed}
            className="h-9 px-5 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
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
