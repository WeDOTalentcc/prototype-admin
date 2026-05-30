"use client";

import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard";
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { buttonVariants } from "@/components/ui/button";
import type { ChatSuggestionMetadata } from "@/components/ui/chat-workflow-reels";
import { useLiaChatContext, useLiaFloat } from "@/contexts/lia-float-context";
import { useNavigationIntent } from "@/hooks/shared/use-navigation-intent";
import { cn } from "@/lib/utils";
import {
  formatGlossaryEntryMarkdown,
  lookupGlossaryTerm,
} from "@/services/lia-api/glossary-api";
import { useAuthStore } from "@/stores/auth-store";
import { useChatStateStore } from "@/stores/chat-state-store";
import { useRecentItemsStore } from "@/stores/recent-items-store";
import { Maximize2, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { requestRegeneration } from "@/services/lia-api/feedback-api";
import { deleteChatConversation } from "./deleteChatConversation";
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
  fetchWizardSessionState,
  WizardBackendUnavailableError,
  purgeLegacyWizardStorage,
  resetWizardSession,
} from "./wizard/useWizardSessionApi";
import { WIZARD_PIPELINE_TEMPLATE_DISPATCH } from "./wizard/dispatchMessages";
import {
  DynamicContextPanel,
  SPLIT_STAGES,
} from "./wizard/DynamicContextPanel";
import { ProgressiveDisclosure } from "./wizard/ProgressiveDisclosure";
import { WizardProgressBar } from "./wizard/WizardProgressBar";
import { PipelineTemplateSuggestion } from "./wizard/PipelineTemplateSuggestion";
import { WizardPipelineTemplateStagePanel } from "./wizard/WizardPipelineTemplateStagePanel";
import { useWizardChatCards } from "./wizard/useWizardChatCards";
import { useWizardFlow } from "./wizard/useWizardFlow";
import { useWizardIntegration } from "./wizard/useWizardIntegration";
import { formatWizardSavedLabel } from "./wizard/wizard-saved-label";
import { STAGE_PILL_LABELS, type WizardStage } from "./wizard/wizard-types";
import { getPersisted, setPersisted } from "@/lib/lia-persistence";

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

// Onda 4-P2-6 (2026-05-24): getStoredMode/getStoredWidth migrados pra
// liaPersistence helper canonical (TTL "long" = 90 dias). Backwards-compat
// via getPersisted (legacy raw values são auto-removidos no primeiro read).
function getStoredMode(): ChatMode {
  const stored = getPersisted<string>(MODE_STORAGE_KEY, "sidebar");
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen")
    return stored;
  return "sidebar";
}

function getStoredWidth(): number {
  const stored = getPersisted<number | null>(WIDTH_STORAGE_KEY, null);
  if (typeof stored === "number" && stored >= MIN_WIDTH && stored <= MAX_WIDTH) {
    return stored;
  }
  return DEFAULT_WIDTH;
}

// Painel lateral redimensionável (pedido Paulo 2026-05-30). Largura própria,
// persistida com TTL "long" como a do chat.
const PANEL_WIDTH_KEY = "lia-panel-width";
const PANEL_DEFAULT_WIDTH = 340;
const PANEL_MIN_WIDTH = 280;
const PANEL_MAX_WIDTH = 560;

