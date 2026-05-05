"use client";

import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard";
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal";
import type { ChatSuggestionMetadata } from "@/components/ui/chat-workflow-reels";
import { useLiaChatContext, useLiaFloat } from "@/contexts/lia-float-context";
import { useNavigationIntent } from "@/hooks/shared/use-navigation-intent";
import { cn } from "@/lib/utils";
import {
  formatGlossaryEntryMarkdown,
  lookupGlossaryTerm,
} from "@/services/lia-api/glossary-api";
import { useAuthStore } from "@/stores/auth-store";
import { Maximize2, X } from "lucide-react";
import { useTranslations } from "next-intl";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { UnifiedChatEmptyState } from "./UnifiedChatEmptyState";
import { UnifiedChatHeader } from "./UnifiedChatHeader";
import { UnifiedChatInput } from "./UnifiedChatInput";
import { UnifiedMessageList } from "./UnifiedMessageList";
import {
  BUSCAR_BARE_REGEX,
  buildAjudaChatMessages,
  buildBuscarChatMessages,
  buildBuscarHelpMarkdown,
} from "./slash-commands";
import type { ChatMode } from "./unified-chat-types";
import { useJdUploadProgress } from "./useJdUploadProgress";
import {
  DynamicContextPanel,
  SPLIT_STAGES,
} from "./wizard/DynamicContextPanel";
import { ProgressiveDisclosure } from "./wizard/ProgressiveDisclosure";
import { TaskContextBar } from "./wizard/TaskContextBar";
import { WizardProgressBar } from "./wizard/WizardProgressBar";
import { useWizardChatCards } from "./wizard/useWizardChatCards";
import { useWizardFlow } from "./wizard/useWizardFlow";
import { useWizardIntegration } from "./wizard/useWizardIntegration";
import { formatWizardSavedLabel } from "./wizard/wizard-saved-label";
import { STAGE_PILL_LABELS, type WizardStage } from "./wizard/wizard-types";

const DEFINIR_REGEX = /^\/(?:definir|glossario|glossário)(?:\s+(.+))?$/i;

const MODE_STORAGE_KEY = "lia-chat-mode";

// `STAGE_PILL_LABELS` is the single source of truth for the long
// "Criando vaga · X" strings shown on the chat header and the workflow
// rail. Importing instead of duplicating keeps both surfaces in sync
// when a stage is renamed or added in the backend graph.
const WIZARD_STAGE_LABELS = STAGE_PILL_LABELS as Record<string, string>;

const WIDTH_STORAGE_KEY = "lia-chat-width";
const DEFAULT_WIDTH = 380;
const MIN_WIDTH = 300;
const MAX_WIDTH = 600;

function getStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar";
  const stored = localStorage.getItem(MODE_STORAGE_KEY);
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen")
    return stored;
  return "sidebar";
}

function getStoredWidth(): number {
  if (typeof window === "undefined") return DEFAULT_WIDTH;
  const stored = localStorage.getItem(WIDTH_STORAGE_KEY);
  if (stored) {
    const n = Number.parseInt(stored, 10);
    if (!isNaN(n) && n >= MIN_WIDTH && n <= MAX_WIDTH) return n;
  }
  return DEFAULT_WIDTH;
}

interface Props {
  renderMode?: "inline" | "overlay";
  initialMode?: ChatMode;
  className?: string;
}

/**
 * UnifiedChat — Single chat component with 3 visual modes (Notion AI-inspired).
 *
 * Includes:
 * - HITL confirmation cards (all modes)
 * - DynamicContextPanel split view (sidebar expands, fullscreen adds panel)
 * - Auto-scroll, streaming, thinking indicators
 */
