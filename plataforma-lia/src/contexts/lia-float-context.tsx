"use client";

import {
  type BackgroundTaskEvent,
  type HITLPending,
  type LiaChatMessage,
  type PanelUpdateEvent,
  type TransportMode,
  formatMessageTime,
} from "@/hooks/chat/lia-chat-connection-types";
import type { FloatMessage } from "@/hooks/chat/use-float-conversation";
import { useLiaChatConnection } from "@/hooks/chat/use-lia-chat-connection";
import { useUIAction } from "@/hooks/chat/useUIAction";
import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";

export interface SplitViewState {
  active: boolean;
  page: string | null;
  conversationId: string | null;
}

export interface EntityContext {
  type: "candidate" | "job" | null;
  id?: string | number;
  name?: string;
  meta?: Record<string, unknown>;
}

export type DynamicPanelType =
  | "calibration"
  | "candidate_review"
  | "profile"
  | "job_creation"
  | "scheduling"
  | "agent_creation_preview"
  | "agent_details"
  | "agent_metrics";

export interface DynamicPanelData {
  panelType: DynamicPanelType;
  data: Record<string, unknown>;
  title?: string;
  stage?: string | null;
  requires_approval?: boolean;
}

/**
 * PR-A FE — Map active dynamic panel → CascadedRouter `domain_hint`.
 *
 * When a dynamic panel is active, every outbound chat message gets enriched
 * with `metadata.{source: "rail_a", domain_hint}` so the backend Tier -1
 * (`rail_a_hint_override.try_hint_route`) routes deterministically with
 * confidence=0.99, bypassing vector cache / fast router / LLM tiers.
 *
 * Without this guide, mid-wizard messages like "qual competência?" leak
 * into `job_management` via the vector cache (≥0.85 cosine similarity).
 *
 * Add new panel→domain mappings here as new panel types are introduced.
 * Domains must be registered in `DomainRegistry` (backend allowlist) — drift
 * gracefully falls back to normal routing.
 *
 * Skill canônica: harness-engineering [guide computacional].
 */
const PANEL_TYPE_TO_DOMAIN_HINT: Partial<Record<DynamicPanelType, string>> = {
  job_creation: "wizard",
  // Future mappings (TBD with backend):
  // calibration: "calibration",
  // scheduling: "scheduling",
  // candidate_review: "candidate_evaluation",
  // profile: "candidate_profile",
};

/**
 * Bug 5 fix (2026-05-24): mapeia ChatContextType (FE state) para
 * Rail A domain_hint (BE roteamento). Usado como FALLBACK quando não
 * há dynamicPanel ativo. Sem isso, chat lateral em /configuracoes
 * caía no roteador default e era atribuído a recruiter_assistant
 * (que não tem analyze_company_website / save_company_field / etc).
 *
 * Domínios DEVEM estar registrados em DomainRegistry backend (@register_domain).
 * Drift cai graceful no roteamento normal.
 */
const CONTEXT_TYPE_TO_DOMAIN_HINT: Partial<Record<ChatContextType, string>> = {
  // general: undefined  // default routing (CascadedRouter decide)
  job_chat: "job_management",
  talent_chat: "talent_pool",
  kanban_chat: "pipeline_transition",
  candidates_chat: "cv_screening",
  agent_studio: "agent_studio",
  settings_config: "company_settings",
};

export type ChatContextType =
  | "general"
  | "job_chat"
  | "talent_chat"
  | "kanban_chat"
  | "candidates_chat"
  | "agent_studio"
  | "settings_config";

interface LiaFloatState {
  isOpen: boolean;
  isExpanded: boolean;
  conversationId: string | null;
  splitView: SplitViewState;
  contextPage: string | null;
  entityContext: EntityContext | null;
  dynamicPanel: DynamicPanelData | null;
  hasInlineChat: boolean;
}

interface LiaFloatContextType extends LiaFloatState {
  open: (conversationId?: string) => void;
  close: () => void;
  toggle: () => void;
  expand: () => void;
  collapse: () => void;
  closeAll: () => void;
  navigateToChat: (conversationId?: string) => void;
  setContextPage: (page: string | null) => void;
  setEntityContext: (ctx: EntityContext | null) => void;
  openWithEntity: (entity: EntityContext) => void;
  openSplitView: (page: string, conversationId?: string) => void;
  closeSplitView: () => void;
  setHasInlineChat: (active: boolean) => void;
  openDynamicPanel: (panel: DynamicPanelData) => void;
  closeDynamicPanel: () => void;
  updateDynamicPanelData: (data: Record<string, unknown>) => void;