function getStoredPanelWidth(): number {
  const stored = getPersisted<number | null>(PANEL_WIDTH_KEY, null);
  if (typeof stored === "number" && stored >= PANEL_MIN_WIDTH && stored <= PANEL_MAX_WIDTH) {
    return stored;
  }
  return PANEL_DEFAULT_WIDTH;
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

export function wizardUpdateToMessage(updates: Record<string, unknown>): string {
  if ("jd_similar_reuse_id" in updates) return "Reutilizar JD similar: " + String(updates.jd_similar_reuse_id)
  if ("jd_similar_dismissed" in updates) return "Ignorar JD similar, vou digitar manualmente"
  if ("raw_input" in updates) return String(updates.raw_input)
  if ("screening_mode" in updates)
    return updates.screening_mode === "compact" ? "Modo compacto (7 perguntas)" : "Modo completo (12 perguntas)"
  if ("sourcing_mode" in updates) {
    const labels: Record<string, string> = {
      internal: "Talent Pool interno",
      internal_global: "Interno + Global",
      global: "Busca global",
    }
    return labels[String(updates.sourcing_mode)] ?? "Sourcing: " + String(updates.sourcing_mode)
  }
  if ("salary_min" in updates && "salary_max" in updates)
    return "Salario entre R$ " + String(updates.salary_min) + " e R$ " + String(updates.salary_max)
  if ("salary_min" in updates) return "Salario minimo: R$ " + String(updates.salary_min)
  if ("salary_max" in updates) return "Salario maximo: R$ " + String(updates.salary_max)
  if ("platforms" in updates) return "Plataformas: " + (updates.platforms as string[]).join(", ")
  if ("auto_screen" in updates) return "Auto-triagem: " + (updates.auto_screen ? "ativada" : "desativada")
  if ("questions" in updates) return "Atualizar perguntas de elegibilidade"
  // Fase 5b — edições de competência no painel (chips). O texto é só o espelho
  // legível; os dados estruturados viajam em context.right_panel_form e o
  // backend (intake_gate) lê confirmed_* com precedência sobre a sugestão.
  if (
    "confirmed_technical_competencies" in updates ||
    "confirmed_behavioral_competencies" in updates
  ) {
    const tech = ((updates.confirmed_technical_competencies as Array<{ skill?: string }>) ?? [])
      .map((t) => t.skill)
      .filter(Boolean)
    const behav = ((updates.confirmed_behavioral_competencies as Array<{ competencia?: string }>) ?? [])
      .map((b) => b.competencia)
      .filter(Boolean)
    const parts: string[] = []
    if (tech.length) parts.push("Competências técnicas: " + tech.join(", "))
    if (behav.length) parts.push("Competências comportamentais: " + behav.join(", "))
    return parts.length ? "Confirmei as competências. " + parts.join(". ") + "." : "Atualizei as competências."
  }
  return JSON.stringify({ type: "wizard_update", updates })
}

/**
 * Fase 5b — acumula os campos estruturados editados no painel (ficha viva)
 * para viajarem juntos em context.right_panel_form, mesmo quando editados em
 * ações separadas. Shallow-merge: a edição mais recente vence por campo.
 */
export function mergeCollectedData(
  prev: Record<string, unknown>,
  updates: Record<string, unknown>,
): Record<string, unknown> {
  return { ...prev, ...updates }
}

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
  // Fase 5b — acumula os campos estruturados do painel (ficha viva) para enviar
  // como context.right_panel_form no próximo turno (loop real dos chips).
  const collectedDataRef = useRef<Record<string, unknown>>({});

  // Painel lateral redimensionável (delta-based: robusto a posições absolutas).
  const [dynamicPanelWidthPx, setDynamicPanelWidthPx] = useState(getStoredPanelWidth);
  const panelWidthRef = useRef(dynamicPanelWidthPx);
  const startPanelResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = panelWidthRef.current;
    const onMove = (ev: MouseEvent) => {
      // Arrastar para a ESQUERDA (clientX diminui) alarga o painel.
      const next = Math.min(
        PANEL_MAX_WIDTH,
        Math.max(PANEL_MIN_WIDTH, startWidth + (startX - ev.clientX)),
      );
      panelWidthRef.current = next;
      setDynamicPanelWidthPx(next);
    };
    const onUp = () => {
      setPersisted(PANEL_WIDTH_KEY, panelWidthRef.current);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.body.style.cursor = "ew-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }, []);

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
      // Onda 4-P2-6: canonical persistence com TTL "long" (90 dias)
      setPersisted(WIDTH_STORAGE_KEY, widthRef.current);
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

  // Task #1128 — one-shot purge of the abolished
  // `localStorage["lia-wizard-state-*"]` cache for users who installed
  // the app before Nova-conversa-reset shipped. Idempotent so re-mounts
  // are free.
  useEffect(() => {
    purgeLegacyWizardStorage();
  }, []);

  // Task #1128 — hydrate wizard state from the backend checkpointer on
  // every conversation/session change. Source of truth is the LangGraph
  // thread keyed by `(company_id, session_id)`; we never trust local
  // caches anymore. A 404 / inactive snapshot triggers `wizard.reset()`
  // so a fresh conversation never inherits a stale stage row from the
  // previous one. Errors are toast-logged but never silently swallowed.
  const wizardHandleStagePayload = wizard.handleStagePayload;
  const wizardReset = wizard.reset;
  useEffect(() => {
    if (!chatSessionId) return;
    let cancelled = false;
    (async () => {
      try {
        const snap = await fetchWizardSessionState(chatSessionId);
        if (cancelled) return;
        if (!snap || !snap.active || !snap.current_stage) {
          wizardReset();
          return;
        }
        wizardHandleStagePayload({
          type: "wizard_stage",
          stage: snap.current_stage as never,
          data: snap.stage_data ?? {},
          completeness: snap.completeness ?? 0,
          requires_approval: !!snap.requires_approval,
          thread_id: snap.thread_id,
        } as never);
      } catch (err) {
        if (cancelled) return;
        // Task #1177 — separa três ramos:
        //   (b) backend ainda subindo / indisponível após retries → toast
        //       neutro "Conectando ao servidor…", SEM console.error (evita
        //       o overlay vermelho do Next.js no dev e ruído no Sentry).
        //   (c) erro real (500 do endpoint, 404, 4xx auth/tenant) →
        //       comportamento Task #1128: console.error + toast vermelho.
        if (err instanceof WizardBackendUnavailableError) {
          toast("Conectando ao servidor…", {
            description:
              "O backend está demorando para responder. Vamos retomar assim que ele estiver pronto.",
          });
          return;
        }
        // eslint-disable-next-line no-console
        console.error(
          "[UnifiedChat] GET wizard session hydration failed",
          { session_id: chatSessionId },
          err,
        );
        // Task #1128 — feedback explícito ao recrutador: sem hidratação
        // a UI pode mostrar um stepper stale (de uma rota anterior) ou
        // simplesmente nenhum, e ele precisa saber que o servidor não
        // confirmou o estado atual.
        toast.error("Não consegui carregar o estado do wizard", {
          description:
            "Recarregue a página em alguns segundos. Se persistir, abra uma nova conversa.",
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chatSessionId, wizardHandleStagePayload, wizardReset]);
  const {
    currentStage: wizardStage,
    stageData: wizardStageData,
    completeness: wizardCompleteness,
    stageHistory: wizardHistory,
    degradedStages: wizardDegradedStages,
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

  // Persist mode preference (Onda 4-P2-6: canonical TTL 90 dias)
  useEffect(() => {
    setPersisted(MODE_STORAGE_KEY, mode);
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
        // Task #1165 — forward the context-aware `mode` resolved inside
        // `useNavigationIntent`. When the hook decided we are already on
        // `/chat` and the suggestion is "Vagas", it zeros `page` out (so
        // we never reach this branch) and the user stays put. Otherwise
        // `mode === "ask"` and `DashboardApp` will propose the
        // transition via chat instead of pushing the router silently.
        window.dispatchEvent(
          new CustomEvent("lia:navigation-hint", {
            detail: {
              page: result.page,
              hint: result.hint,
              mode: result.mode,
            },
          }),
        );
      }
    });
  }, [inputText, sendChatMessage, detectNavIntent, handleSlashCommand]);

  const handleSuggestionClick = useCallback(
    (prompt: string, metadata?: ChatSuggestionMetadata) => {
      // P1-4 (Fase B 2026-05-23): removido setTimeout 100ms — race-condition
      // workaround era hack visual desnecessário. sendChatMessage usa `prompt`
      // diretamente como argument, não depende do state input ter renderizado.
      // PR-A (FE-H03): quando vem do Rail A, passa `domain_hint` como
      // `domain` e a metadata completa como 4º arg. O orchestrator usa
      // `context.metadata.intent_hint` como guide para routing determinístico.
      // Chamadas sem metadata (slash, mention, manual) seguem inalteradas.
      sendChatMessage(
        prompt,
        metadata?.domain_hint,
        undefined,
        metadata as Record<string, unknown> | undefined,
      );
      setInputText("");
    },
    [sendChatMessage],
  );

  // P1-7 (Fase B 2026-05-23): regenerate button wiring.
  // UnifiedMessageList chama `onRegenerate(messageId)` quando recruiter clica
  // no botao "Gerar novamente" numa mensagem LIA. Pipeline:
  //   1. POST /lia/feedback/regenerate { session_id, message_id }
  //      → backend valida ownership e devolve { user_message, regenerate_of }
  //   2. Re-dispara o mesmo user_message via sendChatMessage com metadata
  //      `regenerateOf` pra analytics distinguir turno regenerado de organico.
  // Error path: toast vermelho. Sem retry silencioso (anti-pattern REGRA 4).
  const handleRegenerate = useCallback(
    async (messageId: string) => {
      if (!chatSessionId) {
        toast.error("Nao foi possivel regenerar — sessao indisponivel");
        return;
      }
      try {
        const result = await requestRegeneration(chatSessionId, messageId);
        sendChatMessage(
          result.user_message,
          undefined,
          undefined,
          { regenerateOf: result.regenerate_of } as Record<string, unknown>,
        );
      } catch (err) {
        const detail = err instanceof Error ? err.message : "erro desconhecido";
        toast.error("Nao foi possivel gerar novamente", { description: detail });
      }
    },
    [chatSessionId, sendChatMessage],
  );

  // Task #1128 — shared low-level reset: DELETE the canonical wizard
  // checkpointer for the current session. Used by BOTH "Nova conversa"
  // (which then also switches conversation) and "Cancelar wizard"
  // (which keeps the current conversation, just kills the wizard).
  // Fail-loud — recruiter must know the reset did not happen.
  const resetCurrentWizardSession = useCallback(async (): Promise<boolean> => {
    const previousSessionId = chatSessionId;
    if (!previousSessionId) {
      wizard.reset();
      return true;
    }
    try {
      await resetWizardSession(previousSessionId);
      wizard.reset();
      return true;
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(
        "[UnifiedChat] DELETE wizard session failed",
        { session_id: previousSessionId, conversation_id: chatConversationId },
        err,
      );
      toast.error("Não consegui cancelar o wizard atual", {
        description:
          "O wizard ainda está ativo no servidor. Tente novamente em alguns segundos. Se persistir, recarregue a página.",
      });
      // CRITICAL (Task #1128 code review): NÃO chamamos wizard.reset() aqui.
      // O backend é a fonte da verdade — esconder o stepper localmente
      // enquanto o checkpoint segue aberto criaria a ilusão de cancelamento
      // bem-sucedido, e o próximo `ws_stage_payload` re-abriria o stepper
      // do nada, reproduzindo o bug original do screenshot. Fail-loud:
      // o stepper permanece visível, o recrutador vê o toast e re-tenta.
      return false;
    }
  }, [chatSessionId, chatConversationId, wizard]);

  // Task #1133 — diálogo canônico (DS LIA v4.2.2 AlertDialog) que substitui o
  // `window.confirm` jurássico usado entre #1128 e #1133. A confirmação SÓ
  // aparece quando há rascunho em risco (`wizard.active === true`); se o
  // wizard estiver inativo o comportamento original — cancelar/abrir nova
  // conversa direto, sem prompt — é mantido. Promise armazenada em ref
  // evita re-renders/race entre múltiplos cliques.
  const [wizardConfirm, setWizardConfirm] = useState<{
    open: boolean;
    mode: "cancel" | "new-chat";
  }>({ open: false, mode: "cancel" });
  const wizardConfirmResolverRef = useRef<((ok: boolean) => void) | null>(null);

  const requireWizardCancelConfirm = useCallback(
    (mode: "cancel" | "new-chat"): Promise<boolean> => {
      if (!wizard.active) return Promise.resolve(true);
      return new Promise<boolean>((resolve) => {
        wizardConfirmResolverRef.current = resolve;
        setWizardConfirm({ open: true, mode });
      });
    },
    [wizard.active],
  );

  const closeWizardConfirm = useCallback((decision: boolean) => {
    const resolver = wizardConfirmResolverRef.current;
    wizardConfirmResolverRef.current = null;
    setWizardConfirm((prev) => ({ ...prev, open: false }));
    resolver?.(decision);
  }, []);

  // Task #1128 — "Nova conversa": clears wizard AND switches to a fresh
  // conversation. Triggered by the sidebar/slash command "/nova-conversa".
  // Task #1133 — quando há wizard ativo, exige confirmação antes de
  // descartar o rascunho (mesmo modal canônico do "Cancelar wizard").
  const handleNewChat = useCallback(async () => {
    const proceed = await requireWizardCancelConfirm("new-chat");
    if (!proceed) return;
    const ok = await resetCurrentWizardSession();
    if (!ok) return;
    switchChatContext("general", { conversationId: null, resetConversation: true });
    setChatMessages([]);
    setInputText("");
    setAttachedFile(null);
  }, [
    requireWizardCancelConfirm,
    resetCurrentWizardSession,
    switchChatContext,
    setChatMessages,
  ]);

  // Task #1128 — "Cancelar wizard": kills the wizard checkpoint but
  // PRESERVES the current `conversation_id` / chat thread. The recruiter
  // stays in the same conversation, the stepper/banner disappear, and
  // the next message is routed to general chat instead of resuming the
  // wizard.
  // Task #1133 — confirmação migra de `window.confirm` para `AlertDialog`
  // canônico do DS LIA v4.2.2 (rounded-md, status-error, copy PT-BR
  // fail-loud). O prompt continua sendo um requisito porque o draft em
  // andamento (JD, competências, salário) é descartado server-side e
  // não pode ser recuperado.
  const handleCancelWizard = useCallback(async () => {
    const proceed = await requireWizardCancelConfirm("cancel");
    if (!proceed) return;
    await resetCurrentWizardSession();
    // Stay on the same conversation_id — only nudge focus back to the
    // input so the recruiter can keep talking with the LIA generalist.
  }, [requireWizardCancelConfirm, resetCurrentWizardSession]);

  const removeRecentItem = useRecentItemsStore((s) => s.removeItem);
  const removeStoredConversationId = useChatStateStore(
    (s) => s.removeConversationId,
  );
  const tChatHeader = useTranslations("chat.header");

  const handleDeleteConversation = useCallback(async () => {
    await deleteChatConversation({
      conversationId: chatConversationId,
      removeRecentItem,
      removeStoredConversationId,
      resetChat: handleNewChat,
      onError: (err) => {
        // eslint-disable-next-line no-console
        console.error("[UnifiedChat] failed to delete conversation", err);
        toast.error(tChatHeader("deleteError"), {
          description: tChatHeader("deleteErrorDescription"),
        });
      },
    });
  }, [
    chatConversationId,
    handleNewChat,
    removeRecentItem,
    removeStoredConversationId,
    tChatHeader,
  ]);

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

  // Onda 4-P2-4 (2026-05-24): removidas 5 emissões workflow:* (started,
  // updated, completed, failed, thinking) que eram DEAD EMISSIONS. Audit
  // exaustivo confirmou ZERO addEventListener('workflow:*') em todo src/.
  // Eram 5 CustomEvents emitidos sem consumer = ruído + ciclos CPU.
  // Backlog separado: se quisermos UI progress bar do wizard quando chat
  // fechado, criar consumer dedicated em sprint própria.

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
      // Onda 4-P2-6: canonical TTL persistence
      setPersisted(MODE_STORAGE_KEY, newMode);
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

  const dynamicPanelWidth = hasDynamicPanel ? dynamicPanelWidthPx : 0;
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
          onDelete={handleDeleteConversation}
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
              degradedStages={wizardDegradedStages}
              compact={effectiveMode === "floating"}
              onCancelWizard={handleCancelWizard}
            />
          </div>
        )}

        {/* Sprint Pipeline Templates Gap #6 (2026-05-26) — render auto-suggest card no chat.
            Card aparece quando backend graph (intake_node ou jd_enrichment_node) emite
            ui_action="suggest_pipeline_template" + data.templates. O fetch de apply é
            interno do card (PipelineTemplateSuggestion.handleApply usa o canonical proxy
            /api/backend-proxy/job-vacancies/{id}/apply-pipeline-template). onApplied/onSkip
            limpam a sugestão do state do wizard. vacancyId hoje é null (vaga ainda não
            persistida no intake/jd_enrichment); card desabilita "Aplicar" e orienta
            recrutador a re-aplicar pelo edit-job modal pós-publish. */}
        {wizard.pipelineTemplateSuggestions.length > 0 && wizard.currentStage !== "pipeline_template" && (
          <div className="px-4 pt-2" data-testid="wizard-pipeline-template-suggestion-container">
            <PipelineTemplateSuggestion
              templates={wizard.pipelineTemplateSuggestions}
              vacancyId={null}
              onApplied={() => wizard.skipPipelineTemplateSuggestion()}
              onSkip={() => wizard.skipPipelineTemplateSuggestion()}
            />
          </div>
        )}

        {/* Sprint Pipeline Templates Opção B (2026-05-26) — STAGE FORMAL panel.
            Quando o backend graph emite wizard_stage com stage="pipeline_template",
            renderizamos o painel canonical (em vez do card passivo acima). O
            recrutador DEVE decidir: aplicar um template sugerido OU usar o
            "Padrão da Empresa" canonical. Skip emite chat message livre que o
            backend graph parseia para avançar; apply usa o canonical proxy
            POST /api/backend-proxy/job-vacancies/{id}/apply-pipeline-template
            via wizard.applyPipelineTemplateFromWizard. vacancyId vem de
            stageData.vacancy_id quando disponível (publish posterior — em
            fluxos onde vaga ainda não existe, fica null e Apply é desabilitado). */}
        {wizard.currentStage === "pipeline_template" && wizard.stageData && (
          <div className="px-4 pt-2" data-testid="wizard-pipeline-template-stage-container">
            <WizardPipelineTemplateStagePanel
              templates={
                ((wizard.stageData as { templates?: unknown }).templates as
                  | import("./wizard/wizard-types").WizardPipelineTemplateSuggestion[]
                  | undefined) ?? []
              }
              suggestedTemplateId={
                ((wizard.stageData as { suggested_template_id?: string | null })
                  .suggested_template_id) ?? null
              }
              defaultPipelineStagesCount={
                ((wizard.stageData as { default_pipeline_stages_count?: number })
                  .default_pipeline_stages_count) ?? 0
              }
              allowSkip={
                ((wizard.stageData as { allow_skip?: boolean }).allow_skip) ?? true
              }
              onApply={async (templateId) => {
                const vacancyId = (wizard.stageData as { vacancy_id?: string | null })
                  .vacancy_id
                if (!vacancyId) {
                  // Sem vaga persistida, o backend graph é quem segura a
                  // transição. Emite mensagem livre PT-BR para o graph
                  // anotar a escolha e retomar.
                  sendChatMessage(
                    WIZARD_PIPELINE_TEMPLATE_DISPATCH.applyTemplate(templateId),
                  )
                  return
                }
                const response = await wizard.applyPipelineTemplateFromWizard(
                  vacancyId,
                  templateId,
                  "wizard_explicit",
                )
                if (!response.ok) {
                  const detail = await response
                    .json()
                    .catch(() => ({ detail: response.statusText }))
                  throw new Error(
                    typeof detail?.detail === "string" ? detail.detail : "apply_failed",
                  )
                }
                // Sinaliza ao backend graph que a stage foi resolvida.
                sendChatMessage(WIZARD_PIPELINE_TEMPLATE_DISPATCH.appliedAck)
              }}
              onSkip={async () => {
                // Backend graph parseia free-text para "use_default_pipeline".
                sendChatMessage(WIZARD_PIPELINE_TEMPLATE_DISPATCH.useDefault)
              }}
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
            onRegenerate={handleRegenerate}
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

      </div>

      {/* Split View: DynamicContextPanel — wider in fullscreen to use available space */}
      {hasDynamicPanel && (
        <div
          className="flex-shrink-0 flex p-2 relative"
          style={{ width: dynamicPanelWidthPx }}
        >
          {/* Handle de redimensionamento (borda chat/painel) — delta-based */}
          <div
            className="absolute left-0 top-0 w-1.5 h-full cursor-ew-resize z-10 group hover:bg-wedo-cyan/20 active:bg-wedo-cyan/30 transition-colors"
            onMouseDown={startPanelResize}
            role="separator"
            aria-orientation="vertical"
            aria-label="Redimensionar painel"
          >
            <div className="absolute left-0.5 top-1/2 -translate-y-1/2 w-0.5 h-8 rounded-full bg-lia-border-subtle group-hover:bg-wedo-cyan transition-colors" />
          </div>
          <div className="flex-1 min-w-0 rounded-xl border border-lia-border-subtle bg-lia-bg-primary shadow-lg shadow-black/10 overflow-hidden">
          <DynamicContextPanel
            stage={(dynamicPanel?.stage as WizardStage) ?? null}
            data={dynamicPanel?.data ?? {}}
            requiresApproval={dynamicPanel?.requires_approval ?? false}
            onApprove={() => sendApproval(true)}
            onReject={() => sendApproval(false)}
            onClose={closeDynamicPanel}
            onUpdate={(updates) => {
              collectedDataRef.current = mergeCollectedData(collectedDataRef.current, updates)
              sendChatMessage(wizardUpdateToMessage(updates), undefined, undefined, {
                right_panel_form: collectedDataRef.current,
              })
            }}
          />
          </div>
        </div>
      )}

      {/* Switch Task Modal (⌘K) */}
      <SwitchTaskModal
        isOpen={showSwitchTask}
        onClose={() => setShowSwitchTask(false)}
        onSelectSession={handleSelectSession}
        currentSessionId={chatConversationId}
      />

      {/*
        Task #1133 — modal canônico de confirmação ao cancelar wizard
        ativo. Mesma instância serve "Cancelar wizard" (stepper) e
        "Nova conversa" (header/slash); o `mode` diferencia só o copy
        do título/CTA. Botão destrutivo usa `buttonVariants` + classes
        status-error do DS LIA v4.2.2 (rounded-md herdado do Button).
      */}
      <AlertDialog
        open={wizardConfirm.open}
        onOpenChange={(open) => {
          if (!open) closeWizardConfirm(false);
        }}
      >
        <AlertDialogContent data-testid="wizard-cancel-confirm-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>
              {wizardConfirm.mode === "new-chat"
                ? "Iniciar nova conversa e descartar rascunho?"
                : "Cancelar criação da vaga?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Você perderá o rascunho desta vaga (JD, competências, salário)
              e voltará ao chat geral. Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              data-testid="wizard-cancel-confirm-keep"
              onClick={() => closeWizardConfirm(false)}
            >
              Continuar editando
            </AlertDialogCancel>
            <AlertDialogAction
              data-testid="wizard-cancel-confirm-discard"
              onClick={() => closeWizardConfirm(true)}
              className={cn(
                buttonVariants({ variant: "destructive" }),
                "bg-status-error text-white hover:bg-status-error/90",
              )}
            >
              {wizardConfirm.mode === "new-chat"
                ? "Descartar e iniciar nova"
                : "Descartar rascunho"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