export function UnifiedChat({
  renderMode = "overlay",
  initialMode,
  className,
}: Props) {
  const [mode, setMode] = useState<ChatMode>(initialMode ?? getStoredMode());
  const [inputText, setInputText] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [showSwitchTask, setShowSwitchTask] = useState(false);
  const [showFullscreenHint, setShowFullscreenHint] = useState(false);
  const fullscreenHintShown = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sidebarWidthPx, setSidebarWidthPx] = useState(getStoredWidth);
  const [isResizing, setIsResizing] = useState(false);
  const widthRef = useRef(sidebarWidthPx);

  useEffect(() => {
    if (!isResizing) return;
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.min(
        MAX_WIDTH,
        Math.max(MIN_WIDTH, window.innerWidth - e.clientX),
      );
      widthRef.current = newWidth;
      setSidebarWidthPx(newWidth);
    };
    const handleMouseUp = () => {
      setIsResizing(false);
      localStorage.setItem(WIDTH_STORAGE_KEY, String(widthRef.current));
    };
    document.body.style.cursor = "ew-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  const authUser = useAuthStore((s) => s.user);
  const tc = useTranslations("common");
  const userName = authUser?.name || authUser?.email || tc("defaultUserName");

  const {
    isOpen,
    open,
    close,
    contextPage,
    dynamicPanel,
    openDynamicPanel,
    closeDynamicPanel,
  } = useLiaFloat();

  const {
    chatMessages,
    setChatMessages,
    chatConversationId,
    setChatConversationId,
    switchChatContext,
    sendChatMessage,
    sendApproval,
    loadChatHistory,
    chatIsConnected,
    chatTransportMode,
    chatIsReconnecting,
    chatIsStreaming,
    chatStreamingContent,
    chatIsCreating,
    chatIsThinking,
    chatThinkingSteps,
    chatHitlPending,
    chatBackgroundTasks,
    chatSessionId,
    seedBackgroundTask,
    clearBackgroundTask,
  } = useLiaChatContext();

  // Task #865 — wizard JD upload step subscribes to the new async backend.
  // The hook owns the entire JD lifecycle (POST → seed queued → terminal
  // event) so `useWizardIntegration` no longer needs to fire the
  // "Criar vaga…" message itself.
  useJdUploadProgress({
    chatSessionId,
    chatBackgroundTasks,
    seedBackgroundTask,
    clearBackgroundTask,
    appendChatMessage: (msg) => setChatMessages((prev) => [...prev, msg]),
  });

  const { detect: detectNavIntent } = useNavigationIntent();

  // Wire wizard integration (file→wizard, question events, slash commands).
  // `onLocalCommand` lets `useWizardIntegration` resolve `/ajuda` (and any
  // future client-only command) without UnifiedChat re-implementing the
  // SLASH_COMMANDS filtering / help-text formatting itself.
  // Onda 33 — also consume `missingFields` so the banner below can surface
  // pending intake fields driven by the WS `wizard_step_response` payload.
  const { handleSlashCommand, missingFields } = useWizardIntegration({
    isWizardActive: !!dynamicPanel,
    currentStage: dynamicPanel?.stage ?? null,
    sendMessage: sendChatMessage,
    onLocalCommand: (commandId, payload) => {
      if (commandId !== "ajuda") return;
      const { userMsg, helpMsg } = buildAjudaChatMessages(
        payload.rawInput,
        payload.responseMarkdown,
      );
      setChatMessages((prev) => [...prev, userMsg, helpMsg]);
    },
  });

  // Canonical wizard state on the chat surface — listens to the same
  // `lia:wizard-stage-payload` window event that powers `WizardContext` for
  // the right-side panel. Reusing the hook avoids a parallel state channel.
  // `userId` namespaces the wizard's localStorage key so recruiter A's
  // in-flight job doesn't bleed to recruiter B on a shared browser (LGPD).
  const wizard = useWizardFlow({ userId: authUser?.id });
  const {
    currentStage: wizardStage,
    stageData: wizardStageData,
    completeness: wizardCompleteness,
    stageHistory: wizardHistory,
  } = wizard;
  const wizardActive =
    wizardStage !== null && wizardStage !== "done" && wizardStage !== "handoff";

  // Auto-save hint — every wizard_stage payload from the backend means
  // the in-flight job draft was just persisted server-side, so we treat
  // the arrival of a new stage as the wizard's "saved at" timestamp.
  // The header re-renders the relative label every minute. We skip the
  // first render (rehydrate from localStorage) to avoid a misleading
  // "Salvando…" flash when nothing was actually persisted just now.
  const [wizardSavedAt, setWizardSavedAt] = useState<Date | null>(null);
  const [, setSavedTick] = useState(0);
  const wizardSavedHydratedRef = useRef(false);
  useEffect(() => {
    if (!wizardStage) return;
    if (!wizardSavedHydratedRef.current) {
      wizardSavedHydratedRef.current = true;
      return;
    }
    setWizardSavedAt(new Date());
  }, [wizardStage, wizardCompleteness]);
  useEffect(() => {
    if (!wizardActive) return;
    const id = setInterval(() => setSavedTick((n) => n + 1), 30_000);
    return () => clearInterval(id);
  }, [wizardActive]);
  const wizardSavedLabel = formatWizardSavedLabel(
    wizardSavedAt,
    new Date(),
    wizardActive,
  );

  // Track last-seen dynamic panel so we can re-open it after the user
  // dismisses the right-side panel mid-wizard (Task #836 — botão "Ver vaga").
  const lastDynamicPanelRef = useRef<typeof dynamicPanel>(null);
  useEffect(() => {
    if (dynamicPanel) lastDynamicPanelRef.current = dynamicPanel;
  }, [dynamicPanel]);
  const reopenLastPanel = useCallback(() => {
    if (lastDynamicPanelRef.current) {
      openDynamicPanel(lastDynamicPanelRef.current);
    }
  }, [openDynamicPanel]);
  // Plan card + published-job card are owned by `useWizardChatCards`
  // (Task A2) — extracted from this file so the same behaviour can be
  // unit-tested in isolation. Comments on when each card appears/updates
  // live in the hook itself.
  useWizardChatCards({
    wizardStage,
    wizardStageData,
    setChatMessages,
    // E.8 — pipeline template tile click forwards as a chat reply so
    // LIA's stage_basic_info handler resolves the choice with the
    // same NLU path as a typed answer ("Vou usar o template ...").
    onSelectTemplate: (option) => {
      sendChatMessage(`Vou usar o template ${option.name}`);
    },
  });

  // Persist mode preference
  useEffect(() => {
    localStorage.setItem(MODE_STORAGE_KEY, mode);
  }, [mode]);

  const handleSend = useCallback(() => {
    const text = inputText.trim();
    if (!text) return;

    // `/definir <termo>` is resolved locally against the canonical glossary
    // endpoint so recruiters get the official WSI/BARS/Bloom definition without
    // round-tripping the LIA agent (Task #745).
    const definirMatch = text.match(DEFINIR_REGEX);
    if (definirMatch) {
      const term = (definirMatch[1] ?? "").trim();
      const now = new Date().toISOString();
      const userMsg = {
        id: `user-${Date.now()}`,
        sender: "user" as const,
        content: text,
        timestamp: now,
      };
      // Bare `/definir` (no term) — answer locally with usage guidance instead
      // of hitting the backend agent.
      if (!term) {
        const helpMsg = {
          id: `lia-${Date.now()}-glossary-help`,
          sender: "lia" as const,
          content:
            "Informe o termo apos o comando. Exemplos: `/definir WSI`, `/definir Bloom`, `/definir BARS`.",
          timestamp: now,
        };
        setChatMessages((prev) => [...prev, userMsg, helpMsg]);
        setInputText("");
        setAttachedFile(null);
        return;
      }
      const pendingId = `lia-${Date.now()}-glossary`;
      const pendingMsg = {
        id: pendingId,
        sender: "lia" as const,
        content: `Buscando a definicao oficial de **${term}**...`,
        timestamp: now,
      };
      setChatMessages((prev) => [...prev, userMsg, pendingMsg]);
      setInputText("");
      setAttachedFile(null);
      void lookupGlossaryTerm(term).then((result) => {
        const replyContent = result.ok
          ? formatGlossaryEntryMarkdown(result.entry)
          : `${result.message}\n\n_Tente outro termo, por exemplo: \`/definir WSI\`._`;
        setChatMessages((prev) =>
          prev.map((m) =>
            m.id === pendingId ? { ...m, content: replyContent } : m,
          ),
        );
      });
      return;
    }

    // Bare `/buscar` (no args) renders a local clarification card with
    // canonical search recipes — same UX pattern as `/ajuda` /
    // `/definir`. Avoids shipping the generic "Buscar candidatos"
    // payload to the backend agent and gives the user a copy/pasteable
    // menu of patterns instead.
    if (BUSCAR_BARE_REGEX.test(text)) {
      const { userMsg, helpMsg } = buildBuscarChatMessages(
        text,
        buildBuscarHelpMarkdown(),
      );
      setChatMessages((prev) => [...prev, userMsg, helpMsg]);
      setInputText("");
      setAttachedFile(null);
      return;
    }

    // Intercept slash commands before sending to backend. `/ajuda` and the
    // other client-only commands resolve inside `useWizardIntegration`
    // (single source of truth) — see `onLocalCommand` wiring above.
    if (text.startsWith("/") && handleSlashCommand(text)) {
      setInputText("");
      setAttachedFile(null);
      return;
    }
    sendChatMessage(text);
    setInputText("");
    setAttachedFile(null);

    detectNavIntent(text).then((result) => {
      // BUG-18 fix: 0.85 era muito alto — frases naturais como "me leva pra vagas"
      // atingiam no máximo ~0.70 mesmo após fix do dampening no backend.
      // 0.65 captura imperativos de navegação sem falso-positivar perguntas genéricas.
      if (result?.page && result.confidence >= 0.65) {
        window.dispatchEvent(
          new CustomEvent("lia:navigation-hint", {
            detail: { page: result.page, hint: result.hint },
          }),
        );
      }
    });
  }, [inputText, sendChatMessage, detectNavIntent, handleSlashCommand]);

  const handleSuggestionClick = useCallback(
    (prompt: string, metadata?: ChatSuggestionMetadata) => {
      setInputText(prompt);
      // setTimeout 100ms é workaround para renderizar setInputText antes do
      // send (evita race com input que ainda não recebeu o valor visualmente).
      setTimeout(() => {
        // PR-A (FE-H03): quando vem do Rail A, passa `domain_hint` como
        // `domain` e a metadata completa como 4º arg. O orchestrator usa
        // `context.metadata.intent_hint` como guide para routing determinístico.
        // Chamadas sem metadata (slash, mention, manual) seguem inalteradas.
        const domain = metadata?.domain_hint;
        sendChatMessage(
          prompt,
          domain,
          undefined,
          metadata as Record<string, unknown> | undefined,
        );
        setInputText("");
      }, 100);
    },
    [sendChatMessage],
  );

  const handleNewChat = useCallback(() => {
    switchChatContext("general", { conversationId: null });
    setChatMessages([]);
    setInputText("");
    setAttachedFile(null);
  }, [switchChatContext, setChatMessages]);

  // Switch to a different conversation
  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      setChatConversationId(sessionId);
      await loadChatHistory(sessionId);
      setShowSwitchTask(false);
    },
    [setChatConversationId, loadChatHistory],
  );

  const currentModeRef = useRef(mode);
  currentModeRef.current = mode;

  // Suggest fullscreen once when wizard starts in non-fullscreen mode
  useEffect(() => {
    if (
      dynamicPanel?.stage === "intake" &&
      mode !== "fullscreen" &&
      renderMode !== "inline" &&
      !fullscreenHintShown.current
    ) {
      fullscreenHintShown.current = true;
      setShowFullscreenHint(true);
      const timer = setTimeout(() => setShowFullscreenHint(false), 7000);
      return () => clearTimeout(timer);
    }
  }, [dynamicPanel?.stage, mode, renderMode]);

  // Workflow Rail integration — emit lifecycle events as wizard stage changes
  const prevStageRef = useRef<string | null>(null);
  const wizardWorkflowIdRef = useRef<string | null>(null);

  useEffect(() => {
    const stage = dynamicPanel?.stage ?? null;
    const prevStage = prevStageRef.current;
    if (stage === prevStage) return;
    prevStageRef.current = stage;

    if (stage === "intake" && !prevStage) {
      wizardWorkflowIdRef.current = `wizard-${Date.now()}`;
      window.dispatchEvent(
        new CustomEvent("workflow:started", {
          detail: {
            id: wizardWorkflowIdRef.current,
            type: "campaign",
            label: "Criando vaga",
            stage: "intake",
          },
        }),
      );
    } else if (stage && wizardWorkflowIdRef.current) {
      if (stage === "done") {
        window.dispatchEvent(
          new CustomEvent("workflow:completed", {
            detail: { id: wizardWorkflowIdRef.current, outcome: "success" },
          }),
        );
        wizardWorkflowIdRef.current = null;
      } else {
        window.dispatchEvent(
          new CustomEvent("workflow:updated", {
            detail: {
              id: wizardWorkflowIdRef.current,
              stage,
              label: WIZARD_STAGE_LABELS[stage] ?? stage,
            },
          }),
        );
      }
    } else if (!stage && prevStage && wizardWorkflowIdRef.current) {
      window.dispatchEvent(
        new CustomEvent("workflow:failed", {
          detail: {
            id: wizardWorkflowIdRef.current,
            error: "Fluxo interrompido",
          },
        }),
      );
      wizardWorkflowIdRef.current = null;
    }
  }, [dynamicPanel?.stage]);

  useEffect(() => {
    if (!wizardWorkflowIdRef.current) return;
    window.dispatchEvent(
      new CustomEvent("workflow:thinking", {
        detail: { id: wizardWorkflowIdRef.current, isThinking: chatIsThinking },
      }),
    );
  }, [chatIsThinking]);

  const handleModeChange = useCallback(
    (newMode: ChatMode) => {
      const prevMode = currentModeRef.current;
      if (newMode === "minimized") {
        close();
        window.dispatchEvent(
          new CustomEvent("lia:chat-mode-changed", {
            detail: { mode: "minimized", prevMode },
          }),
        );
        return;
      }
      setMode(newMode);
      localStorage.setItem(MODE_STORAGE_KEY, newMode);
      window.dispatchEvent(
        new CustomEvent("lia:chat-mode-changed", {
          detail: { mode: newMode, prevMode },
        }),
      );
      if (newMode === "fullscreen") {
        close();
        window.dispatchEvent(
          new CustomEvent("lia:navigate-chat-page", { detail: {} }),
        );
      } else if (newMode === "floating") {
        open();
      } else if (newMode === "sidebar") {
        open();
        if (prevMode === "fullscreen") {
          window.dispatchEvent(
            new CustomEvent("lia:leave-fullscreen-chat", {
              detail: { targetMode: newMode },
            }),
          );
        }
      }
    },
    [close, open],
  );

  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileAttach = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && file.size <= 10 * 1024 * 1024) {
        setAttachedFile(file);
      }
      if (e.target) e.target.value = "";
    },
    [],
  );

  const conversationTitle =
    chatMessages.find((m) => m.sender === "user")?.content?.slice(0, 40) ||
    null;
  const hasMessages = chatMessages.length > 0;
  const hasDynamicPanel =
    !!dynamicPanel && SPLIT_STAGES.includes(dynamicPanel.stage as WizardStage);
  const activeTaskLabel = dynamicPanel?.stage
    ? (WIZARD_STAGE_LABELS[dynamicPanel.stage] ?? dynamicPanel.stage)
    : null;

  if (renderMode === "overlay" && !isOpen && mode !== "fullscreen") return null;

  const isInline = renderMode === "inline";
  const effectiveMode: ChatMode = isInline ? "sidebar" : mode;

  const dynamicPanelWidth = hasDynamicPanel ? 340 : 0;
  const inlineWidth = isInline ? sidebarWidthPx + dynamicPanelWidth : undefined;

  return (
    <div
      className={cn(
        "flex bg-lia-bg-primary relative overflow-hidden",
        isInline
          ? "flex-shrink-0 border border-lia-border-subtle rounded-md h-full"
          : mode === "fullscreen"
            ? "fixed inset-0 z-50"
            : mode === "sidebar"
              ? "fixed top-2 right-2 bottom-2 z-40 border border-lia-border-subtle rounded-md"
              : "fixed bottom-4 right-4 w-[360px] h-[520px] z-30 rounded-md border border-lia-border-subtle",
        className,
      )}
      style={
        isInline
          ? { width: `${inlineWidth}px` }
          : !isInline && mode === "sidebar"
            ? { width: `${sidebarWidthPx + dynamicPanelWidth}px` }
            : undefined
      }
      data-chat-mode={effectiveMode}
      data-render-mode={renderMode}
    >
      {(isInline || (!isInline && mode === "sidebar")) && (
        <div
          className="absolute left-0 top-0 w-1.5 h-full cursor-ew-resize z-10 group hover:bg-wedo-cyan/20 active:bg-wedo-cyan/30 transition-colors"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
        >
          <div className="absolute left-0.5 top-1/2 -translate-y-1/2 w-0.5 h-8 rounded-full bg-lia-border-subtle group-hover:bg-wedo-cyan transition-colors" />
        </div>
      )}
      {/* Chat column */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <UnifiedChatHeader
          mode={effectiveMode}
          onModeChange={handleModeChange}
          onClose={close}
          onNewChat={handleNewChat}
          onSwitchTask={() => setShowSwitchTask(true)}
          conversationTitle={conversationTitle}
          isConnected={chatIsConnected}
          transportMode={chatTransportMode}
          isReconnecting={chatIsReconnecting}
          activeTaskLabel={activeTaskLabel}
          autoSaveLabel={wizardSavedLabel}
          showOpenJobButton={
            wizardActive &&
            !hasDynamicPanel &&
            !!lastDynamicPanelRef.current &&
            SPLIT_STAGES.includes(
              lastDynamicPanelRef.current.stage as WizardStage,
            )
          }
          onOpenJob={reopenLastPanel}
        />

        {/* Wizard progress bar — sticky at the top of the feed while the
            "Criar nova vaga" wizard is active. Mounts on the first
            `wizard_stage` event and unmounts at `done`/`handoff`. */}
        {wizardActive && (
          <div
            className="border-b border-lia-border-subtle"
            role="status"
            aria-live="polite"
            aria-label="Progresso do wizard de criação de vaga"
            data-testid="wizard-progress-bar"
          >
            <WizardProgressBar
              currentStage={wizardStage}
              completeness={wizardCompleteness}
              stageHistory={wizardHistory}
              compact={effectiveMode === "floating"}
            />
          </div>
        )}

        {/* Onda 33 — missingFields banner. Reuses the warning pattern from
            ReviewPanel (`bg-status-warning/5 border border-status-warning/20`)
            instead of introducing a new component. Sits between the progress
            bar and the message list so it stays visible while the recruiter
            is reading the latest LIA reply. */}
        {missingFields.length > 0 && (
          <div className="px-4 pt-2">
            <div
              role="status"
              aria-live="polite"
              data-testid="wizard-missing-fields-banner"
              className="rounded-md border border-status-warning/20 bg-status-warning/5 px-3 py-2 text-sm text-status-warning"
            >
              <span className="font-medium">⚠️ Campos obrigatórios em aberto:</span>{" "}
              {missingFields.join(", ")}
            </div>
          </div>
        )}

        {/* Content area */}
        {hasMessages ? (
          <UnifiedMessageList
            mode={effectiveMode}
            messages={chatMessages}
            isStreaming={chatIsStreaming}
            streamingContent={chatStreamingContent}
            isThinking={chatIsThinking}
            thinkingSteps={chatThinkingSteps}
            userName={userName}
            onChipClick={(value) => sendChatMessage(value)}
          />
        ) : (
          <UnifiedChatEmptyState
            mode={effectiveMode}
            onSuggestionClick={handleSuggestionClick}
          />
        )}

        {/* HITL Confirmation — inline above input (all modes) */}
        {chatHitlPending && (
          <div className="px-4 pb-2">
            <HITLConfirmCard
              action={chatHitlPending.action}
              description={chatHitlPending.description}
              onConfirm={() => sendApproval(true)}
              onCancel={() => sendApproval(false)}
            />
          </div>
        )}

        {/* Progressive disclosure tips (wizard active) */}
        {hasDynamicPanel && (
          <ProgressiveDisclosure
            currentStage={(dynamicPanel?.stage as WizardStage) ?? null}
            interactionCount={
              chatMessages.filter((m) => m.sender === "user").length
            }
          />
        )}

        {/* Fullscreen suggestion hint (once when wizard starts in non-fullscreen) */}
        {showFullscreenHint && (
          <div className="px-4 pb-1">
            <div className="flex items-center justify-between px-3 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary">
              <span className="text-xs text-lia-text-secondary">
                Tela cheia melhora a experiência do wizard
              </span>
              <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                <button
                  onClick={() => {
                    handleModeChange("fullscreen");
                    setShowFullscreenHint(false);
                  }}
                  className="flex items-center gap-1 text-xs font-medium text-lia-text-primary px-2 py-0.5 rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                >
                  <Maximize2 className="w-3 h-3" aria-hidden="true" />
                  Tela cheia
                </button>
                <button
                  onClick={() => setShowFullscreenHint(false)}
                  className="p-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                  aria-label="Fechar sugestão"
                >
                  <X className="w-3 h-3" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Input */}
        <UnifiedChatInput
          mode={effectiveMode}
          inputText={inputText}
          setInputText={setInputText}
          onSend={handleSend}
          isStreaming={chatIsStreaming}
          isCreating={chatIsCreating}
          isDisabled={!!chatHitlPending}
          contextPage={contextPage}
          attachedFile={attachedFile}
          setAttachedFile={setAttachedFile}
          fileInputRef={fileInputRef}
          onFileButtonClick={handleFileButtonClick}
          onFileAttach={handleFileAttach}
          onExecuteSlashCommand={handleNewChat}
        />

        {/* E.5: TaskContextBar — shown when wizard is active, below the input */}
        {wizardActive && activeTaskLabel && (
          <div className="px-2 pb-2">
            <TaskContextBar
              currentAction={activeTaskLabel}
              onSwitchTask={(taskId) => {
                void handleSelectSession(taskId)
              }}
            />
          </div>
        )}
      </div>

      {/* Split View: DynamicContextPanel — wider in fullscreen to use available space */}
      {hasDynamicPanel && (
        <div
          className={cn(
            "flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto",
            effectiveMode === "fullscreen" ? "w-[420px]" : "w-[340px]",
          )}
        >
          <DynamicContextPanel
            stage={(dynamicPanel?.stage as WizardStage) ?? null}
            data={dynamicPanel?.data ?? {}}
            requiresApproval={dynamicPanel?.requires_approval ?? false}
            onApprove={() => sendApproval(true)}
            onReject={() => sendApproval(false)}
            onClose={closeDynamicPanel}
            onUpdate={(updates) =>
              sendChatMessage(
                JSON.stringify({ type: "wizard_update", updates }),
              )
            }
          />
        </div>
      )}

      {/* Switch Task Modal (⌘K) */}
      <SwitchTaskModal
        isOpen={showSwitchTask}
        onClose={() => setShowSwitchTask(false)}
        onSelectSession={handleSelectSession}
        currentSessionId={chatConversationId}
      />
    </div>
  );
}
