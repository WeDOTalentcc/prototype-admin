"use client"

import { useState, useEffect } from"react"
import { liaApi, JobVacancy } from"@/services/lia-api"
import { formatJobLocation } from "@/lib/jobs/location"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Checkbox } from"@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from"@/components/ui/dialog"
import { Briefcase, Search, Loader2, Users, Check, Building2, MapPin } from"lucide-react"
import { Chip } from"@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import { cn } from"@/lib/utils"
import { toast } from"sonner"

interface AddListToVacanciesModalProps {
  isOpen: boolean
  onClose: () => void
  listId: string
  listName: string
  candidateCount: number
  selectedCandidateIds?: string[]
  onSuccess?: () => void
}

export function AddListToVacanciesModal({ 
  isOpen, 
  onClose, 
  listId, 
  listName, 
  candidateCount, 
  selectedCandidateIds, 
  onSuccess 
}: AddListToVacanciesModalProps) {
const [vacancies, setVacancies] = useState<JobVacancy[]>([])
  const [selectedVacancyIds, setSelectedVacancyIds] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadVacancies()
      setSelectedVacancyIds(new Set())
      setSearchTerm('')
    }
  }, [isOpen])

  const loadVacancies = async () => {
    setIsLoading(true)
    try {
      const response = await liaApi.listJobVacancies('open', 0, 100)
      setVacancies(response.items || [])
    } catch (error) {
      toast.error("Erro ao carregar vagas")
    } finally {
      setIsLoading(false)
    }
  }

  const toggleVacancy = (vacancyId: string) => {
    const newSelected = new Set(selectedVacancyIds)
    if (newSelected.has(vacancyId)) {
      newSelected.delete(vacancyId)
    } else {
      newSelected.add(vacancyId)
    }
    setSelectedVacancyIds(newSelected)
  }

  const toggleAll = () => {
    if (selectedVacancyIds.size === filteredVacancies.length) {
      setSelectedVacancyIds(new Set())
    } else {
      setSelectedVacancyIds(new Set(filteredVacancies.map(v => v.id)))
    }
  }

  const filteredVacancies = vacancies.filter(v => 
    v.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.department?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    formatJobLocation(v.location)?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleSubmit = async () => {
    if (selectedVacancyIds.size === 0) {
      toast.error("Selecione pelo menos uma vaga")
      return
    }
    
    setIsSubmitting(true)
    try {
      const result = await liaApi.assignListToJobs(
        listId,
        Array.from(selectedVacancyIds),
        selectedCandidateIds
      )
      
      toast.success("Candidatos adicionados às vagas", { description: `${result.assigned} adicionado(s) a ${result.jobs_count} vaga(s)${result.already_in_job > 0 ? `, ${result.already_in_job} já existente(s)` : ''}` })
      
      onSuccess?.()
      onClose()
    } catch (error) {
      toast.error("Erro ao adicionar às vagas")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  const candidatesToAdd = selectedCandidateIds?.length || candidateCount
  const isAddingSelected = selectedCandidateIds && selectedCandidateIds.length > 0

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return <Chip variant="success">Aberta</Chip>
      case 'paused':
        return <Chip variant="warning">Pausada</Chip>
      case 'closed':
        return <Chip variant="neutral" muted>Fechada</Chip>
      default:
        return <Chip variant="neutral">{status}</Chip>
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return <Chip variant="danger">Urgente</Chip>
      case 'high':
        return <Chip variant="warning">Alta</Chip>
      default:
        return null
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg border-lia-border-subtle rounded-xl" data-testid="add-list-to-vacancies-modal">
        <DialogHeader>
          <DialogTitle className="text-lg flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-lia-text-secondary" />
            Adicionar a Vagas
          </DialogTitle>
          <DialogDescription className="text-xs">
            <div className="flex items-center gap-4 mt-1">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full bg-lia-bg-secondary dark:bg-lia-text-secondary" 
                />
                <span className="font-medium text-lia-text-primary">{listName}</span>
              </div>
              <div className="flex items-center gap-1.5 text-lia-text-primary">
                <Users className="w-4 h-4" />
                <span aria-live="polite" aria-atomic="true">
                  {isAddingSelected 
                    ? `${candidatesToAdd} de ${candidateCount} candidatos selecionados`
                    : `${candidateCount} candidato${candidateCount !== 1 ? 's' : ''}`
                  }
                </span>
              </div>
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
            <Input
              placeholder="Buscar vagas por título, departamento ou local..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 border-lia-border-subtle rounded-xl text-xs"
            />
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
            </div>
          ) : vacancies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Briefcase className="w-10 h-10 text-lia-text-disabled mb-3" />
              <p className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">Nenhuma vaga aberta encontrada</p>
              <p className="text-xs text-lia-text-secondary mt-1" aria-live="polite" aria-atomic="true">
                Crie uma vaga primeiro para poder adicionar candidatos
              </p>
            </div>
          ) : filteredVacancies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-10 h-10 text-lia-text-disabled mb-3" />
              <p className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">Nenhuma vaga encontrada</p>
              <p className="text-xs text-lia-text-secondary mt-1">
                Tente buscar com outros termos
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between px-1">
                <button
                  type="button"
                  onClick={toggleAll}
                  className="text-xs text-lia-text-secondary hover:underline flex items-center gap-1.5"
                >
                  <Checkbox 
                    checked={selectedVacancyIds.size === filteredVacancies.length && filteredVacancies.length > 0}
                    className="w-3.5 h-3.5"
                  />
                  {selectedVacancyIds.size === filteredVacancies.length 
                    ? 'Desmarcar todas' 
                    : 'Selecionar todas'
                  }
                </button>
                <span className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
                  {filteredVacancies.length} vaga{filteredVacancies.length !== 1 ? 's' : ''} disponíve{filteredVacancies.length !== 1 ? 'is' : 'l'}
                </span>
              </div>

              <ScrollArea className="h-[280px] pr-3">
                <div className="space-y-2">
                  {filteredVacancies.map((vacancy) => (
                    <div
                      key={vacancy.id}
                      className={cn("flex items-start gap-3 p-3 rounded-md border border-lia-border-subtle cursor-pointer transition-colors motion-reduce:transition-none hover:border-lia-border-medium dark:hover:border-lia-border-medium",
                        selectedVacancyIds.has(vacancy.id) &&"border-lia-btn-primary-bg bg-lia-bg-secondary"
                      )}
                      onClick={() => toggleVacancy(vacancy.id)}
                    >
                      <Checkbox 
                        checked={selectedVacancyIds.has(vacancy.id)}
                        className="mt-0.5"
                        onClick={(e) => e.stopPropagation()}
                        onCheckedChange={() => toggleVacancy(vacancy.id)}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-xs font-medium text-lia-text-primary truncate">
                              {vacancy.title}
                            </h4>
                            <div className="flex items-center gap-3 mt-1 text-xs text-lia-text-primary">
                              {vacancy.department && (
                                <div className="flex items-center gap-1">
                                  <Building2 className="w-3 h-3" />
                                  <span>{vacancy.department}</span>
                                </div>
                              )}
                              {vacancy.location && (
                                <div className="flex items-center gap-1">
                                  <MapPin className="w-3 h-3" />
                                  <span>{formatJobLocation(vacancy.location)}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            {getPriorityBadge(vacancy.priority)}
                            {getStatusBadge(vacancy.status)}
                          </div>
                        </div>
                        {vacancy.funnel_data?.total !== undefined && (
                          <div className="mt-2 text-xs text-lia-text-primary">
                            {vacancy.funnel_data.total} candidato{vacancy.funnel_data.total !== 1 ? 's' : ''} no funil
                          </div>
                        )}
                      </div>
                      {selectedVacancyIds.has(vacancy.id) && (
                        <Check className="w-4 h-4 flex-shrink-0 mt-0.5 text-lia-text-primary" />
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {selectedVacancyIds.size > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 bg-lia-bg-secondary rounded-xl border border-lia-border-default">
                  <Check className="w-4 h-4 text-lia-text-primary" />
                  <span className="text-xs text-lia-text-primary">
                    <strong>{selectedVacancyIds.size}</strong> vaga{selectedVacancyIds.size !== 1 ? 's' : ''} selecionada{selectedVacancyIds.size !== 1 ? 's' : ''}
                    {' · '}
                    <strong>{candidatesToAdd}</strong> candidato{candidatesToAdd !== 1 ? 's' : ''} serão adicionados
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-2 border-t border-lia-border-subtle bg-lia-bg-secondary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
            className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg"
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || isLoading || selectedVacancyIds.size === 0}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                Adicionando...
              </>
            ) : (
              <>
                <Briefcase className="w-4 h-4 mr-2" />
                {selectedVacancyIds.size > 0 
                  ? `Adicionar a ${selectedVacancyIds.size} vaga${selectedVacancyIds.size !== 1 ? 's' : ''}`
                  : 'Adicionar a Vagas'
                }
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
