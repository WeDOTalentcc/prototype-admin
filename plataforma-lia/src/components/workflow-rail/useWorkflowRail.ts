import { useState, useEffect, useCallback, useRef } from "react"

// ---------- Types ----------

export interface WorkflowStage {
  stage: string
  label: string
  status: "completed" | "in_progress" | "pending"
  candidatesCount: number
  checkpoint?: string | null
}

export interface WorkflowPendingAction {
  message: string
  candidatesCount?: number
  actionUrl?: string
}

export interface WorkflowEntry {
  id: string
  type: "campaign" | "pool" | "search"
  name: string
  currentStage?: string
  stages?: WorkflowStage[]
  pendingAction?: WorkflowPendingAction | null
  jobId?: string | number | null
  talentPoolId?: string | null
  searchResults?: { count: number; query: string } | null
  createdAt: string
  expiresAt?: string | null  // for search entries (auto-dismiss after 30min)
}

// ---------- Hook ----------

/**
 * useWorkflowRail — manages active workflow entries with real-time updates.
 *
 * - Loads initial entries from API on mount
 * - Connects to ActionCable WorkflowChannel for real-time updates
 * - Auto-dismisses search entries after 30min
 * - Provides methods to add/dismiss entries
 */
export function useWorkflowRail(userId: string) {
  const [entries, setEntries] = useState<WorkflowEntry[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load initial entries from API
  const loadEntries = useCallback(async () => {
    try {
      const res = await fetch("/api/backend-proxy/recruitment-campaigns?status=active")
      const data = await res.json()
      const campaigns = (data?.data || []).map(
        (d: { id: string; attributes: Record<string, unknown> }) => mapCampaignToEntry(d)
      )
      setEntries(prev => {
        // Merge: keep search entries, replace campaign entries
        const searches = prev.filter(e => e.type === "search")
        return [...campaigns, ...searches]
      })
    } catch (err) {
      console.error("[WorkflowRail] Failed to load entries:", err)
    }
  }, [])

  // Connect to ActionCable for real-time updates
  const connectWebSocket = useCallback(() => {
    if (!userId) return

    const railsWsUrl = process.env.NEXT_PUBLIC_RAILS_WS_URL || ""
    if (!railsWsUrl) {
      // Fallback to polling if no WebSocket URL
      startPolling()
      return
    }

    try {
      const token = document.cookie.match(/auth_token=([^;]+)/)?.[1] || ""
      const ws = new WebSocket(`${railsWsUrl}/cable?auth_token=${token}`)

      ws.onopen = () => {
        setIsConnected(true)
        // Subscribe to WorkflowChannel
        ws.send(JSON.stringify({
          command: "subscribe",
          identifier: JSON.stringify({ channel: "WorkflowChannel" }),
        }))
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === "ping" || data.type === "welcome" || data.type === "confirm_subscription") return

          const msg = data.message
          if (msg?.type === "campaign_update") {
            handleCampaignUpdate(msg)
          }
        } catch {
          // Ignore parse errors
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        // Reconnect after 5s
        setTimeout(connectWebSocket, 5000)
      }

      ws.onerror = () => {
        ws.close()
      }

      wsRef.current = ws
    } catch {
      startPolling()
    }
  }, [userId])

  const startPolling = useCallback(() => {
    if (pollingRef.current) return
    pollingRef.current = setInterval(loadEntries, 30000) // Poll every 30s
  }, [loadEntries])

  const handleCampaignUpdate = useCallback((msg: Record<string, unknown>) => {
    setEntries(prev => {
      const idx = prev.findIndex(e => e.id === msg.campaign_id)
      const updated: WorkflowEntry = {
        id: msg.campaign_id as string,
        type: "campaign",
        name: msg.name as string,
        currentStage: msg.current_stage as string,
        stages: (msg.stages as WorkflowStage[]) || [],
        jobId: msg.job_id as string | null,
        talentPoolId: msg.talent_pool_id as string | null,
        pendingAction: null,
        createdAt: new Date().toISOString(),
      }

      // Check for checkpoint pending action
      const currentStageData = updated.stages?.find(s => s.status === "in_progress")
      if (currentStageData?.checkpoint) {
        updated.pendingAction = {
          message: currentStageData.checkpoint,
          candidatesCount: currentStageData.candidatesCount,
        }
      }

      if (idx >= 0) {
        const next = [...prev]
        next[idx] = updated
        return next
      }
      return [updated, ...prev]
    })
  }, [])

  // Add a search entry (called when user performs a search)
  const addSearchEntry = useCallback((query: string, count: number) => {
    const entry: WorkflowEntry = {
      id: `search-${Date.now()}`,
      type: "search",
      name: `Busca: "${query}"`,
      searchResults: { count, query },
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30min
    }
    setEntries(prev => [entry, ...prev])
  }, [])

  // Dismiss an entry
  const dismissEntry = useCallback((entryId: string) => {
    setEntries(prev => prev.filter(e => e.id !== entryId))
  }, [])

  // Auto-dismiss expired search entries
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      setEntries(prev => prev.filter(e => {
        if (e.expiresAt && new Date(e.expiresAt) < now) return false
        return true
      }))
    }, 60000) // Check every minute

    return () => clearInterval(interval)
  }, [])

  // Init
  useEffect(() => {
    loadEntries()
    connectWebSocket()

    return () => {
      wsRef.current?.close()
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [loadEntries, connectWebSocket])

  return { entries, isConnected, addSearchEntry, dismissEntry, loadEntries }
}

// ---------- Helpers ----------

function mapCampaignToEntry(raw: { id: string; attributes: Record<string, unknown> }): WorkflowEntry {
  const a = raw.attributes
  const stages = (a.stages as WorkflowStage[]) || []
  const pendingAction = a.pending_action as WorkflowPendingAction | null

  return {
    id: raw.id,
    type: "campaign",
    name: a.name as string,
    currentStage: a.current_stage as string,
    stages: stages.map(s => ({
      stage: s.stage,
      label: s.label,
      status: s.status,
      candidatesCount: s.candidatesCount || 0,
      checkpoint: s.checkpoint,
    })),
    pendingAction: pendingAction ? {
      message: pendingAction.message,
      candidatesCount: pendingAction.candidatesCount,
    } : null,
    jobId: a.job_id as string | null,
    talentPoolId: a.talent_pool_id as string | null,
    createdAt: a.created_at as string,
  }
}
