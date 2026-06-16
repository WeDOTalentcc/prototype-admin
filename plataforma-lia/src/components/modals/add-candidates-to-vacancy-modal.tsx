"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from"react"
import { createPortal } from"react-dom"
import { liaApi, JobVacancy } from"@/services/lia-api"
import { formatJobLocation } from "@/lib/jobs/location"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Briefcase, Search, Loader2, Users, Check, Building2, MapPin, Star, X, AlertCircle } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import { cn } from"@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { toast } from"sonner"

interface AddCandidatesToVacancyModalProps {
  isOpen: boolean
  onClose: () => void
  candidateIds: string[]
  candidateNames: string[]
  onSuccess?: () => void
  currentRecruiterEmail?: string
}

interface VacancyDisplay {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
  priority?: string
  candidates_count?: number
  recruiter_name?: string
  recruiter_email?: string
}


function mapApiVacancyToDisplay(vacancy: JobVacancy): VacancyDisplay {
  return {
    id: vacancy.id,
    title: vacancy.title,
    department: vacancy.department,
    location: formatJobLocation(vacancy.location),
    status: vacancy.status,
    priority: vacancy.priority as string | undefined,
    candidates_count: (vacancy as unknown as Record<string, unknown>).candidates_count as number | undefined,
    recruiter_name: vacancy.recruiter,
    recruiter_email: vacancy.recruiter_email
  }
}

