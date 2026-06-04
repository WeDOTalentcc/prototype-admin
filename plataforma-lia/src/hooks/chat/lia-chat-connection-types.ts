// Shared types for the use-lia-chat-connection hook family

/**
 * Quick-reply option attached to a clarification message.
 * Rendered as a clickable chip that, when pressed, sends `value` as the next user message.
 */
export interface LiaChatClarificationOption {
  label: string;
  value: string;
}

export interface LiaChatMessage {
  id: string;
  sender: "lia" | "user" | "system";
  content: string;
  timestamp: string;
  executionPlan?: Record<string, unknown>;
  planProgressSteps?: Array<{
    task_id: string;
    action_id: string;
    status: string;
  }>;
  metadata?: Record<string, unknown>;
  /**
   * Set by the cascaded router fallback (Tier 8) when no domain confidently
   * resolves the user's intent. Frontend renders `options` as clickable chips.
   */
  isClarification?: boolean;
  options?: LiaChatClarificationOption[];
  /**
   * Persisted feedback state for this LIA message (Task #570).
   * Hydrated from `/lia/feedback/by-conversation/{id}` on history load so
   * thumbs survive a refresh. `null` means "no feedback yet".
   */
  thumbs?: "up" | "down" | null;
  feedbackText?: string | null;
}

export interface HITLPending {
  pendingId: string;
  threadId: string;
  action: string;
  description: string;
  data: Record<string, unknown>;
}

export interface PanelUpdateEvent {
  panel_type: string;
  panel_data: Record<string, unknown>;
  panel_title?: string;
  action: "open" | "update" | "close";
}

export interface BackgroundTaskEvent {
  task_id: string;
  // `wizard` was added by the async JD-upload worker (Audit B-02 / Task #865)
  // so the chat surface can render the import progress alongside the
  // pre-existing sourcing/screening/communication/analysis lanes.
  task_type: "sourcing" | "screening" | "communication" | "analysis" | "wizard";
  label: string;
  // `queued` is the initial state seeded right after the proxy returns 202
  // and before the Celery worker fires its first `running` update — without
  // it the UI would jump from "nothing" to "running" or "failed".
  status: "queued" | "running" | "completed" | "failed";
  progress?: number;
  message?: string;
  result?: Record<string, unknown>;
}

/**
 * Optional extras attached to a completed message.
 * - `options`: clarification chips rendered as buttons under the message.
 * - `isClarification`: marks the message as a Tier 8 fallback so the UI can
 *   style it differently if desired.
 * - `ui_action` / `ui_action_params`: PR-D — UIAction string opcional vinda
 *   do orchestrator (ChatResponse.ui_action). Despachada pelo handler global
 *   `useUIAction` se for tipo conhecido, senão re-emitida via
 *   `lia:unhandled_ui_action` CustomEvent para handlers page-specific.
 */
export interface MessageCompleteExtras {
  options?: LiaChatClarificationOption[];
  isClarification?: boolean;
  ui_action?: string;
  ui_action_params?: Record<string, unknown>;
}

export interface UseLiaChatConnectionOptions {
  sessionId: string;
  onMessageComplete?: (
    content: string,
    executionPlan?: Record<string, unknown>,
    extras?: MessageCompleteExtras,
  ) => void;
  onPanelUpdate?: (event: PanelUpdateEvent) => void;
}

export type TransportMode = "ws" | "sse" | "disconnected";

export interface UseLiaChatConnectionResult {
  conversationId: string | null;
  setConversationId: (id: string | null) => void;
  isConnected: boolean;
  isStreaming: boolean;
  isReconnecting: boolean;
  reconnectAttempt: number;
  streamingContent: string;
  error: string | null;
  transportMode: TransportMode;
  isCreating: boolean;
  isFetchingHistory: boolean;
  hitlPending: HITLPending | null;
  thinkingSteps: string[];
  isThinking: boolean;
  fairnessWarnings: string[];
  backgroundTasks: BackgroundTaskEvent[];
  planProgressSteps: Array<{
    task_id: string;
    action_id: string;
    domain_id: string;
    status: string;
  }>;
  activePlanId: string | null;
  /** PR-A: aceita `metadata` opcional com hints de routing (Rail A). */
  sendMessage: (
    content: string,
    domain?: string,
    scope?: string,
    metadata?: Record<string, unknown>,
  ) => Promise<void>;
  sendApproval: (approved: boolean) => void;
  dismissFairnessWarnings: () => void;
  clearBackgroundTask: (taskId: string) => void;
  resetBackgroundTasks: () => void;
  /**
   * Seed (or overwrite by `task_id`) a single `BackgroundTaskEvent` into
   * the chat surface — used by callers that kick off a server-side
   * background job and want to render an immediate `queued` row before
   * the worker emits its first WS update (Audit B-02 / Task #865).
   */
  seedBackgroundTask: (event: BackgroundTaskEvent) => void;
  initConversation: (
    firstMessage: string,
    contextType?: string,
  ) => Promise<string | null>;
  loadHistory: (id: string) => Promise<LiaChatMessage[]>;
  connect: () => void;
  disconnect: () => void;
}

// ── Helpers ──

export function maskPII(text: string): string {
  return text
    .replace(/\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, "[CPF]")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, "[email]")
    .replace(
      /\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\d{4}|\d{4})-?\d{4}\b/g,
      "[tel]",
    );
}

export function formatMessageTime(isoDate?: string): string {
  const d = isoDate ? new Date(isoDate) : new Date();
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}


// ── Canonical message id (collision-safe) ──

/**
 * Monotonic per-session counter. `Date.now()` alone is NOT a safe React key:
 * two messages minted in the same millisecond — a turn that emits a text reply
 * plus an action/candidate card in one synchronous tick, or a loop of cards —
 * collide → "Encountered two children with the same key" → the message list
 * crashes (UnifiedMessageList). The counter guarantees uniqueness within the
 * tab session; the timestamp keeps ids sortable + debuggable.
 *
 * Canonical: every chat message id MUST be minted here (or via `dedupeAppend`),
 * never with an inline `` `${prefix}-${Date.now()}` `` literal.
 */
let _messageIdSeq = 0

export function createMessageId(prefix: string): string {
  _messageIdSeq += 1
  return `${prefix}-${Date.now()}-${_messageIdSeq}`
}

/**
 * Append `incoming` to `list` while guaranteeing the array never holds two
 * items with the same `id` (the React-key invariant for every chat surface).
 * If the id already exists — e.g. a backend that emits a message frame and a
 * card frame sharing one id — the incoming item is KEPT (lossless) under a
 * uniquified id instead of being dropped. Pure: returns a new array, never
 * mutates the input.
 */
export function dedupeAppend(
  list: LiaChatMessage[],
  incoming: LiaChatMessage,
): LiaChatMessage[] {
  if (list.some((m) => m.id === incoming.id)) {
    return [...list, { ...incoming, id: createMessageId(incoming.id) }]
  }
  return [...list, incoming]
}
