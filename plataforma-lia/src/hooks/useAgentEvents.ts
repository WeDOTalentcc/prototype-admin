"use client"

/**
 * useAgentEvents — React hook for agent lifecycle events (FIX-P0-03).
 *
 * Subscribes to real-time agent events for a chat session and exposes
 * typed state for the UI:
 *   - thinking: whether the agent is currently processing
 *   - currentAction: the action being executed (null when idle)
 *   - lastResult: the most recent action result
 *   - contextUpdate: the last page/UI state change received
 *   - isActive: alias for (thinking || currentAction !== null)
 *
 * Usage:
 *   const { thinking, currentAction, lastResult } = useAgentEvents(sessionId)
 *
 *   // In JSX:
 *   {thinking && <span>Processing...</span>}
 *   {currentAction && <LoadingIndicator label={currentAction.action_name} />}
 *   {lastResult?.status === "error" && <ErrorBanner message={lastResult.payload?.error} />}
 */

import { useEffect, useRef, useState, useCallback } from "react"
import {
  AgentEventListener,
  AgentEventPayload,
  AgentEventStatus,
} from "@/lib/agentEventListener"

export interface AgentActionState {
  action_name: string
  status: AgentEventStatus
  payload: Record<string, unknown>
  message_id: string
  timestamp: number
}

export interface AgentEventsState {
  thinking: boolean
  currentAction: AgentActionState | null
  lastResult: AgentActionState | null
  contextUpdate: AgentActionState | null
  isActive: boolean
}

const INITIAL_STATE: AgentEventsState = {
  thinking: false,
  currentAction: null,
  lastResult: null,
  contextUpdate: null,
  isActive: false,
}

function toActionState(ev: AgentEventPayload): AgentActionState {
  return {
    action_name: ev.action_name,
    status: ev.status,
    payload: ev.payload,
    message_id: ev.message_id,
    timestamp: ev.timestamp,
  }
}

export function useAgentEvents(sessionId: string | null): AgentEventsState {
  const [state, setState] = useState<AgentEventsState>(INITIAL_STATE)
  const listenerRef = useRef<AgentEventListener | null>(null)

  const handleThinking = useCallback((ev: AgentEventPayload) => {
    setState((prev) => ({
      ...prev,
      thinking: true,
      isActive: true,
    }))
  }, [])

  const handleAction = useCallback((ev: AgentEventPayload) => {
    setState((prev) => ({
      ...prev,
      currentAction: toActionState(ev),
      isActive: true,
    }))
  }, [])

  const handleActionResult = useCallback((ev: AgentEventPayload) => {
    setState((prev) => ({
      ...prev,
      thinking: false,
      currentAction: null,
      lastResult: toActionState(ev),
      isActive: false,
    }))
  }, [])

  const handleContextUpdate = useCallback((ev: AgentEventPayload) => {
    setState((prev) => ({
      ...prev,
      contextUpdate: toActionState(ev),
    }))
  }, [])

  useEffect(() => {
    if (!sessionId) {
      // Reset state and close any existing listener
      if (listenerRef.current) {
        listenerRef.current.close()
        listenerRef.current = null
      }
      setState(INITIAL_STATE)
      return
    }

    // Close previous listener if session changed
    if (listenerRef.current) {
      listenerRef.current.close()
      listenerRef.current = null
    }

    const listener = new AgentEventListener(sessionId)
    listener
      .on("agent_thinking", handleThinking)
      .on("agent_action", handleAction)
      .on("agent_action_result", handleActionResult)
      .on("agent_context_update", handleContextUpdate)

    listener.connect()
    listenerRef.current = listener

    return () => {
      listener.close()
      listenerRef.current = null
    }
  }, [sessionId, handleThinking, handleAction, handleActionResult, handleContextUpdate])

  return state
}
