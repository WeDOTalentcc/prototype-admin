"use client"

import { useState } from "react"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"
import type { Job } from "@/components/jobs"

export interface UseJobSelectionState {
  selectedJobsForBatch: Set<number>
  pinnedJobs: Set<number>
  urgentJobs: Set<number>
  favoriteJobs: Set<number>
}

export interface UseJobSelectionActions {
  setSelectedJobsForBatch: React.Dispatch<React.SetStateAction<Set<number>>>
  selectAllJobs: (filteredJobs: Job[], callbacks?: SelectionCallbacks) => void
  deselectAllJobs: () => void
  toggleJobSelection: (jobId: number, allJobs: Job[], callbacks?: SelectionCallbacks) => void
  togglePinJob: (jobId: number) => void
  toggleUrgentJob: (jobId: number, allJobs: Job[]) => void
  toggleFavoriteJob: (jobId: number) => void
  getSelectedJobsHaveActiveStatus: (allJobs: Job[]) => boolean
}

export interface SelectionCallbacks {
  setShowExpandedLIA?: (show: boolean) => void
  setLiaHighlight?: (highlight: boolean) => void
  setLiaPromptValue?: (value: string) => void
  liaInputRef?: React.RefObject<HTMLInputElement>
}

export interface UseJobSelectionReturn {
  state: UseJobSelectionState
  actions: UseJobSelectionActions
}

export function useJobSelection(): UseJobSelectionReturn {
  const [selectedJobsForBatch, setSelectedJobsForBatch] = useState<Set<number>>(new Set())
  const [pinnedJobs, setPinnedJobs] = useState<Set<number>>(new Set())
  const [urgentJobs, setUrgentJobs] = useState<Set<number>>(new Set())
  const [favoriteJobs, setFavoriteJobs] = useState<Set<number>>(new Set())

  const selectAllJobs = (filteredJobs: Job[], callbacks?: SelectionCallbacks) => {
    const allJobIds = new Set(filteredJobs.map(job => job.id))
    setSelectedJobsForBatch(allJobIds)

    if (callbacks) {
      callbacks.setShowExpandedLIA?.(true)
      callbacks.setLiaHighlight?.(true)
      callbacks.setLiaPromptValue?.(`Analisar ${allJobIds.size} vagas selecionadas`)
      setTimeout(() => callbacks.setLiaHighlight?.(false), 1000)
      setTimeout(() => {
        callbacks.liaInputRef?.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 100)
    }
  }

  const deselectAllJobs = () => {
    setSelectedJobsForBatch(new Set())
  }

  const toggleJobSelection = (jobId: number, allJobs: Job[], callbacks?: SelectionCallbacks) => {
    setSelectedJobsForBatch(prev => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }

      if (callbacks) {
        if (newSet.size > 0) {
          callbacks.setShowExpandedLIA?.(true)
          callbacks.setLiaHighlight?.(true)
          const selectedJobs = allJobs.filter(job => newSet.has(job.id))
          const jobTitles = selectedJobs.map(job => job.title).join(', ')
          callbacks.setLiaPromptValue?.(`Analisar ${newSet.size} vaga(s) selecionada(s): ${jobTitles}`)
          setTimeout(() => callbacks.setLiaHighlight?.(false), 1000)
          setTimeout(() => {
            callbacks.liaInputRef?.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }, 100)
        } else {
          callbacks.setLiaPromptValue?.('')
        }
      }

      return newSet
    })
  }

  const togglePinJob = (jobId: number) => {
    setPinnedJobs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }
      return newSet
    })
  }

  const toggleUrgentJob = async (jobId: number, allJobs: Job[]) => {
    const job = allJobs.find(j => j.id === jobId)
    if (!job?.backendId) {
      toast.error('Vaga não encontrada')
      return
    }

    const isCurrentlyUrgent = urgentJobs.has(jobId)
    const newUrgencyLevel = isCurrentlyUrgent ? 3 : 5

    try {
      await liaApi.updateJobVacancy(job.backendId, { urgency_level: newUrgencyLevel })
      setUrgentJobs(prev => {
        const newSet = new Set(prev)
        if (isCurrentlyUrgent) {
          newSet.delete(jobId)
        } else {
          newSet.add(jobId)
        }
        return newSet
      })
      toast.success(isCurrentlyUrgent ? 'Vaga marcada como normal' : 'Vaga marcada como urgente')
    } catch (error) {
      toast.error('Erro ao atualizar urgência da vaga')
    }
  }

  const toggleFavoriteJob = (jobId: number) => {
    setFavoriteJobs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(jobId)) {
        newSet.delete(jobId)
      } else {
        newSet.add(jobId)
      }
      return newSet
    })
  }

  const getSelectedJobsHaveActiveStatus = (allJobs: Job[]) => {
    const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
    return selectedJobs.some(job => job.status === 'Ativa')
  }

  return {
    state: {
      selectedJobsForBatch,
      pinnedJobs,
      urgentJobs,
      favoriteJobs,
    },
    actions: {
      setSelectedJobsForBatch,
      selectAllJobs,
      deselectAllJobs,
      toggleJobSelection,
      togglePinJob,
      toggleUrgentJob,
      toggleFavoriteJob,
      getSelectedJobsHaveActiveStatus,
    },
  }
}
