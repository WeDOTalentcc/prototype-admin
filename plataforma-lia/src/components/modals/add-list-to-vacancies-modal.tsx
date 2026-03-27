"use client"

import { useState, useEffect } from "react"
import { liaApi, JobVacancy } from "@/services/lia-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog"
import { Briefcase, Search, Loader2, Users, Check, Building2, MapPin } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

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
  const { toast } = useToast()
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
      toast({ title: "Erro ao carregar vagas", variant: "destructive" })
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
    v.location?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleSubmit = async () => {
    if (selectedVacancyIds.size === 0) {
      toast({ title: "Selecione pelo menos uma vaga", variant: "destructive" })
      return
    }
    
    setIsSubmitting(true)
    try {
      const result = await liaApi.assignListToJobs(
        listId,
        Array.from(selectedVacancyIds),
        selectedCandidateIds
      )
      
      toast({
        title: "Candidatos adicionados às vagas",
        description: `${result.assigned} adicionado(s) a ${result.jobs_count} vaga(s)${result.already_in_job > 0 ? `. ${result.already_in_job} já estavam em alguma vaga.` : ''}`
      })
      
      onSuccess?.()
      onClose()
    } catch (error) {
      toast({ title: "Erro ao adicionar às vagas", variant: "destructive" })
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
        return <Badge variant="success" className="text-xs">Aberta</Badge>
      case 'paused':
        return <Badge variant="warning" className="text-xs">Pausada</Badge>
      case 'closed':
        return <Badge variant="default" className="text-xs">Fechada</Badge>
      default:
        return <Badge variant="outline" className="text-xs">{status}</Badge>
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return <Badge variant="danger" className="text-xs">Urgente</Badge>
      case 'high':
        return <Badge variant="warning" className="text-xs">Alta</Badge>
      default:
        return null
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg border-gray-200 dark:border-gray-700 rounded-md dark:bg-gray-900">
        <DialogHeader>
          <DialogTitle className="font-['Open_Sans',sans-serif] text-lg flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Adicionar a Vagas
          </DialogTitle>
          <DialogDescription className="text-xs">
            <div className="flex items-center gap-4 mt-1">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full bg-gray-500 dark:bg-gray-400" 
                />
                <span className="font-medium text-gray-800 dark:text-gray-200">{listName}</span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-800 dark:text-gray-200">
                <Users className="w-4 h-4" />
                <span>
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
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Buscar vagas por título, departamento ou local..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 border-gray-200 rounded-md text-xs"
            />
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
            </div>
          ) : vacancies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Briefcase className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-xs text-gray-800 dark:text-gray-200">Nenhuma vaga aberta encontrada</p>
              <p className="text-xs text-gray-600 mt-1">
                Crie uma vaga primeiro para poder adicionar candidatos
              </p>
            </div>
          ) : filteredVacancies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-xs text-gray-800 dark:text-gray-200">Nenhuma vaga encontrada</p>
              <p className="text-xs text-gray-600 mt-1">
                Tente buscar com outros termos
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between px-1">
                <button
                  type="button"
                  onClick={toggleAll}
                  className="text-xs text-gray-700 dark:text-gray-300 hover:underline flex items-center gap-1.5"
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
                <span className="text-xs text-gray-800 dark:text-gray-200">
                  {filteredVacancies.length} vaga{filteredVacancies.length !== 1 ? 's' : ''} disponíve{filteredVacancies.length !== 1 ? 'is' : 'l'}
                </span>
              </div>

              <ScrollArea className="h-[280px] pr-3">
                <div className="space-y-2">
                  {filteredVacancies.map((vacancy) => (
                    <div
                      key={vacancy.id}
                      className={cn(
                        "flex items-start gap-3 p-3 rounded-md border border-gray-200 dark:border-gray-700 cursor-pointer transition-all hover:border-gray-400 dark:hover:border-gray-500",
                        selectedVacancyIds.has(vacancy.id) && "border-gray-900 dark:border-gray-300 bg-gray-50 dark:bg-gray-800"
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
                            <h4 className="text-xs font-medium text-gray-950 dark:text-gray-50 truncate">
                              {vacancy.title}
                            </h4>
                            <div className="flex items-center gap-3 mt-1 text-xs text-gray-800 dark:text-gray-200">
                              {vacancy.department && (
                                <div className="flex items-center gap-1">
                                  <Building2 className="w-3 h-3" />
                                  <span>{vacancy.department}</span>
                                </div>
                              )}
                              {vacancy.location && (
                                <div className="flex items-center gap-1">
                                  <MapPin className="w-3 h-3" />
                                  <span>{vacancy.location}</span>
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
                          <div className="mt-2 text-xs text-gray-800 dark:text-gray-200">
                            {vacancy.funnel_data.total} candidato{vacancy.funnel_data.total !== 1 ? 's' : ''} no funil
                          </div>
                        )}
                      </div>
                      {selectedVacancyIds.has(vacancy.id) && (
                        <Check className="w-4 h-4 flex-shrink-0 mt-0.5 text-gray-900 dark:text-gray-100" />
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {selectedVacancyIds.size > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-600">
                  <Check className="w-4 h-4 text-gray-900 dark:text-gray-100" />
                  <span className="text-xs text-gray-800 dark:text-gray-200">
                    <strong>{selectedVacancyIds.size}</strong> vaga{selectedVacancyIds.size !== 1 ? 's' : ''} selecionada{selectedVacancyIds.size !== 1 ? 's' : ''}
                    {' · '}
                    <strong>{candidatesToAdd}</strong> candidato{candidatesToAdd !== 1 ? 's' : ''} serão adicionados
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
            className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || isLoading || selectedVacancyIds.size === 0}
            className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