export function AddCandidatesToVacancyModal({ 
  isOpen, 
  onClose, 
  candidateIds,
  candidateNames,
  onSuccess,
  currentRecruiterEmail
}: AddCandidatesToVacancyModalProps) {
const [vacancies, setVacancies] = useState<VacancyDisplay[]>([])
  const [selectedVacancyId, setSelectedVacancyId] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)
  const firstFocusableRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  useEffect(() => {
    if (isOpen) {
      loadVacancies()
      setSelectedVacancyId(null)
      setSearchTerm('')
      setLoadError(null)
      setTimeout(() => firstFocusableRef.current?.focus(), 100)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
        if (focusableElements.length === 0) return
        
        const firstElement = focusableElements[0]
        const lastElement = focusableElements[focusableElements.length - 1]

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault()
          lastElement?.focus()
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault()
          firstElement?.focus()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  useEffect(() => {
    if (!isOpen) return

    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = originalOverflow
    }
  }, [isOpen])

  const loadVacancies = async () => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const response = await liaApi.listJobVacancies('open', 0, 100)
      if (response.items && response.items.length > 0) {
        const mapped = response.items.map(mapApiVacancyToDisplay)
        setVacancies(mapped)
      } else {
        setVacancies([])
      }
    } catch (error) {
      setLoadError("Não foi possível carregar as vagas. Tente novamente.")
      setVacancies([])
    } finally {
      setIsLoading(false)
    }
  }

  const isRecruiterVacancy = useCallback((vacancy: VacancyDisplay) => {
    if (!currentRecruiterEmail) return false
    return vacancy.recruiter_email?.toLowerCase() === currentRecruiterEmail.toLowerCase()
  }, [currentRecruiterEmail])

  const sortedAndFilteredVacancies = useMemo(() => {
    const filtered = vacancies.filter(v => 
      v.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.department?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.location?.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return filtered.sort((a, b) => {
      const aIsRecruiter = isRecruiterVacancy(a)
      const bIsRecruiter = isRecruiterVacancy(b)
      if (aIsRecruiter && !bIsRecruiter) return -1
      if (!aIsRecruiter && bIsRecruiter) return 1

      const priorityOrder: Record<string, number> = { 'alta': 0, 'media': 1, 'baixa': 2 }
      const aPriority = priorityOrder[a.priority || 'media'] ?? 1
      const bPriority = priorityOrder[b.priority || 'media'] ?? 1
      if (aPriority !== bPriority) return aPriority - bPriority

      return (b.candidates_count || 0) - (a.candidates_count || 0)
    })
  }, [vacancies, searchTerm, isRecruiterVacancy])

  const recruiterVacancies = sortedAndFilteredVacancies.filter(isRecruiterVacancy)
  const otherVacancies = sortedAndFilteredVacancies.filter(v => !isRecruiterVacancy(v))

  const handleSubmit = async () => {
    if (!selectedVacancyId) {
      toast.error("Selecione uma vaga")
      return
    }
    
    setIsSubmitting(true)
    try {
      const selectedVacancy = vacancies.find(v => v.id === selectedVacancyId)
      
      const response = await fetch(`/api/backend-proxy/search/vacancy/${selectedVacancyId}/add-candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          candidate_ids: candidateIds,
          stage: 'novo'
        })
      })
      
      if (!response.ok) {
        throw new Error('Falha ao adicionar candidatos')
      }
      
      toast.success("Candidatos adicionados!", { description: `${candidateIds.length} candidato(s) adicionado(s) à vaga"${selectedVacancy?.title}"` })
      
      onSuccess?.()
      onClose()
    } catch (error) {
      toast.error("Erro ao adicionar candidatos", { description:"Tente novamente" })
    } finally {
      setIsSubmitting(false)
    }
  }

  const getPriorityBadge = (priority?: string) => {
    switch (priority) {
      case 'alta':
        return <Chip variant="neutral" muted className={badgeStyles.error}>Alta</Chip>
      case 'media':
        return <Chip variant="neutral" muted className={badgeStyles.warning}>Média</Chip>
      case 'baixa':
        return <Chip variant="neutral" muted className={badgeStyles.success}>Baixa</Chip>
      default:
        return null
    }
  }

  const VacancyCard = ({ vacancy }: { vacancy: VacancyDisplay }) => {
    const isOwn = isRecruiterVacancy(vacancy)
    
    return (
      <div
        data-testid={`vacancy-card-${vacancy.id}`}
        role="option"
        aria-selected={selectedVacancyId === vacancy.id}
        tabIndex={0}
        onClick={() => setSelectedVacancyId(vacancy.id)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setSelectedVacancyId(vacancy.id)
          }
        }}
        className={cn("p-3 rounded-md cursor-pointer transition-colors outline-none",
          selectedVacancyId === vacancy.id
            ?"bg-lia-bg-tertiary border-2 border-lia-border-medium"
            :"hover:bg-lia-interactive-hover border-2 border-transparent focus:ring-2 focus:ring-lia-border-default/50"
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={`${textStyles.subtitle} truncate`}>
                {vacancy.title}
              </span>
              {selectedVacancyId === vacancy.id && (
                <Check className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
              )}
              {isOwn && (
                <Star className="w-3 h-3 text-status-warning flex-shrink-0" fill="var(--status-warning)" />
              )}
            </div>
            <div className={`flex items-center gap-3 mt-1 ${textStyles.bodySmall}`}>
              {vacancy.department && (
                <span className="flex items-center gap-1">
                  <Building2 className="w-3 h-3" />
                  {vacancy.department}
                </span>
              )}
              {vacancy.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {vacancy.location}
                </span>
              )}
              {vacancy.candidates_count !== undefined && vacancy.candidates_count > 0 && (
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {vacancy.candidates_count}
                </span>
              )}
            </div>
          </div>
          {vacancy.priority && (
            <div className="flex flex-col items-end gap-1 ml-2">
              {getPriorityBadge(vacancy.priority)}
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!isOpen || !mounted) return null

  const modalContent = (
    <div 
      className="fixed inset-0 z-modal flex items-center justify-center"
     
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-vacancy-modal-title"
    >
      <div 
        className="absolute inset-0 bg-lia-overlay backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden="true"
      />
      
      <div 
        ref={modalRef}
        className={`relative ${cardStyles.default} w-full max-w-md mx-4 max-h-[90vh] overflow-hidden flex flex-col`}
      >
        <div className="p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-lia-text-secondary" />
              <h2 id="add-vacancy-modal-title" className={textStyles.title}>
                Adicionar à Vaga
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
          <p className={`${textStyles.bodySmall} mt-1`} aria-live="polite" aria-atomic="true">
            Selecione uma vaga para adicionar {candidateIds.length} candidato{candidateIds.length > 1 ? 's' : ''}
          </p>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-hidden flex flex-col">
          <div className={`flex items-center gap-2 p-2 ${cardStyles.flat}`}>
            <Users className="w-4 h-4 text-lia-text-secondary" />
            <span className={textStyles.bodySmall}>
              {candidateNames.slice(0, 2).join(', ')}
              {candidateNames.length > 2 && ` e mais ${candidateNames.length - 2}`}
            </span>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
            <Input
              ref={firstFocusableRef}
              placeholder="Buscar vagas por título, departamento ou local..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 border-lia-border-subtle text-xs placeholder:text-lia-text-disabled focus:ring-1 focus:ring-lia-border-default focus:border-lia-border-medium"
              aria-label="Buscar vagas"
            />
          </div>

          <ScrollArea className="flex-1 border border-lia-border-subtle rounded-xl min-h-[250px]">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-[250px] text-lia-text-secondary" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary mb-2" />
                <p className={textStyles.bodySmall} aria-live="polite" aria-atomic="true">Carregando vagas...</p>
              </div>
            ) : loadError ? (
              <div className="flex flex-col items-center justify-center h-[250px] text-lia-text-secondary">
                <AlertCircle className="w-8 h-8 mb-2 text-status-error" />
                <p className={`${textStyles.bodySmall} text-status-error`}>{loadError}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={loadVacancies}
                  className="mt-2 text-xs"
                >
                  Tentar novamente
                </Button>
              </div>
            ) : sortedAndFilteredVacancies.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[250px] text-lia-text-secondary">
                <Briefcase className="w-8 h-8 mb-2 opacity-50" />
                <p className={textStyles.bodySmall} aria-live="polite" aria-atomic="true">Nenhuma vaga encontrada</p>
                {searchTerm && (
                  <p className={`${textStyles.caption} mt-1`}>
                    Tente buscar com outros termos
                  </p>
                )}
              </div>
            ) : (
              <div className="p-2 space-y-3" role="listbox" aria-label="Lista de vagas">
                {recruiterVacancies.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 px-2 py-1.5 mb-1">
                      <Star className="w-3 h-3 text-status-warning" fill="var(--status-warning)" />
                      <span className={`${textStyles.caption} font-medium uppercase tracking-wider`} aria-live="polite" aria-atomic="true">
                        Suas Vagas
                      </span>
                    </div>
                    <div className="space-y-1">
                      {recruiterVacancies.map((vacancy) => (
                        <VacancyCard key={vacancy.id} vacancy={vacancy} />
                      ))}
                    </div>
                  </div>
                )}
                
                {otherVacancies.length > 0 && (
                  <div>
                    {recruiterVacancies.length > 0 && (
                      <div className="flex items-center gap-2 px-2 py-1.5 mb-1 mt-2">
                        <Briefcase className="w-3 h-3 text-lia-text-tertiary" />
                        <span className={`${textStyles.caption} font-medium uppercase tracking-wider`} aria-live="polite" aria-atomic="true">
                          Outras Vagas
                        </span>
                      </div>
                    )}
                    <div className="space-y-1">
                      {otherVacancies.map((vacancy) => (
                        <VacancyCard key={vacancy.id} vacancy={vacancy} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </div>

        <div className="border-t border-lia-border-subtle bg-lia-bg-secondary p-4 flex items-center justify-end gap-2">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={isSubmitting}
            className="bg-lia-bg-primary border border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover text-xs dark:hover:bg-lia-btn-primary-bg"
          >
            Cancelar
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={!selectedVacancyId || isSubmitting}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                Adicionando...
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Adicionar à Vaga
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )

  return createPortal(modalContent, document.body)
}
