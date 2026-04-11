// Shared types for the use-lia-chat-connection hook family

export interface LiaChatMessage {
  id: string
  sender: "lia" | "user"
  content: string
  timestamp: string
  executionPlan?: Record<string, unknown>
  planProgressSteps?: Array<{ task_id: string; action_id: string; status: string }>
  metadata?: Record<string, unknown>
}

export interface HITLPending {
  pendingId: string
  threadId: string
  action: string
  description: string
  data: Record<string, unknown>
}

export interface PanelUpdateEvent {
  panel_type: string
  panel_data: Record<string, unknown>
  panel_title?: string
  action: "open" | "update" | "close"
}

export interface BackgroundTaskEvent {
  task_id: string
  task_type: "sourcing" | "screening" | "communication" | "analysis"
  label: string
  status: "running" | "completed" | "failed"
  progress?: number
  message?: string
  result?: Record<string, unknown>
}

export interface UseLiaChatConnectionOptions {
  sessionId: string
  onMessageComplete?: (content: string, executionPlan?: Record<string, unknown>) => void
  onPanelUpdate?: (event: PanelUpdateEvent) => void
}

export type TransportMode = "ws" | "sse" | "disconnected"

export interface UseLiaChatConnectionResult {
  conversationId: string | null
  setConversationId: (id: string | null) => void
  isConnected: boolean
  isStreaming: boolean
  isReconnecting: boolean
  reconnectAttempt: number
  streamingContent: string
  error: string | null
  transportMode: TransportMode
  isCreating: boolean
  isFetchingHistory: boolean
  hitlPending: HITLPending | null
  thinkingSteps: string[]
  isThinking: boolean
  fairnessWarnings: string[]
  backgroundTasks: BackgroundTaskEvent[]
  planProgressSteps: Array<{ task_id: string; action_id: string; domain_id: string; status: string }>
  activePlanId: string | null
  sendMessage: (content: string, domain?: string, scope?: string) => Promise<void>
  sendApproval: (approved: boolean) => void
  dismissFairnessWarnings: () => void
  clearBackgroundTask: (taskId: string) => void
  resetBackgroundTasks: () => void
  initConversation: (firstMessage: string, contextType?: string) => Promise<string | null>
  loadHistory: (id: string) => Promise<LiaChatMessage[]>
  connect: () => void
  disconnect: () => void
}

// ── Helpers ──

export function maskPII(text: string): string {
  return text
    .replace(/\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, "[CPF]")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, "[email]")
    .replace(/\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\d{4}|\d{4})-?\d{4}\b/g, "[tel]")
}

export function formatMessageTime(isoDate?: string): string {
  const d = isoDate ? new Date(isoDate) : new Date()
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}
