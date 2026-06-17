"use client"

import { useState, useCallback, useEffect } from "react"
import { liaApi } from "@/services/lia-api"
import { formatJobLocation } from "@/lib/jobs/location"
import type { 
  KanbanJob, 
  KanbanCandidate, 
  KanbanStage, 
  MoveAction, 
  LIASuggestion,
  DragResult 
} from "../types"

interface UseKanbanStateOptions {
  jobId: string
  onMoveComplete?: (action: MoveAction) => void
}

interface UseKanbanStateResult {
  job: KanbanJob | null
  stages: KanbanStage[]
  selectedCandidate: KanbanCandidate | null
  isLoading: boolean
  error: Error | null
  pendingMove: MoveAction | null
  liaSuggestions: LIASuggestion[]
  selectCandidate: (candidate: KanbanCandidate | null) => void
  startMove: (action: MoveAction) => void
  confirmMove: (substatus?: string, reason?: string) => Promise<void>
  cancelMove: () => void
  handleDragEnd: (result: DragResult) => void
  refreshJob: () => Promise<void>
}

export function useKanbanState(options: UseKanbanStateOptions): UseKanbanStateResult {
  const { jobId, onMoveComplete } = options
  
  const [job, setJob] = useState<KanbanJob | null>(null)
  const [stages, setStages] = useState<KanbanStage[]>([])
  const [selectedCandidate, setSelectedCandidate] = useState<KanbanCandidate | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [pendingMove, setPendingMove] = useState<MoveAction | null>(null)
  const [liaSuggestions, setLiaSuggestions] = useState<LIASuggestion[]>([])

  const loadJob = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await liaApi.getJobVacancy(jobId)
      
      const defaultStages: KanbanStage[] = [
        { id: "applied", name: "Inscritos", color: "var(--lia-text-tertiary)", order: 0, candidates: [], candidateCount: 0 },
        { id: "screening", name: "Triagem", color: "var(--wedo-blue)", order: 1, candidates: [], candidateCount: 0 },
        { id: "interview", name: "Entrevista", color: "var(--wedo-purple)", order: 2, candidates: [], candidateCount: 0 },
        { id: "technical", name: "Teste Técnico", color: "var(--status-warning)", order: 3, candidates: [], candidateCount: 0 },
        { id: "offer", name: "Proposta", color: "var(--status-success)", order: 4, candidates: [], candidateCount: 0 },
        { id: "hired", name: "Contratado", color: "var(--status-success)", order: 5, candidates: [], candidateCount: 0 },
      ]
      
      const jobData: KanbanJob = {
        id: response.id,
        title: response.title,
        department: response.department,
        location: formatJobLocation(response.location),
        status: response.status as KanbanJob['status'],
        stages: defaultStages,
        totalCandidates: 0,
        createdAt: (response as unknown as Record<string, unknown>).created_at as string,
      }
      
      setJob(jobData)
      setStages(defaultStages)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to load job"))
    } finally {
      setIsLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    loadJob()
  }, [loadJob])

  const selectCandidate = useCallback((candidate: KanbanCandidate | null) => {
    setSelectedCandidate(candidate)
  }, [])

  const startMove = useCallback(async (action: MoveAction) => {
    setPendingMove(action)
    
    try {
      const response = await fetch("/api/backend-proxy/lia/kanban-assistant/stage-move-suggestions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: action.candidateId,
          from_stage: action.fromStageId,
          to_stage: action.toStageId,
          job_title: job?.title ?? null,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const suggestions: LIASuggestion[] = (data.suggestions ?? []).map(
          (s: { type: string; content: string; confidence: number }) => ({
            type: s.type,
            content: s.content,
            confidence: s.confidence,
          })
        )
        setLiaSuggestions(suggestions)
      } else {
        setLiaSuggestions([])
      }
    } catch {
      setLiaSuggestions([])
    }
  }, [job])

  const confirmMove = useCallback(async (substatus?: string, reason?: string) => {
    if (!pendingMove) return
    
    const finalAction: MoveAction = {
      ...pendingMove,
      newSubstatus: substatus,
      reason,
    }
    
    try {
      setStages((currentStages) => {
        const newStages = [...currentStages]
        
        const fromStage = newStages.find((s) => s.id === finalAction.fromStageId)
        const toStage = newStages.find((s) => s.id === finalAction.toStageId)
        
        if (fromStage && toStage) {
          const candidateIndex = fromStage.candidates.findIndex(
            (c) => c.id === finalAction.candidateId
          )
          
          if (candidateIndex !== -1) {
            const [candidate] = fromStage.candidates.splice(candidateIndex, 1)
            candidate.stageId = finalAction.toStageId
            candidate.substatus = finalAction.newSubstatus
            candidate.movedAt = new Date().toISOString()
            toStage.candidates.push(candidate)
            
            fromStage.candidateCount = fromStage.candidates.length
            toStage.candidateCount = toStage.candidates.length
          }
        }
        
        return newStages
      })
      
      onMoveComplete?.(finalAction)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Move failed"))
    } finally {
      setPendingMove(null)
      setLiaSuggestions([])
    }
  }, [pendingMove, onMoveComplete])

  const cancelMove = useCallback(() => {
    setPendingMove(null)
    setLiaSuggestions([])
  }, [])

  const handleDragEnd = useCallback((result: DragResult) => {
    if (!result.destination) return
    
    const { source, destination, draggableId } = result
    
    if (source.droppableId === destination.droppableId) {
      setStages((currentStages) => {
        const newStages = [...currentStages]
        const stage = newStages.find((s) => s.id === source.droppableId)
        
        if (stage) {
          const [removed] = stage.candidates.splice(source.index, 1)
          stage.candidates.splice(destination.index, 0, removed)
        }
        
        return newStages
      })
    } else {
      startMove({
        candidateId: draggableId,
        fromStageId: source.droppableId,
        toStageId: destination.droppableId,
      })
    }
  }, [startMove])

  const refreshJob = useCallback(async () => {
    await loadJob()
  }, [loadJob])

  return {
    job,
    stages,
    selectedCandidate,
    isLoading,
    error,
    pendingMove,
    liaSuggestions,
    selectCandidate,
    startMove,
    confirmMove,
    cancelMove,
    handleDragEnd,
    refreshJob,
  }
}