  sharedMessages: FloatMessage[];
  addSharedMessage: (msg: FloatMessage) => void;
  setSharedMessages: React.Dispatch<React.SetStateAction<FloatMessage[]>>;
  sharedConversationId: string | null;
  setSharedConversationId: (id: string | null) => void;

  chatMessages: LiaChatMessage[];
  addChatMessage: (msg: LiaChatMessage) => void;
  setChatMessages: React.Dispatch<React.SetStateAction<LiaChatMessage[]>>;
  chatConversationId: string | null;
  setChatConversationId: (id: string | null) => void;
  chatContextType: ChatContextType;
  setChatContextType: (type: ChatContextType) => void;
  switchChatContext: (
    newType: ChatContextType,
    options?: {
      conversationId?: string | null;
      continuePrevious?: boolean;
      resetConversation?: boolean;
    },
  ) => string | null;
  previousConversationId: string | null;

  sendChatMessage: (
    content: string,
    domain?: string,
    scope?: string,
    /** PR-A: metadata estruturada de origem do command (Rail A, slash, etc). */
    metadata?: Record<string, unknown>,
  ) => Promise<void>;
  sendOrchestratedMessage: (
    message: string,
    apiCall: (conversationId: string | null) => Promise<{
      content: string;
      conversation_id?: string | null;
      [key: string]: unknown;
    }>,
    options?: {
      extractResponseMetadata?: (response: {
        content: string;
        conversation_id?: string | null;
        [key: string]: unknown;
      }) => Record<string, unknown>;
      conversationId?: string | null;
    },
  ) => Promise<{
    content: string;
    conversation_id?: string | null;
    [key: string]: unknown;
  }>;
  initChatConversation: (firstMessage: string) => Promise<string | null>;
  loadChatHistory: (id: string) => Promise<LiaChatMessage[]>;
  sendApproval: (approved: boolean) => void;
  chatIsConnected: boolean;
  chatTransportMode: TransportMode;
  chatIsReconnecting: boolean;
  chatIsStreaming: boolean;
  chatStreamingContent: string;
  chatHitlPending: HITLPending | null;
  chatBackgroundTasks: BackgroundTaskEvent[];
  clearBackgroundTask: (taskId: string) => void;
  resetBackgroundTasks: () => void;
  /** Stable WS session id used by the chat socket — exposed so callers
   *  that POST a server-side background job (e.g. JD upload) can forward
   *  it as `?session_id=` and have the worker publish updates back. */
  chatSessionId: string;
  seedBackgroundTask: (event: BackgroundTaskEvent) => void;
  chatIsCreating: boolean;
  chatIsFetchingHistory: boolean;
  chatIsThinking: boolean;
  chatThinkingSteps: string[];
  chatPlanProgressSteps: Array<{
    task_id: string;
    action_id: string;
    domain_id: string;
    status: string;
  }>;
  chatActivePlanId: string | null;
  chatFairnessWarnings: string[];
  dismissFairnessWarnings: () => void;
  connectChat: () => void;
  disconnectChat: () => void;
  pendingPrefill: string | null;
  clearPendingPrefill: () => void;
}

const LiaFloatContext = createContext<LiaFloatContextType | undefined>(
  undefined,
);

const INITIAL_SPLIT_VIEW: SplitViewState = {
  active: false,
  page: null,
  conversationId: null,
};

