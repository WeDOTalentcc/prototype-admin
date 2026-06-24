"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { createPortal } from "react-dom"
import { liaApi, JobVacancy } from "@/services/lia-api"
import { formatJobLocation } from "@/lib/jobs/location"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { 
  Briefcase, 
  Search, 
  Loader2, 
  Users, 
  Check, 
  Building2, 
  MapPin, 
  X, 
  Bell, 
  MessageSquare,
  ChevronRight,
  AlertTriangle,
  ExternalLink
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { toast } from "sonner"
import { usePipelineStageTemplates, flattenTemplates } from "@/hooks/pipeline/use-pipeline-stage-templates"

const MAX_BULK_CANDIDATES = 100

export interface AddToJobModalProps {
  open: boolean
  onClose: () => void
  candidateIds: string[]
  candidateNames?: string[]
  feedbackComments?: Map<string, string>
  sharedSearchId?: string
  onSuccess?: () => void
  onNavigateToJob?: (jobId: string) => void
}

interface JobDisplay {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
  candidates_count?: number
  pipeline_stages?: string[]
  existing_candidate_ids?: string[]
}

// Audit 2026-05-20 Sprint 2 F4: catalogo dinamico canonical via
// usePipelineStageTemplates. Fallback PT-BR mantido apenas para o caso
// de loading/error/JobVacancy sem pipeline_stages persistidas.
const DEFAULT_STAGES_FALLBACK = [
  'Triagem',
  'Entrevista RH',
  'Entrevista Técnica',
  'Entrevista Gestor',
  'Proposta',
  'Contratado'
]

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export function AddToJobModal({
  open,
  onClose,
  candidateIds,
  candidateNames = [],
  feedbackComments,
  sharedSearchId,
  onSuccess,
  onNavigateToJob
}: AddToJobModalProps) {
const [jobs, setJobs] = useState<JobDisplay[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [duplicateIds, setDuplicateIds] = useState<string[]>([])
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  
  const [selectedStage, setSelectedStage] = useState('Triagem')
  const [notifyManager, setNotifyManager] = useState(false)
  const [includeComments, setIncludeComments] = useState(!!feedbackComments && feedbackComments.size > 0)

  // Sprint 2 F4 canonical: catalogo dinamico per-tenant (master + custom).
  // Filtra is_default_in_pipeline=true, ordena por data.order asc.
  const { templates: stageTemplates, isLoading: stagesLoading } = usePipelineStageTemplates({ includeMaster: true })
  const dynamicDefaultStages = useMemo(() => {
    if (stagesLoading || !stageTemplates.length) return DEFAULT_STAGES_FALLBACK
    const flat = flattenTemplates(stageTemplates)
      .filter((s) => s.is_default_in_pipeline)
      .sort((a, b) => a.order - b.order)
    if (!flat.length) return DEFAULT_STAGES_FALLBACK
    return flat.map((s) => s.display_name)
  }, [stageTemplates, stagesLoading])

  const searchInputRef = useRef<HTMLInputElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  const isOverLimit = candidateIds.length > MAX_BULK_CANDIDATES
  const effectiveCandidateIds = isOverLimit ? candidateIds.slice(0, MAX_BULK_CANDIDATES) : candidateIds

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  useEffect(() => {
    if (open) {
      loadJobs()
      setSelectedJobId(null)
      setSearchTerm('')
      setSelectedStage('Triagem')
      setNotifyManager(false)
      setIncludeComments(!!feedbackComments && feedbackComments.size > 0)
      setDuplicateIds([])
      setSkipDuplicates(true)
      setTimeout(() => searchInputRef.current?.focus(), 100)
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

  const checkDuplicates = useCallback(async (jobId: string) => {
    try {
      const job = jobs.find(j => j.id === jobId)
      if (job?.existing_candidate_ids) {
        const dupes = effectiveCandidateIds.filter(id => job.existing_candidate_ids!.includes(id))
        setDuplicateIds(dupes)
      } else {
        try {
          const response = await fetch(`/api/backend-proxy/search/vacancy/${jobId}/check-duplicates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_ids: effectiveCandidateIds })
          })
          if (response.ok) {
            const data = await response.json()
            setDuplicateIds(data.duplicate_ids || [])
          } else {
            setDuplicateIds([])
          }
        } catch {
          setDuplicateIds([])
        }
      }
    } catch {
      setDuplicateIds([])
    }
  }, [jobs, effectiveCandidateIds, setDuplicateIds])

  useEffect(() => {
    if (selectedJobId) {
      checkDuplicates(selectedJobId)
    } else {
      setDuplicateIds([])
    }
  }, [selectedJobId, candidateIds, checkDuplicates])

  const loadJobs = async () => {
    setIsLoading(true)
    try {
      const response = await liaApi.listJobVacancies('open', 0, 100)
      if (response.items && response.items.length > 0) {
        const mapped: JobDisplay[] = response.items.map((jv: JobVacancy) => ({
          id: jv.id,
          title: jv.title,
          department: jv.department,
          location: formatJobLocation(jv.location),
          status: jv.status,
          candidates_count: (jv as JobVacancy & { candidates_count?: number; funnel_data?: { total?: number } }).candidates_count || (jv as JobVacancy & { candidates_count?: number; funnel_data?: { total?: number } }).funnel_data?.total || 0,
          pipeline_stages: (jv as JobVacancy & { pipeline_stages?: string[]; candidate_ids?: string[] }).pipeline_stages || dynamicDefaultStages,
          existing_candidate_ids: (jv as JobVacancy & { pipeline_stages?: string[]; candidate_ids?: string[] }).candidate_ids || []
        }))
        setJobs(mapped)
      } else {
        setJobs([])
      }
    } catch (error) {
      setJobs([])
    } finally {
      setIsLoading(false)
    }
  }

  const filteredJobs = useMemo(() => {
    if (!searchTerm.trim()) return jobs
    const term = searchTerm.toLowerCase()
    return jobs.filter(j =>
      j.title?.toLowerCase().includes(term) ||
      j.department?.toLowerCase().includes(term) ||
      j.location?.toLowerCase().includes(term)
    )
  }, [jobs, searchTerm])

  const selectedJob = useMemo(() => {
    return jobs.find(j => j.id === selectedJobId)
  }, [jobs, selectedJobId])

  const availableStages = useMemo(() => {
    return selectedJob?.pipeline_stages || dynamicDefaultStages
  }, [selectedJob, dynamicDefaultStages])

  const finalCandidateIds = useMemo(() => {
    if (skipDuplicates && duplicateIds.length > 0) {
      return effectiveCandidateIds.filter(id => !duplicateIds.includes(id))
    }
    return effectiveCandidateIds
  }, [effectiveCandidateIds, duplicateIds, skipDuplicates])

  const handleSubmit = async () => {
    if (!selectedJobId) {
      toast.error("Selecione uma vaga")
      return
    }

    if (finalCandidateIds.length === 0) {
      toast.error("Todos os candidatos já estão nesta vaga")
      return
    }

    setIsSubmitting(true)
    try {
      if (sharedSearchId) {
        await liaApi.addSharedCandidatesToJob(sharedSearchId, {
          job_id: selectedJobId,
          candidate_ids: finalCandidateIds,
          include_notes: includeComments
        })
      } else {
        const response = await fetch(`/api/backend-proxy/search/vacancy/${selectedJobId}/add-candidates`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_ids: finalCandidateIds,
            stage: selectedStage.toLowerCase(),
            notify_manager: notifyManager,
            include_notes: includeComments,
            notes: includeComments && feedbackComments 
              ? Object.fromEntries(feedbackComments) 
              : undefined
          })
        })
        if (!response.ok) {
          throw new Error('Falha ao adicionar candidatos')
        }
      }

      const jobTitle = selectedJob?.title || 'vaga'
      const addedCount = finalCandidateIds.length
      const skippedCount = duplicateIds.length
      const skippedMsg = skippedCount > 0 && skipDuplicates
        ? ` (${skippedCount} duplicado${skippedCount > 1 ? 's' : ''} ignorado${skippedCount > 1 ? 's' : ''})`
        : ''

      toast.success("Candidatos adicionados!", { description: `${addedCount} candidato(s) adicionado(s) à "${jobTitle}"${skippedMsg}` })

      onSuccess?.()
      onClose()
    } catch (error) {
      toast.error("Erro ao adicionar candidatos", { description: "Tente novamente" })
    } finally {
      setIsSubmitting(false)
    }
  }

  const candidateCount = candidateIds.length
  const displayNames = candidateNames.slice(0, 5)
  const remainingCount = candidateCount > 5 ? candidateCount - 5 : 0
  const hasComments = feedbackComments && feedbackComments.size > 0

  if (!open || !mounted) return null

  const modalContent = (
    <div
      className="fixed inset-0 z-modal flex items-center justify-center"
     
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-to-job-modal-title"
    >
      <div
        className="absolute inset-0 bg-lia-overlay backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={modalRef}
        className={`relative ${cardStyles.default} w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col`}
      >
        <div className=" p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-lia-text-secondary" />
              <h2 id="add-to-job-modal-title" className={textStyles.title}>
                Adicionar candidatos à vaga
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
              aria-label="Fechar modal"
              data-dismiss="true"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-hidden flex flex-col">
          {isOverLimit && (
            <div className="flex items-start gap-2 p-3 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-xl">
              <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-status-warning" aria-live="polite" aria-atomic="true">
                  Limite de {MAX_BULK_CANDIDATES} candidatos por operação
                </p>
                <p className="text-xs text-status-warning mt-0.5">
                  Você selecionou {candidateIds.length}. Apenas os primeiros {MAX_BULK_CANDIDATES} serão adicionados.
                </p>
              </div>
            </div>
          )}

          <div className={`${cardStyles.flat} p-3`}>
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-lia-text-secondary" />
              <span className={textStyles.label} aria-live="polite" aria-atomic="true">
                {effectiveCandidateIds.length} candidato{effectiveCandidateIds.length !== 1 ? 's' : ''} selecionado{effectiveCandidateIds.length !== 1 ? 's' : ''}
              </span>
            </div>
            {displayNames.length > 0 && (
              <div className="flex items-center gap-1.5 flex-wrap">
                {displayNames.map((name, idx) => (
                  <div key={idx} className="flex items-center gap-1.5 bg-lia-bg-primary rounded-full px-2 py-1 border border-lia-border-subtle">
                    <Avatar className="w-5 h-5">
                      <AvatarFallback className="text-micro bg-lia-bg-tertiary text-lia-text-secondary">
                        {getInitials(name)}
                      </AvatarFallback>
                    </Avatar>
                    <span className={`${textStyles.caption} truncate max-w-[100px]`}>
                      {name}
                    </span>
                  </div>
                ))}
                {remainingCount > 0 && (
                  <span className={`${textStyles.caption} text-lia-text-tertiary`}>
                    +{remainingCount} mais
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-muted" />
            <Input
              ref={searchInputRef}
              placeholder="Buscar vaga..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 border-lia-border-subtle text-xs placeholder:text-lia-text-disabled focus:ring-1 focus:ring-lia-border-default focus:border-lia-border-medium"
              aria-label="Buscar vagas"
            />
          </div>

          <ScrollArea className="flex-1 border border-lia-border-subtle rounded-xl min-h-card-lg max-h-[220px]">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-card-lg text-lia-text-secondary" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary mb-2" />
                <p className={textStyles.bodySmall}>Carregando...</p>
              </div>
            ) : filteredJobs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-card-lg text-lia-text-secondary">
                <Briefcase className="w-8 h-8 mb-2 opacity-50" />
                <p className={textStyles.bodySmall} aria-live="polite" aria-atomic="true">Nenhuma vaga encontrada</p>
                {searchTerm && (
                  <p className={`${textStyles.caption} mt-1`}>
                    Tente buscar com outros termos
                  </p>
                )}
              </div>
            ) : (
              <RadioGroup
                value={selectedJobId || ''}
                onValueChange={setSelectedJobId}
                className="p-2 space-y-1"
              >
                {filteredJobs.map((job) => (
                  <div
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                    className={cn(
                      "flex items-start gap-3 p-3 rounded-md cursor-pointer transition-colors",
                      selectedJobId === job.id
                        ? "bg-lia-bg-tertiary border border-lia-border-medium"
                        : "hover:bg-lia-interactive-hover border border-transparent"
                    )}
                  >
                    <RadioGroupItem value={job.id} id={job.id} className="mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Label
                          htmlFor={job.id}
                          className={`${textStyles.subtitle} cursor-pointer truncate`}
                        >
                          {job.title}
                        </Label>
                        {selectedJobId === job.id && (
                          <Check className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
                        )}
                      </div>
                      <div className={`flex items-center gap-3 mt-1 ${textStyles.caption}`}>
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {job.location}
                          </span>
                        )}
                        {job.candidates_count !== undefined && job.candidates_count > 0 && (
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {job.candidates_count} candidatos
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </RadioGroup>
            )}
          </ScrollArea>

          {duplicateIds.length > 0 && selectedJobId && (
            <div className="flex items-start gap-2 p-3 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-xl">
              <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-status-warning" aria-live="polite" aria-atomic="true">
                  {duplicateIds.length} candidato{duplicateIds.length > 1 ? 's' : ''} já {duplicateIds.length > 1 ? 'estão' : 'está'} nesta vaga
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Checkbox
                    id="skip-duplicates"
                    checked={skipDuplicates}
                    onCheckedChange={(checked) => setSkipDuplicates(checked === true)}
                  />
                  <Label
                    htmlFor="skip-duplicates"
                    className="text-xs text-status-warning cursor-pointer"
                  >
                    Ignorar duplicados e adicionar apenas os novos ({effectiveCandidateIds.length - duplicateIds.length})
                  </Label>
                </div>
              </div>
            </div>
          )}

          {selectedJobId && (
            <div className="space-y-3 pt-2 border-t border-lia-border-subtle">
              <div className="space-y-2">
                <Label className={textStyles.label}>Etapa inicial</Label>
                <Select value={selectedStage} onValueChange={setSelectedStage}>
                  <SelectTrigger className="w-full border-lia-border-subtle text-xs">
                    <SelectValue placeholder="Selecione a etapa" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableStages.map((stage) => (
                      <SelectItem key={stage} value={stage} className="text-xs">
                        {stage}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="notify-manager"
                    checked={notifyManager}
                    onCheckedChange={(checked) => setNotifyManager(checked === true)}
                  />
                  <Label
                    htmlFor="notify-manager"
                    className={`${textStyles.bodySmall} cursor-pointer flex items-center gap-1.5`}
                  >
                    <Bell className="w-3.5 h-3.5 text-lia-text-tertiary" />
                    Notificar gestor da vaga
                  </Label>
                </div>

                {hasComments && (
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-comments"
                      checked={includeComments}
                      onCheckedChange={(checked) => setIncludeComments(checked === true)}
                    />
                    <Label
                      htmlFor="include-comments"
                      className={`${textStyles.bodySmall} cursor-pointer flex items-center gap-1.5`}
                    >
                      <MessageSquare className="w-3.5 h-3.5 text-lia-text-tertiary" />
                      Incluir comentários como notas do candidato
                    </Label>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-lia-border-subtle bg-lia-bg-secondary p-4 flex items-center justify-between gap-2">
          <div className="text-xs text-lia-text-tertiary">
            {finalCandidateIds.length} candidato{finalCandidateIds.length !== 1 ? 's' : ''} será{finalCandidateIds.length !== 1 ? 'ão' : ''} adicionado{finalCandidateIds.length !== 1 ? 's' : ''}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!selectedJobId || isSubmitting || finalCandidateIds.length === 0}
              className="h-9 px-4 text-xs font-medium text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                  Adicionando...
                </>
              ) : (
                <>
                  Adicionar à Vaga
                  <ChevronRight className="w-4 h-4 ml-1" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
