"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { createPortal } from "react-dom"
import { liaApi, JobVacancy } from "@/services/lia-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import { Briefcase, Search, Loader2, Users, Check, Building2, MapPin, Star, X, AlertCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

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

const mockVacancies: VacancyDisplay[] = [
  {
    id: 'vacancy-1',
    title: 'UX Designer Sênior',
    department: 'Design',
    location: 'São Paulo, SP',
    status: 'open',
    priority: 'alta',
    candidates_count: 15,
    recruiter_name: 'Ana Silva',
    recruiter_email: 'ana.silva@empresa.com'
  },
  {
    id: 'vacancy-2',
    title: 'Tech Lead Mobile',
    department: 'Tecnologia',
    location: 'Remoto',
    status: 'open',
    priority: 'alta',
    candidates_count: 8,
    recruiter_name: 'Ana Silva',
    recruiter_email: 'ana.silva@empresa.com'
  },
  {
    id: 'vacancy-3',
    title: 'Product Manager',
    department: 'Produto',
    location: 'Rio de Janeiro, RJ',
    status: 'open',
    priority: 'media',
    candidates_count: 12,
    recruiter_name: 'Carlos Mendes',
    recruiter_email: 'carlos.mendes@empresa.com'
  },
  {
    id: 'vacancy-4',
    title: 'Frontend Developer',
    department: 'Tecnologia',
    location: 'São Paulo, SP',
    status: 'open',
    priority: 'alta',
    candidates_count: 20,
    recruiter_name: 'Ana Silva',
    recruiter_email: 'ana.silva@empresa.com'
  },
  {
    id: 'vacancy-5',
    title: 'Data Analyst',
    department: 'Dados',
    location: 'Híbrido - SP',
    status: 'open',
    priority: 'media',
    candidates_count: 5,
    recruiter_name: 'Roberto Costa',
    recruiter_email: 'roberto.costa@empresa.com'
  },
  {
    id: 'vacancy-6',
    title: 'Backend Developer Python',
    department: 'Tecnologia',
    location: 'Remoto',
    status: 'open',
    priority: 'baixa',
    candidates_count: 18,
    recruiter_name: 'Ana Silva',
    recruiter_email: 'ana.silva@empresa.com'
  }
]