function generateSessionId(): string {
  return `lia-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

const SESSION_STORAGE_KEY = "lia.wizard.session_id";

// Task #1097 — persist the current chat conversation id across reloads so the
// frontend can replay history (`/conversations/{id}`) after the user refreshes
// mid-wizard. Without this, the right-side wizard panel would be hydrated from
// the backend resume payload but the chat surface would appear blank until the
// next user turn. Stored in sessionStorage (same lifecycle as `session_id`) so
// closing the tab still resets the chat — only refresh / soft-nav restores it.
const CHAT_CONVERSATION_STORAGE_KEY = "lia.chat.conversation_id";

function loadStoredConversationId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = window.sessionStorage.getItem(CHAT_CONVERSATION_STORAGE_KEY);
    return stored && stored.length > 0 ? stored : null;
  } catch {
    return null;
  }
}

function persistConversationId(id: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (id && id.length > 0) {
      window.sessionStorage.setItem(CHAT_CONVERSATION_STORAGE_KEY, id);
    } else {
      window.sessionStorage.removeItem(CHAT_CONVERSATION_STORAGE_KEY);
    }
  } catch {
    /* sessionStorage unavailable — degrade silently */
  }
}

function loadOrCreateSessionId(): string {
  if (typeof window === "undefined") {
    return generateSessionId();
  }
  try {
    const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (existing && existing.length > 0) {
      return existing;
    }
    const fresh = generateSessionId();
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, fresh);
    return fresh;
  } catch {
    return generateSessionId();
  }
}

export function LiaFloatProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LiaFloatState>({
    isOpen: false,
    isExpanded: false,
    conversationId: null,
    splitView: INITIAL_SPLIT_VIEW,
    contextPage: null,
    entityContext: null,
    dynamicPanel: null,
    hasInlineChat: false,
  });

  const [sharedConversationId, setSharedConversationId] = useState<
    string | null
  >(null);

  const [chatMessages, setChatMessages] = useState<LiaChatMessage[]>([]);
  const sharedMessages = chatMessages;
  const setSharedMessages = setChatMessages;
  const addSharedMessage = useCallback((msg: FloatMessage) => {
    setChatMessages((prev) => [...prev, msg]);
  }, []);

  const [chatContextType, setChatContextType] =
    useState<ChatContextType>("general");
  const chatContextTypeRef = useRef<ChatContextType>("general");
  const [previousConversationId, setPreviousConversationId] = useState<
    string | null
  >(null);
  const contextConversationMapRef = useRef<Map<ChatContextType, string>>(
    new Map(),
  );

  const [sessionId] = useState(() => loadOrCreateSessionId());
  const [pendingPrefill, setPendingPrefill] = useState<string | null>(null);

  const { dispatchOrEmit: dispatchUIAction } = useUIAction();

  // Global listener: captures lia:prefill-message dispatched from any surface
  // (settings conversational, wizard panels, etc.) and stores as pendingPrefill.
  // Consumers (UnifiedChat, ChatPageFullscreen) read and clear via context.
  useEffect(() => {
    const handler = (ev: Event) => {
      const detail = (ev as CustomEvent).detail || {};
      const msg: string = detail.message || detail.text || "";
      if (msg) setPendingPrefill(msg);
    };
    window.addEventListener("lia:prefill-message", handler);
    return () => window.removeEventListener("lia:prefill-message", handler);
  }, []);

  const handleMessageComplete = useCallback(
    (
      content: string,
      executionPlan?: Record<string, unknown>,
      extras?: {
        options?: Array<{ label: string; value: string }>;
        isClarification?: boolean;
        ui_action?: string;
        ui_action_params?: Record<string, unknown>;
      },
    ) => {
      const msg: LiaChatMessage = {
        id: `lia-${Date.now()}`,
        sender: "lia" as const,
        content,
        timestamp: formatMessageTime(),
      };
      if (executionPlan) {
        msg.executionPlan = executionPlan;
      }
      if (extras?.options && extras.options.length > 0) {
        msg.options = extras.options;
      }
      if (extras?.isClarification) {
        msg.isClarification = true;
      }
      setChatMessages((prev) => [...prev, msg]);

      // PR-D — handler unificado de UIActions. Se o tipo for global,
      // useUIAction trata. Senão, re-emite via `lia:unhandled_ui_action`
      // CustomEvent para handlers page-specific (kanban, talent, jobs).
      if (extras?.ui_action) {
        dispatchUIAction(extras.ui_action, extras.ui_action_params ?? {});
      }
    },
    [dispatchUIAction],
  );

  const handlePanelUpdate = useCallback((event: PanelUpdateEvent) => {
    if (event.action === "open" || event.action === "update") {
      setState((prev) => ({
        ...prev,
        dynamicPanel: {
          panelType: event.panel_type as DynamicPanelType,
          data: event.panel_data,
          title: event.panel_title,
        },
      }));
    } else if (event.action === "close") {
      setState((prev) => ({ ...prev, dynamicPanel: null }));
    }
  }, []);

  const connection = useLiaChatConnection({
    sessionId,
    onMessageComplete: handleMessageComplete,
    onPanelUpdate: handlePanelUpdate,
  });

  const chatConversationId = connection.conversationId;
  const chatConversationIdRef = useRef(chatConversationId);
  // Bug 2 (2026-05-29): dynamicPanel via ref — sendChatMessage NAO pode
  // depender de state.dynamicPanel no dep array, senao recria a cada
  // wizard_stage e faz churn dos listeners de edit/regenerate WSI.
  const dynamicPanelRef = useRef(state.dynamicPanel);
  chatContextTypeRef.current = chatContextType;
  chatConversationIdRef.current = chatConversationId;
  dynamicPanelRef.current = state.dynamicPanel;
  const setChatConversationId = useCallback(
    (id: string | null) => {
      chatConversationIdRef.current = id;
      persistConversationId(id);
      connection.setConversationId(id);
    },
    [connection],
  );

  // Task #1097 — restore the persisted conversation id once after mount and
  // pull its history. Runs only when (a) sessionStorage has a value from the
  // previous tab lifetime AND (b) the connection has not already learned a
  // conversation id from the WS handshake. Guarded by a ref so it never
  // double-fires across React 18 StrictMode mounts.
  const didRestoreConversationRef = useRef(false);
  useEffect(() => {
    if (didRestoreConversationRef.current) return;
    if (chatConversationId) return; // WS already supplied one — nothing to restore
    const stored = loadStoredConversationId();
    if (!stored) return;
    didRestoreConversationRef.current = true;
    chatConversationIdRef.current = stored;
    connection.setConversationId(stored);
    void connection.loadHistory(stored).then((history) => {
      if (history.length > 0) {
        setChatMessages(history);
      }
    });
  }, [chatConversationId, connection]);

  // Mirror WS-derived conversation id into sessionStorage so it survives
  // refresh. The setChatConversationId callback covers explicit FE writes;
  // this effect catches the WS-driven path (`connection.conversationId`
  // populated by the `message` event in useChatSocket).
  useEffect(() => {
    if (chatConversationId) {
      persistConversationId(chatConversationId);
    }
  }, [chatConversationId]);

  const addChatMessage = useCallback((msg: LiaChatMessage) => {
    setChatMessages((prev) => [...prev, msg]);
  }, []);

  // Bidirectional sync (Task #712 + Paulo 2026-05-21): UI saves in any settings
  // hub broadcast `lia:settings-updated`. We absorb that into the chat as a
  // silent system note so LIA's next turn knows the user just changed
  // something via UI — and can react proactively (e.g. "vi que você definiu
  // missão como X, quer ajuda com visão alinhada?").
  //
  // 2026-05-21 enrichment: include field + value when present in the event
  // detail. The hook in use-company-settings-cards.ts already broadcasts both;
  // this template was discarding them and only showing section/method, which
  // gave LIA no leverage for follow-up. Truncation cap on `value` defends
  // against huge list/array dumps overwhelming the chat context window.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onUpdated = (e: Event) => {
      const detail = ((e as CustomEvent).detail || {}) as {
        actionId?: string;
        section?: string;
        field?: string;
        value?: unknown;
        url?: string;
        method?: string;
        source?: string;
        ts?: number;
      };
      const sectionLabel = detail.section || detail.actionId || "secao";
      // Format value compactly for chat context. Lists → first 3 + count,
      // strings → truncate to 200 chars, objects → JSON with 120-char cap.
      // Goal: enough signal for LIA to reason about the change, never a
      // wall of text.
      let valueText = "";
      if (detail.field && detail.value !== undefined && detail.value !== null) {
        const v = detail.value;
        if (Array.isArray(v)) {
          const head = v.slice(0, 3).map((x) => String(x)).join(", ");
          valueText = v.length > 3 ? `[${head}, +${v.length - 3}]` : `[${head}]`;
        } else if (typeof v === "string") {
          valueText = v.length > 200 ? `${v.slice(0, 200)}…` : v;
        } else if (typeof v === "object") {
          try {
            const j = JSON.stringify(v);
            valueText = j.length > 120 ? `${j.slice(0, 120)}…` : j;
          } catch {
            valueText = "[objeto]";
          }
        } else {
          valueText = String(v);
        }
      }
      const fieldClause = detail.field
        ? ` · campo "${detail.field}"${valueText ? ` = ${valueText}` : ""}`
        : "";
      // G5 canonical fix (2026-05-24): sender "system" (not "lia") so the
      // renderer skips this note. The content is a backstage hint for LIA,
      // not a user-facing reply. Sprint 2.4 (commit 5996e3c3 2026-05-26)
      // refinou para renderer respeitar metadata.silent (não polui transcript).
      //
      // G9 wire COMPLETO (Sprint 3.2/3.3/3.4 — 2026-05-26):
      //   - Sprint 3.2 (576e67ec) backend POST /api/v1/lia/proactive-context
      //     + Redis store TTL 30min
      //   - Sprint 3.3 (67ddb1b9) settings-notify.ts POSTa após debounce
      //   - Sprint 3.4 (0fd7f8f7) MainOrchestrator inject list_recent() no
      //     system_prompt antes de agentic_loop.run; LLM próximo turn vê
      //     contexto e reage proativamente (respeitando lia_persona
      //     Anti-pattern #1 — NUNCA enumere features).
      // Note local continua mantido em chatMessages SE !silent (Sprint 2.4).
      const note: LiaChatMessage = {
        id: `sys-settings-${detail.ts || Date.now()}`,
        sender: "system",
        content: `[contexto] Recrutador editou via UI: ${sectionLabel}${fieldClause}. Considere reagir proativamente (sugerir complementos, validar consistência, ou continuar silencioso se não houver follow-up útil).`,
        timestamp: formatMessageTime(),
        metadata: {
          system: true,
          source: "settings-sync",
          actionId: detail.actionId,
          section: detail.section,
          field: detail.field,
          silent: true,
        },
      };
      // Sprint 2.4 CR-3 (2026-05-26) — respeitar metadata.silent: NÃO
      // inserir em chatMessages quando silent=true. Antes do fix, system
      // notes "[contexto] Recrutador editou via UI" apareciam visualmente
      // no transcript apesar do flag silent (renderer não respeitava).
      // Polluía a conversa sem benefício — LLM backend nem vê (TODO G9
      // follow-up wire ainda pendente: POSTar pro backend pra LIA reagir
      // proativamente no próximo turno).
      if (!note.metadata?.silent) {
        setChatMessages((prev) => [...prev, note]);
      }
    };
    window.addEventListener("lia:settings-updated", onUpdated);
    return () => window.removeEventListener("lia:settings-updated", onUpdated);
  }, []);

  const switchChatContext = useCallback(
    (
      newType: ChatContextType,
      options?: {
        conversationId?: string | null;
        continuePrevious?: boolean;
        resetConversation?: boolean;
      },
    ): string | null => {
      // Opção A (Paulo 2026-05-29) — conversa GLOBAL contínua. A LIA flutuante
      // é UMA conversa que segue o recrutador por todas as páginas; navegar /
      // trocar de contexto NUNCA descarta a conversa. O contexto é metadado
      // (domain hint por mensagem), não um thread separado por tela. Reverte o
      // modelo thread-por-contexto da Task #1103 (causa raiz do "chat reset" /
      // Bug 4 + perda de histórico no reload / Bug 1). Só dois caminhos mexem
      // na conversa: (1) carregar conversa específica (conversationId string —
      // URL/sidebar); (2) reset explícito (resetConversation:true — "Nova
      // conversa", único reset autorizado).
      const loadConvId =
        typeof options?.conversationId === "string" &&
        options.conversationId.length > 0
          ? options.conversationId
          : null;
      const wantsReset = options?.resetConversation === true;

      const prevType = chatContextTypeRef.current;
      const isActualSwitch =
        prevType !== newType || loadConvId !== null || wantsReset;
      if (!isActualSwitch) {
        return chatConversationIdRef.current;
      }

      const currentConvId = chatConversationIdRef.current;
      if (currentConvId) {
        contextConversationMapRef.current.set(prevType, currentConvId);
      }
      setPreviousConversationId(currentConvId);

      // Tipo de contexto sempre atualiza (drive do domain hint / metadado).
      chatContextTypeRef.current = newType;
      setChatContextType(newType);

      if (loadConvId !== null) {
        // (1) Carregar uma conversa específica.
        persistConversationId(loadConvId);
        connection.setConversationId(loadConvId);
        chatConversationIdRef.current = loadConvId;
        return loadConvId;
      }

      if (wantsReset) {
        // (2) Reset explícito — única forma de zerar a conversa.
        persistConversationId(null);
        connection.setConversationId(null);
        chatConversationIdRef.current = null;
        setChatMessages([]);
        return null;
      }

      // Troca de contexto pura: preserva a conversa ativa intacta.
      return currentConvId;
    },
    [connection],
  );

  const sendChatMessage = useCallback(
    async (
      content: string,
      domain?: string,
      scope?: string,
      metadata?: Record<string, unknown>,
    ) => {
      addChatMessage({
        id: `user-${Date.now()}`,
        sender: "user",
        content,
        timestamp: formatMessageTime(),
      });

      // PR-A FE — enrich metadata with Rail A hint when a dynamic panel is
      // active so backend Tier -1 routes deterministically. See
      // PANEL_TYPE_TO_DOMAIN_HINT above for the mapping rationale. Caller
      // can override by passing explicit metadata.domain_hint.
      const activePanelType = dynamicPanelRef.current?.panelType;
      // Resolution chain: dynamicPanel → chatContextType → undefined (default routing).
      // panelType wins because it's a more specific signal (active wizard panel etc).
      const hintDomain =
        (activePanelType && PANEL_TYPE_TO_DOMAIN_HINT[activePanelType]) ||
        CONTEXT_TYPE_TO_DOMAIN_HINT[chatContextTypeRef.current] ||
        undefined;

      const enrichedMetadata =
        hintDomain && !metadata?.domain_hint
          ? {
              ...(metadata ?? {}),
              source: metadata?.source ?? "rail_a",
              card_id:
                metadata?.card_id ??
                (activePanelType
                  ? `panel_active:${activePanelType}`
                  : `context:${chatContextTypeRef.current}`),
              domain_hint: hintDomain,
            }
          : metadata;

      await connection.sendMessage(content, domain, scope, enrichedMetadata);
    },
    [connection, addChatMessage],
  );

  const sendOrchestratedMessage = useCallback(
    async (
      message: string,
      apiCall: (conversationId: string | null) => Promise<{
        content: string;
        conversation_id?: string | null;
        [key: string]: unknown;
      }>,
      options?: {
        extractResponseMetadata?: (response: {
          content: string;
          conversation_id?: string | null;
          [key: string]: unknown;
        }) => Record<string, unknown>;
        conversationId?: string | null;
      },
    ) => {
      const ts = formatMessageTime();
      addChatMessage({
        id: `user-${Date.now()}`,
        sender: "user",
        content: message,
        timestamp: ts,
      });
      const effectiveConvId =
        options?.conversationId !== undefined
          ? options.conversationId
          : chatConversationIdRef.current;
      const response = await apiCall(effectiveConvId);
      if (response.conversation_id) {
        setChatConversationId(response.conversation_id);
      }
      const metadata = options?.extractResponseMetadata?.(response);
      addChatMessage({
        id: `lia-${Date.now()}`,
        sender: "lia",
        content: response.content,
        timestamp: formatMessageTime(),
        metadata,
      });
      return response;
    },
    [setChatConversationId, addChatMessage],
  );

  const initChatConversation = useCallback(
    async (firstMessage: string) => {
      return connection.initConversation(firstMessage, chatContextType);
    },
    [connection, chatContextType],
  );

  const loadChatHistory = useCallback(
    async (id: string) => {
      const history = await connection.loadHistory(id);
      if (history.length > 0) {
        setChatMessages(history);
      }
      return history;
    },
    [connection],
  );

  const open = useCallback((conversationId?: string) => {
    setState((prev) => ({
      ...prev,
      isOpen: true,
      isExpanded: false,
      conversationId: conversationId ?? prev.conversationId,
    }));
  }, []);

  const close = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isOpen: false,
      entityContext: null,
      dynamicPanel: null,
    }));
  }, []);

  const toggle = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: !prev.isOpen }));
  }, []);

  const expand = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false, isExpanded: true }));
  }, []);

  const collapse = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: false, isOpen: true }));
  }, []);

  const closeAll = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isOpen: false,
      isExpanded: false,
      entityContext: null,
      dynamicPanel: null,
    }));
  }, []);

  const openSplitView = useCallback((page: string, conversationId?: string) => {
    setState((prev) => ({
      ...prev,
      isOpen: false,
      isExpanded: false,
      splitView: {
        active: true,
        page,
        conversationId: conversationId ?? prev.conversationId,
      },
    }));
  }, []);

  const closeSplitView = useCallback(() => {
    setState((prev) => ({ ...prev, splitView: INITIAL_SPLIT_VIEW }));
  }, []);

  const setContextPage = useCallback((page: string | null) => {
    setState((prev) => ({ ...prev, contextPage: page }));
  }, []);

  const setEntityContext = useCallback((ctx: EntityContext | null) => {
    setState((prev) => ({ ...prev, entityContext: ctx }));
  }, []);

  const openWithEntity = useCallback((entity: EntityContext) => {
    setState((prev) => ({
      ...prev,
      isOpen: true,
      isExpanded: false,
      entityContext: entity,
    }));
  }, []);

  const inlineChatCountRef = React.useRef(0);
  const setHasInlineChat = useCallback((active: boolean) => {
    inlineChatCountRef.current += active ? 1 : -1;
    if (inlineChatCountRef.current < 0) inlineChatCountRef.current = 0;
    setState((prev) => ({
      ...prev,
      hasInlineChat: inlineChatCountRef.current > 0,
    }));
  }, []);

  const openDynamicPanel = useCallback((panel: DynamicPanelData) => {
    setState((prev) => ({ ...prev, dynamicPanel: panel }));
  }, []);

  const closeDynamicPanel = useCallback(() => {
    setState((prev) => ({ ...prev, dynamicPanel: null }));
  }, []);

  // Bridge canonical (Fix B 2026-05-27 -- WIZARD_DEEP_DIVE P0-NOVO-#2):
  // Backend `agent_chat_ws.py` emite APENAS `wizard_stage` ao avancar de etapa
  // (nunca `panel_update`). `useChatSocket.ts:289` dispatcha o window event
  // `lia:wizard-stage-payload` mas NAO chama `openDynamicPanel`. Sem essa bridge,
  // `state.dynamicPanel` fica `null` durante todo o wizard, o gate
  // `hasDynamicPanel` falha, e o painel HITL nunca renderiza.
  //
  // Skill canonica: harness-engineering [guide computacional + sensor em
  // `lia-float-context.wizard-stage-bridge.test.ts`].
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = (e: Event) => {
      const detail = ((e as CustomEvent).detail ?? {}) as Record<string, unknown>;
      const stage = detail.stage as string | undefined;
      if (!stage) return; // payload incompleto -- ignora silenciosamente
      openDynamicPanel({
        panelType: "job_creation",
        data: (detail.data as Record<string, unknown>) ?? {},
        stage,
        requires_approval: Boolean(detail.requires_approval),
      });
    };
    window.addEventListener("lia:wizard-stage-payload", handler);
    return () =>
      window.removeEventListener("lia:wizard-stage-payload", handler);
  }, [openDynamicPanel]);

  const updateDynamicPanelData = useCallback(
    (data: Record<string, unknown>) => {
      setState((prev) => {
        if (!prev.dynamicPanel) return prev;
        return {
          ...prev,
          dynamicPanel: {
            ...prev.dynamicPanel,
            data: { ...prev.dynamicPanel.data, ...data },
          },
        };
      });
    },
    [],
  );

  const navigateToChat = useCallback((conversationId?: string) => {
    setState((prev) => ({
      ...prev,
      isOpen: false,
      isExpanded: false,
      splitView: INITIAL_SPLIT_VIEW,
    }));
    const convParam = conversationId
      ? `&conversation_id=${encodeURIComponent(conversationId)}`
      : "";
    if (document.querySelector("[data-dashboard-shell]")) {
      window.dispatchEvent(
        new CustomEvent("lia:navigate-chat-page", {
          detail: { conversationId },
        }),
      );
    } else {
      window.location.href = `/?page=chat-lia${convParam}`;
    }
  }, []);

  const value = useMemo<LiaFloatContextType>(
    () => ({
      ...state,
      open,
      close,
      toggle,
      expand,
      collapse,
      closeAll,
      navigateToChat,
      setContextPage,
      setEntityContext,
      openWithEntity,
      openSplitView,
      closeSplitView,
      setHasInlineChat,
      openDynamicPanel,
      closeDynamicPanel,
      updateDynamicPanelData,
      sharedMessages,
      addSharedMessage,
      setSharedMessages,
      sharedConversationId,
      setSharedConversationId,
      chatMessages,
      addChatMessage,
      setChatMessages,
      chatConversationId,
      setChatConversationId,
      chatContextType,
      setChatContextType,
      switchChatContext,
      previousConversationId,
      sendChatMessage,
      sendOrchestratedMessage,
      initChatConversation,
      loadChatHistory,
      sendApproval: connection.sendApproval,
      chatIsConnected: connection.isConnected,
      chatTransportMode: connection.transportMode,
      chatIsReconnecting: connection.isReconnecting,
      chatIsStreaming: connection.isStreaming,
      chatStreamingContent: connection.streamingContent,
      chatHitlPending: connection.hitlPending,
      chatBackgroundTasks: connection.backgroundTasks,
      clearBackgroundTask: connection.clearBackgroundTask,
      resetBackgroundTasks: connection.resetBackgroundTasks,
      chatSessionId: sessionId,
      seedBackgroundTask: connection.seedBackgroundTask,
      chatIsCreating: connection.isCreating,
      chatIsFetchingHistory: connection.isFetchingHistory,
      chatIsThinking: connection.isThinking,
      chatThinkingSteps: connection.thinkingSteps,
      chatPlanProgressSteps: connection.planProgressSteps,
      chatActivePlanId: connection.activePlanId,
      chatFairnessWarnings: connection.fairnessWarnings,
      dismissFairnessWarnings: connection.dismissFairnessWarnings,
      connectChat: connection.connect,
      disconnectChat: connection.disconnect,
      pendingPrefill,
      clearPendingPrefill: () => setPendingPrefill(null),
    }),
    [
      state,
      open,
      close,
      toggle,
      expand,
      collapse,
      closeAll,
      navigateToChat,
      setContextPage,
      setEntityContext,
      openWithEntity,
      openSplitView,
      closeSplitView,
      setHasInlineChat,
      openDynamicPanel,
      closeDynamicPanel,
      updateDynamicPanelData,
      sharedMessages,
      addSharedMessage,
      sharedConversationId,
      chatMessages,
      addChatMessage,
      chatConversationId,
      setChatConversationId,
      chatContextType,
      switchChatContext,
      previousConversationId,
      sendChatMessage,
      sendOrchestratedMessage,
      initChatConversation,
      loadChatHistory,
      connection.sendApproval,
      connection.isConnected,
      connection.transportMode,
      connection.isReconnecting,
      connection.isStreaming,
      connection.streamingContent,
      connection.hitlPending,
      connection.backgroundTasks,
      connection.clearBackgroundTask,
      connection.resetBackgroundTasks,
      sessionId,
      connection.seedBackgroundTask,
      connection.isCreating,
      connection.isFetchingHistory,
      connection.isThinking,
      connection.thinkingSteps,
      connection.planProgressSteps,
      connection.activePlanId,
      connection.fairnessWarnings,
      connection.dismissFairnessWarnings,
      connection.connect,
      connection.disconnect,
      setSharedMessages,
      pendingPrefill,
    ],
  );

  return (
    <LiaFloatContext.Provider value={value}>
      {children}
    </LiaFloatContext.Provider>
  );
}

export function useLiaFloat(): LiaFloatContextType {
  const ctx = useContext(LiaFloatContext);
  if (!ctx)
    throw new Error("useLiaFloat deve ser usado dentro de LiaFloatProvider");
  return ctx;
}

export function useLiaChatContext() {
  const ctx = useContext(LiaFloatContext);
  if (!ctx)
    throw new Error(
      "useLiaChatContext deve ser usado dentro de LiaFloatProvider",
    );
  return {
    chatMessages: ctx.chatMessages,
    addChatMessage: ctx.addChatMessage,
    setChatMessages: ctx.setChatMessages,
    chatConversationId: ctx.chatConversationId,
    setChatConversationId: ctx.setChatConversationId,
    chatContextType: ctx.chatContextType,
    setChatContextType: ctx.setChatContextType,
    switchChatContext: ctx.switchChatContext,
    previousConversationId: ctx.previousConversationId,
    sendChatMessage: ctx.sendChatMessage,
    sendOrchestratedMessage: ctx.sendOrchestratedMessage,
    initChatConversation: ctx.initChatConversation,
    loadChatHistory: ctx.loadChatHistory,
    sendApproval: ctx.sendApproval,
    chatIsConnected: ctx.chatIsConnected,
    chatTransportMode: ctx.chatTransportMode,
    chatIsReconnecting: ctx.chatIsReconnecting,
    chatIsStreaming: ctx.chatIsStreaming,
    chatStreamingContent: ctx.chatStreamingContent,
    chatHitlPending: ctx.chatHitlPending,
    chatBackgroundTasks: ctx.chatBackgroundTasks,
    clearBackgroundTask: ctx.clearBackgroundTask,
    resetBackgroundTasks: ctx.resetBackgroundTasks,
    chatSessionId: ctx.chatSessionId,
    seedBackgroundTask: ctx.seedBackgroundTask,
    chatIsCreating: ctx.chatIsCreating,
    chatIsFetchingHistory: ctx.chatIsFetchingHistory,
    chatIsThinking: ctx.chatIsThinking,
    chatThinkingSteps: ctx.chatThinkingSteps,
    chatPlanProgressSteps: ctx.chatPlanProgressSteps,
    chatActivePlanId: ctx.chatActivePlanId,
    chatFairnessWarnings: ctx.chatFairnessWarnings,
    dismissFairnessWarnings: ctx.dismissFairnessWarnings,
    connectChat: ctx.connectChat,
    disconnectChat: ctx.disconnectChat,
    isOpen: ctx.isOpen,
    isExpanded: ctx.isExpanded,
    open: ctx.open,
    close: ctx.close,
    expand: ctx.expand,
    collapse: ctx.collapse,
    navigateToChat: ctx.navigateToChat,
  };
}
