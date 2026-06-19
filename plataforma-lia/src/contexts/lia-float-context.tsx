"use client";
import type { ResponseBlock } from "@/types/rrp-blocks";

import {
  type BackgroundTaskEvent,
  type HITLPending,
  type LiaChatMessage,
  type PanelUpdateEvent,
  type TransportMode,
  formatMessageTime,
  createMessageId,
  dedupeAppend,
} from "@/hooks/chat/lia-chat-connection-types";
import type { FloatMessage } from "@/hooks/chat/use-float-conversation";
import { useLiaChatConnection } from "@/hooks/chat/use-lia-chat-connection";
import { usePathname } from "next/navigation";
import { routeToCanonicalPage, CANONICAL_PAGES } from "@/lib/canonical-pages";
import { useUIAction } from "@/hooks/chat/useUIAction";
import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import { useAuthStore } from "@/stores/auth-store";

/** Maps canonical page IDs to badge display labels. */
const CANONICAL_PAGE_DISPLAY: Partial<Record<string, string>> = {
  home: "Início",
  vagas: "Vagas",
  recrutar: "Visão Global",
  pipeline_kanban: "Visão Global",
  funil_talentos: "Funil de Talentos",
  dashboard: "Indicadores",
  configuracoes: "Configurações",
  agent_studio: "Estúdio de Agentes",
  ajuda: "Ajuda",
  bancos_talentos: "Bancos de Talentos",
  biblioteca: "Biblioteca LIA",
  central_comunicacao: "Central de Comunicação",
  tasks: "Decidir",
  chat: "Conversar",
  trust: "Conformidade",
  agents_marketplace: "Marketplace de Agentes",
  ai_credits: "Créditos de IA",
  integracoes_ats: "Integrações ATS",
  vaga_detalhe: "Vaga",
  candidato_detalhe: "Candidato",
}

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
  enterFullscreen: () => void;
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
  /** Manus F1 — modo do painel do wizard: dock lateral ou expandido. */
  wizardPanelMode: "docked" | "expanded";
  setWizardPanelMode: (mode: "docked" | "expanded") => void;
  /** Manus F3 - recrutador dispensou o consent card. */
  wizardConsentDeclined: boolean;
  setWizardConsentDeclined: (v: boolean) => void;

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
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
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

  // Manus F1 — modo do painel do wizard (sticky; fora de LiaFloatState
  // pra nao ser zerado pelos resets de close()/closeAll()).
  const [wizardPanelMode, setWizardPanelModeState] = useState<
    "docked" | "expanded"
  >("docked");
  // Manus F3 - recrutador dispensou o consent card de tela cheia
  const [wizardConsentDeclined, setWizardConsentDeclined] = useState(false);
  // Manus F1 sticky fix — rastreia se o usuário expandiu manualmente nesta sessão
  // do wizard para evitar reset indevido quando backend emite "done" intermediário.
  const userExpandedRef = useRef(false);
  const setWizardPanelMode = useCallback(
    (mode: "docked" | "expanded") => {
      if (mode === "expanded") {
        userExpandedRef.current = true;
      }
      setWizardPanelModeState(mode);
    },
    [],
  );

  const [sharedConversationId, setSharedConversationId] = useState<
    string | null
  >(null);

  const [chatMessages, setChatMessages] = useState<LiaChatMessage[]>([]);
  const sharedMessages = chatMessages;
  const setSharedMessages = setChatMessages;
  const addSharedMessage = useCallback((msg: FloatMessage) => {
    setChatMessages((prev) => dedupeAppend(prev, msg));
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

  // Badge context: update contextPage reactively to URL changes.
  // Covers pages outside DashboardApp shell (Agent Studio, Trust, etc.)
  // DashboardApp.setContextPage() fires AFTER this, so its explicit label
  // takes precedence for sub-pages it manages. Both converge to the same value.
  const _pathname = usePathname();
  useEffect(() => {
    const canonical = routeToCanonicalPage(_pathname);
    if (canonical === CANONICAL_PAGES.GENERAL) return; // unknown page — keep prev label
    const label = CANONICAL_PAGE_DISPLAY[canonical];
    if (label) {
      setState((prev) => {
        const needsPageChange = prev.contextPage !== label;
        // Do NOT clear entityContext here. Its lifecycle is managed
        // exclusively by lia:set-vacancy-context events and explicit
        // setEntityContext(null) on preview close / hard reset.
        // Clearing on every pathname change causes the wizard to lose
        // vacancy_id on any sidebar navigation (P0 #1, fixed 2026-06-19).
        if (!needsPageChange) return prev;
        return {
          ...prev,
          contextPage: label,
        };
      });
    }
  }, [_pathname]);
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
        agent_activity?: Array<{
          kind: string;
          name: string;
          status: string;
          durationMs?: number;
        }>;
        ws_stage_payload?: {
          stage: string
          data: Record<string, unknown>
          completeness?: number
          requires_approval?: boolean
        }
      },
    ) => {
      const msg: LiaChatMessage = {
        id: createMessageId("lia"),
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
      if (extras?.agent_activity && extras.agent_activity.length > 0) {
        msg.metadata = {
          ...(msg.metadata ?? {}),
          agent_activity: extras.agent_activity,
        };
      }
      const _rb = (extras as { response_blocks?: ResponseBlock[] } | undefined)
        ?.response_blocks;
      if (_rb && _rb.length > 0) {
        msg.response_blocks = _rb;
      }
      // F2 wizard: se o frame carregou ws_stage_payload de stage que gera card,
      // popular msg.metadata para que UnifiedMessageList renderize o card inline.
      const _wsp = extras?.ws_stage_payload;
      if (_wsp) {
        const _CARD_STAGES = ["publish", "done"]
        if (_CARD_STAGES.includes(_wsp.stage)) {
          msg.metadata = {
            ...(msg.metadata ?? {}),
            type: "wizard_stage_card",
            wizardStage: _wsp.stage,
            wizardStageData: _wsp.data,
            wizardRequiresApproval: _wsp.requires_approval ?? false,
          }
        }
      }
      setChatMessages((prev) => dedupeAppend(prev, msg));

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
    // Fonte unica (fix 2026-06-05 wizard panel close): o painel do wizard e
    // propriedade EXCLUSIVA da ponte lia:wizard-stage-payload, que chama
    // openDynamicPanel COM o campo stage. handlePanelUpdate grava um shape SEM
    // stage; se ele processar um frame panel_type wizard_stage, derruba o gate
    // hasDynamicPanel (SPLIT_STAGES.includes(undefined)) no 2o turno do mesmo
    // stage -- justamente quando maybeDispatchWizardStage foi deduplicada.
    // Ignorar aqui = single source of truth. Sensor:
    // __tests__/lia-float-wizard-panel-stage.test.ts.
    if (event.panel_type === "wizard_stage") return
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
  // B3b (2026-06-09): entityContextRef mirrors dynamicPanelRef pattern — avoids
  // stale closure in sendChatMessage when entityContext changes.
  const entityContextRef = useRef(state.entityContext);
  chatContextTypeRef.current = chatContextType;
  chatConversationIdRef.current = chatConversationId;
  dynamicPanelRef.current = state.dynamicPanel;
  entityContextRef.current = state.entityContext;
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
    if (!isAuthenticated) return; // do not restore history for unauthenticated users
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
  }, [chatConversationId, connection, isAuthenticated]);

  // Mirror WS-derived conversation id into sessionStorage so it survives
  // refresh. The setChatConversationId callback covers explicit FE writes;
  // this effect catches the WS-driven path (`connection.conversationId`
  // populated by the `message` event in useChatSocket).
  // useLayoutEffect (not useEffect): ensures sessionStorage is updated
  // synchronously before paint. Prevents a race where router.push fires
  // before the async useEffect batch commits, leaving sessionStorage with
  // the old conversationId and causing history to vanish on remount.
  useLayoutEffect(() => {
    if (chatConversationId) {
      persistConversationId(chatConversationId);
    }
  }, [chatConversationId]);

  const addChatMessage = useCallback((msg: LiaChatMessage) => {
    setChatMessages((prev) => dedupeAppend(prev, msg));
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
        setChatMessages((prev) => dedupeAppend(prev, note));
      }
    };
    window.addEventListener("lia:settings-updated", onUpdated);
    return () => window.removeEventListener("lia:settings-updated", onUpdated);
  }, []);

  // C5 (2026-06-18): vacancy context sync — quando recrutador abre preview de
  // uma vaga no painel lateral (pipeline-overview-page), o pipeline despacha
  // "lia:set-vacancy-context" com { vacancyId, vacancyTitle }. Aqui absorvemos
  // como entityContext { type:"job", id, name } para que sendChatMessage
  // inclua automaticamente job_id no metadata de toda mensagem subsequente
  // (via entityContextRef branch B3b 2026-06-09). Ao fechar o preview (null),
  // limpamos o contexto de entidade para nao vazar para outra pagina.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onVacancyContext = (e: Event) => {
      const detail = ((e as CustomEvent).detail || {}) as {
        vacancyId?: string | number | null;
        vacancyTitle?: string | null;
      };
      if (detail.vacancyId) {
        setState((prev) => ({
          ...prev,
          entityContext: {
            type: "job",
            id: detail.vacancyId!,
            name: detail.vacancyTitle ?? undefined,
            meta: { source: "vacancy_preview" },
          },
        }));
      } else {
        // Preview fechado — limpa contexto de entidade para nao vazar.
        setState((prev) =>
          prev.entityContext?.meta?.source === "vacancy_preview"
            ? { ...prev, entityContext: null }
            : prev,
        );
      }
    };
    window.addEventListener("lia:set-vacancy-context", onVacancyContext);
    return () => window.removeEventListener("lia:set-vacancy-context", onVacancyContext);
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
        // Limpa thinking steps e buffer de activity para evitar poluição
        // de reasoning steps da conversa anterior na nova conversa.
        connection.clearActivityState();
        return null;
      }

      // Troca de contexto pura: preserva a conversa ativa intacta.
      return currentConvId;
    },
    // Bug 2026-06-08 fix: depende SO do setter estavel (useState setter),
    // nao do objeto connection (nao-memoizado em useLiaChatConnection ->
    // nova ref a cada render -> tornava switchChatContext instavel ->
    // loop infinito no useEffect de currentPage em dashboard-app.tsx ->
    // 'Maximum update depth exceeded').
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setter de useState e estavel; depender do objeto connection reintroduz o loop
    [connection.setConversationId],
  );

  const sendChatMessage = useCallback(
    async (
      content: string,
      domain?: string,
      scope?: string,
      metadata?: Record<string, unknown>,
    ) => {
      addChatMessage({
        id: createMessageId("user"),
        sender: "user",
        content,
        timestamp: formatMessageTime(),
      });

      // PR-A FE — enrich metadata with Rail A hint when a dynamic panel is
      // active so backend Tier -1 routes deterministically. See
      // PANEL_TYPE_TO_DOMAIN_HINT above for the mapping rationale. Caller
      // can override by passing explicit metadata.domain_hint.
      const activePanelType = dynamicPanelRef.current?.panelType;
      const panelHint = activePanelType
        ? PANEL_TYPE_TO_DOMAIN_HINT[activePanelType]
        : undefined;
      const ctxType = chatContextTypeRef.current;
      const ctxHint = CONTEXT_TYPE_TO_DOMAIN_HINT[ctxType];
      // Resolution chain: dynamicPanel → chatContextType → undefined (default routing).
      // panelType wins because it's a more specific signal (active wizard panel etc).
      //
      // EXCEÇÃO (fix 2026-06-01): `settings_config` é um contexto explícito de
      // tela cheia (o usuário abriu o chat de Configurações). Ele DEVE vencer um
      // painel de wizard que "ficou preso" de um fluxo de criação de vaga
      // anterior — senão os saves de empresa via chat eram sequestrados pro
      // agente `wizard` (que não tem save_company_field) e nunca persistiam.
      // Nos demais contextos o painel mantém prioridade (roteamento mid-wizard,
      // guard 2026-04-29 wizard-domain-hint-leak).
      const hintDomain =
        ctxType === "settings_config"
          ? ctxHint || panelHint || undefined
          : panelHint || ctxHint || undefined;

      // B3b (2026-06-09): inject entityContext ids into Rail A metadata so the
      // backend _collect_entity_ids_for_modal can open entity modals without
      // running the slow EntityResolverService on message text.
      const _entityCtx = entityContextRef.current;
      const _entityIds =
        _entityCtx?.id && _entityCtx.type
          ? {
              [_entityCtx.type === "job" ? "job_id" : "candidate_id"]: String(
                _entityCtx.id,
              ),
              entity_id: String(_entityCtx.id),
              entity_type: _entityCtx.type,
              ...((_entityCtx.name) ? { entity_label: _entityCtx.name } : {}),
            }
          : undefined;

      const baseMetadata = hintDomain && !metadata?.domain_hint
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

      const enrichedMetadata = _entityIds
        ? { ...(baseMetadata ?? {}), entity_ids: _entityIds }
        : baseMetadata;

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
        id: createMessageId("user"),
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
        id: createMessageId("lia"),
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

  // Transição NÃO-destrutiva para TELA CHEIA (página "Conversar").
  //
  // Bug 2026-06-05: o wizard escalava pra fullscreen via `handleModeChange`
  // (UnifiedChat), que chamava `close()`. Mas `close()` é o DISMISS canônico —
  // zera `entityContext` + `dynamicPanel`. Zerar `dynamicPanel` derruba o gate
  // `hasDynamicPanel` → o painel do wizard fechava a cada interação.
  //
  // O overlay flutuante já some sozinho em `mode === "fullscreen"` (UnifiedChat
  // retorna null pro overlay nesse modo), então `close()` ali era redundante
  // pra esconder E destrutivo pro painel. `enterFullscreen` apenas baixa
  // `isOpen` (esconde o overlay) PRESERVANDO `dynamicPanel` + `entityContext`,
  // que a tela cheia lê do MESMO float context compartilhado.
  //
  // Invariante: `close()` (dismiss do usuário) CONTINUA zerando tudo — só este
  // caminho de transição muda. Skill canônica: harness-engineering [guide].
  const enterFullscreen = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false }));
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
    // Defesa em profundidade (Bug 2026-06-08): bail quando inalterado
    // para o React abortar o re-render — evita storm de setState se um
    // consumidor chamar este setter dentro de um effect.
    setState((prev) =>
      prev.contextPage === page ? prev : { ...prev, contextPage: page },
    );
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

  // tool close_panel: LIA fecha o painel lateral via chat.
  useEffect(() => {
    function handleClosePanel() { closeDynamicPanel(); }
    window.addEventListener("lia:close_panel", handleClosePanel);
    return () => window.removeEventListener("lia:close_panel", handleClosePanel);
  }, [closeDynamicPanel]);

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
      const data =
        ((detail.data as Record<string, unknown> | undefined) ?? {}) as Record<string, unknown>;
      openDynamicPanel({
        panelType: "job_creation",
        data,
        stage,
        requires_approval: Boolean(detail.requires_approval),
      });
      // Manus F1 — done/handoff fecha + limpa estado stale (só se usuário não expandiu
      // ativamente esta sessão). handoff = stage terminal real (wizard emite quando
      // job_id existe + navega pro jobs). done = alternativa legada (raramente emitida).
      // Ambos disparam o cleanup. tool open/close_panel aplica preferencia via data.panel_pref.
      if (stage === "done" || stage === "handoff") {
        if (!userExpandedRef.current) {
          setWizardPanelModeState("docked");
        }
        closeDynamicPanel(); // limpa estado stale
        userExpandedRef.current = false; // reset para próximo wizard
        setWizardConsentDeclined(false); // F3: reset consent para próximo wizard
      } else {
        const pref = data.panel_pref;
        if (pref === "expanded" || pref === "docked") {
          // Fix 2026-06-11: ignorar panel_pref=expanded durante stage=intake
          // se o recrutador ainda não expandiu manualmente. A LLM não pode
          // forçar expanded no 1º turno — o painel inicia e permanece docked
          // até ação explícita do recrutador ou artefato gerado (JD/WSI).
          const isIntakeStage = stage === "intake";
          if (pref === "expanded" && isIntakeStage && !userExpandedRef.current) {
            // ignore: LLM não pode forçar expanded durante intake
          } else {
            if (pref === "expanded") userExpandedRef.current = true;
            setWizardPanelModeState(pref);
          }
        }
      }
    };
    window.addEventListener("lia:wizard-stage-payload", handler);
    return () =>
      window.removeEventListener("lia:wizard-stage-payload", handler);
  }, [openDynamicPanel, closeDynamicPanel]);

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
    const convParam = conversationId
      ? `&conversation_id=${encodeURIComponent(conversationId)}`
      : "";
    if (document.querySelector("[data-dashboard-shell]")) {
      // Navega PRIMEIRO, fecha o float com delay (Bug 2026-06-08).
      // Evita race onde float fechava antes da pagina de chat montar.
      window.dispatchEvent(
        new CustomEvent("lia:navigate-chat-page", {
          detail: { conversationId },
        }),
      );
      setTimeout(() => {
        setState((prev) => ({
          ...prev,
          isOpen: false,
          isExpanded: false,
          splitView: INITIAL_SPLIT_VIEW,
        }));
      }, 80);
    } else {
      setState((prev) => ({
        ...prev,
        isOpen: false,
        isExpanded: false,
        splitView: INITIAL_SPLIT_VIEW,
      }));
      window.location.href = `/?page=chat-lia${convParam}`;
    }
  }, []);

  const value = useMemo<LiaFloatContextType>(
    () => ({
      ...state,
      open,
      close,
      enterFullscreen,
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
      wizardPanelMode,
      setWizardPanelMode,
      sharedMessages,
      addSharedMessage,
      setSharedMessages,
      wizardConsentDeclined,
      setWizardConsentDeclined,
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
      enterFullscreen,
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
      wizardPanelMode,
      setWizardPanelMode,
      sharedMessages,
      addSharedMessage,
      sharedConversationId,
      wizardConsentDeclined,
      setWizardConsentDeclined,
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