function mapApiVacancyToDisplay(vacancy: JobVacancy): VacancyDisplay {
  return {
    id: vacancy.id,
    title: vacancy.title,
    department: vacancy.department,
    location: vacancy.location,
    status: vacancy.status,
    priority: (vacancy as any).priority,
    candidates_count: (vacancy as any).candidates_count,
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
  const { toast } = useToast()
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
        setVacancies(mockVacancies)
      }
    } catch (error) {
      console.warn('Failed to load vacancies from API, using mock data:', error)
      setVacancies(mockVacancies)
    } finally {
      setIsLoading(false)
    }
  }

  const isRecruiterVacancy = useCallback((vacancy: VacancyDisplay) => {
    if (!currentRecruiterEmail) return false
    return vacancy.recruiter_email?.toLowerCase() === currentRecruiterEmail.toLowerCase()
  }, [currentRecruiterEmail])

  const sortedAndFilteredVacancies = useMemo(() => {
    let filtered = vacancies.filter(v => 
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
      toast({ title: "Selecione uma vaga", variant: "destructive" })
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
      
      toast({
        title: "Candidatos adicionados!",
        description: `${candidateIds.length} candidato(s) adicionado(s) à vaga "${selectedVacancy?.title}"`,
      })
      
      onSuccess?.()
      onClose()
    } catch (error) {
      console.error('Error adding candidates to vacancy:', error)
      toast({
        title: "Erro ao adicionar candidatos",
        description: "Tente novamente",
        variant: "destructive"
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const getPriorityBadge = (priority?: string) => {
    switch (priority) {
      case 'alta':
        return <Badge className={badgeStyles.error}>Alta</Badge>
      case 'media':
        return <Badge className={badgeStyles.warning}>Média</Badge>
      case 'baixa':
        return <Badge className={badgeStyles.success}>Baixa</Badge>
      default:
        return null
    }
  }

  const VacancyCard = ({ vacancy }: { vacancy: VacancyDisplay }) => {
    const isOwn = isRecruiterVacancy(vacancy)
    
    return (
      <div
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
        className={cn(
          "p-3 rounded-md cursor-pointer transition-all outline-none",
          selectedVacancyId === vacancy.id
            ? "bg-gray-100 dark:bg-gray-700 border-2 border-gray-500"
            : "hover:bg-gray-50 border-2 border-transparent focus:ring-2 focus:ring-gray-400/50"
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={`${textStyles.subtitle} truncate`}>
                {vacancy.title}
              </span>
              {selectedVacancyId === vacancy.id && (
                <Check className="w-4 h-4 text-gray-700 dark:text-gray-300 flex-shrink-0" />
              )}
              {isOwn && (
                <Star className="w-3 h-3 text-amber-500 flex-shrink-0" fill="var(--status-warning)" />
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
      className="fixed inset-0 z-[9999] flex items-center justify-center"
     
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-vacancy-modal-title"
    >
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden="true"
      />
      
      <div 
        ref={modalRef}
        className={`relative ${cardStyles.default} w-full max-w-md mx-4 max-h-[90vh] overflow-hidden flex flex-col`}
      >
        <div className="border-b border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <h2 id="add-vacancy-modal-title" className={textStyles.title}>
                Adicionar à Vaga
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              aria-label="Fechar modal"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className={`${textStyles.bodySmall} mt-1`}>
            Selecione uma vaga para adicionar {candidateIds.length} candidato{candidateIds.length > 1 ? 's' : ''}
          </p>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-hidden flex flex-col">
          <div className={`flex items-center gap-2 p-2 ${cardStyles.flat}`}>
            <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <span className={textStyles.bodySmall}>
              {candidateNames.slice(0, 2).join(', ')}
              {candidateNames.length > 2 && ` e mais ${candidateNames.length - 2}`}
            </span>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              ref={firstFocusableRef}
              placeholder="Buscar vagas por título, departamento ou local..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 border-gray-200 text-xs placeholder:text-gray-400 focus:ring-1 focus:ring-gray-400 focus:border-gray-500"
              aria-label="Buscar vagas"
            />
          </div>

          <ScrollArea className="flex-1 border border-gray-100 rounded-md min-h-[250px]">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-[250px] text-gray-600">
                <Loader2 className="w-6 h-6 animate-spin text-gray-500 mb-2" />
                <p className={textStyles.bodySmall}>Carregando vagas...</p>
              </div>
            ) : loadError ? (
              <div className="flex flex-col items-center justify-center h-[250px] text-gray-600">
                <AlertCircle className="w-8 h-8 mb-2 text-red-400" />
                <p className={`${textStyles.bodySmall} text-red-600`}>{loadError}</p>
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
              <div className="flex flex-col items-center justify-center h-[250px] text-gray-600">
                <Briefcase className="w-8 h-8 mb-2 opacity-50" />
                <p className={textStyles.bodySmall}>Nenhuma vaga encontrada</p>
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
                      <Star className="w-3 h-3 text-amber-500" fill="var(--status-warning)" />
                      <span className={`${textStyles.caption} font-medium uppercase tracking-wider`}>
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
                        <Briefcase className="w-3 h-3 text-gray-500" />
                        <span className={`${textStyles.caption} font-medium uppercase tracking-wider`}>
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

        <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 flex items-center justify-end gap-2">
          <Button 
            variant="outline" 
            onClick={onClose} 
            disabled={isSubmitting}
            className="bg-white border border-gray-300 text-gray-800 hover:bg-gray-50 text-xs dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-200"
          >
            Cancelar
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={!selectedVacancyId || isSubmitting}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
