"use client"

import { useEffect, useRef, useCallback } from "react"
import { useKanbanStore } from "@/stores/kanban-store"

/**
 * GAP-09-001: Real-time kanban updates via SSE.
 *
 * Connects to /api/v1/kanban/events and applies candidate stage changes
 * to the Zustand kanban store. When recruiter A moves a candidate,
 * recruiter B sees it instantly without page refresh.
 *
 * Graceful degradation: if SSE fails, kanban works as before (no polling
 * but manual refresh shows changes). SSE reconnects automatically.
 */

export interface KanbanBroadcastEvent {
  type: "candidate_stage_changed"
  candidate_id: string
  candidate_name: string
  vacancy_id: string
  from_stage: string
  to_stage: string
  sub_status: string
  moved_by: string
  ts: number
}

export function useKanbanBroadcast(jobId?: string) {
  const setCandidatesData = useKanbanStore((s) => s.setCandidatesData)
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)

  const handleEvent = useCallback(
    (event: KanbanBroadcastEvent) => {
      if (jobId && event.vacancy_id !== jobId) return

      setCandidatesData((prev) => {
        const updated = { ...prev }

        // Remove candidate from old stage
        if (updated[event.from_stage]) {
          updated[event.from_stage] = updated[event.from_stage].filter(
            (c) => (c as Record<string, unknown>).id !== event.candidate_id
          )
        }

        // Find candidate in any stage (may be in a different stage locally due to race)
        let movedCandidate: Record<string, unknown> | null = null
        for (const [stageId, candidates] of Object.entries(updated)) {
          const typedCandidates = candidates as Record<string, unknown>[]
          const idx = typedCandidates.findIndex(
            (c) => c.id === event.candidate_id
          )
          if (idx !== -1) {
            movedCandidate = { ...typedCandidates[idx] }
            updated[stageId] = [...typedCandidates.slice(0, idx), ...typedCandidates.slice(idx + 1)]
            break
          }
        }

        if (!movedCandidate) {
          // Candidate not in local state (new to this board or already removed)
          // Add a minimal stub so the card appears
          movedCandidate = {
            id: event.candidate_id,
            name: event.candidate_name,
            stage: event.to_stage,
            sub_status: event.sub_status || "pending",
            status: event.to_stage,
            needsAction: false,
          }
        }

        // Place candidate in new stage
        movedCandidate.stage = event.to_stage
        movedCandidate.etapa = event.to_stage
        movedCandidate.sub_status = event.sub_status || (movedCandidate.sub_status as string) || "pending"
        movedCandidate.status = event.to_stage

        if (!updated[event.to_stage]) {
          updated[event.to_stage] = []
        }
        updated[event.to_stage] = [...updated[event.to_stage], movedCandidate]

        return updated
      })
    },
    [jobId, setCandidatesData]
  )

  useEffect(() => {
    mountedRef.current = true

    const connect = () => {
      if (!mountedRef.current) return

      const params = new URLSearchParams()
      if (jobId) params.set("job_id", jobId)

      const url = `/api/backend-proxy/kanban/events${params.toString() ? `?${params}` : ""}`
      const es = new EventSource(url)
      eventSourceRef.current = es

      es.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as KanbanBroadcastEvent
          if (data.type === "candidate_stage_changed") {
            handleEvent(data)
          }
        } catch {
          // ignore malformed
        }
      }

      es.onerror = () => {
        es.close()
        if (mountedRef.current) {
          // Reconnect with exponential backoff (cap at 30s)
          const delay = Math.min(5000 * Math.pow(1.5, 0), 30000)
          console.warn(`[kanban-broadcast] Disconnected, reconnecting in ${delay}ms`)
          reconnectTimerRef.current = setTimeout(connect, delay)
        }
      }
    }

    connect()

    return () => {
      mountedRef.current = false
      eventSourceRef.current?.close()
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
    }
  }, [jobId, handleEvent])
}
