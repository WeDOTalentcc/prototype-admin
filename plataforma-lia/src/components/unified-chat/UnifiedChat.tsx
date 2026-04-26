"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { X, Maximize2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { DynamicContextPanel, SPLIT_STAGES } from "./wizard/DynamicContextPanel"
import type { WizardStage } from "./wizard/wizard-types"
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal"
import { useNavigationIntent } from "@/hooks/shared/use-navigation-intent"
import { useWizardIntegration } from "./wizard/useWizardIntegration"
import { useWizardFlow } from "./wizard/useWizardFlow"
import { WizardProgressBar } from "./wizard/WizardProgressBar"
import {
  WIZARD_PLAN_MESSAGE_ID,
  WIZARD_PLAN_TITLE,
  WIZARD_PUBLISHED_MESSAGE_ID,
  WIZARD_PUBLISHED_TITLE,
  buildPlanFlowSteps,
  buildPublishedJobCard,
  isWizardClosingStage,
  planStepsEqual,
  publishedJobCardsEqual,
  type WizardPublishedJobCardData,
} from "./wizard/wizard-plan-card"
import type { FlowStep } from "@/components/workflow-rail/FlowStepMessage"
import { ProgressiveDisclosure } from "./wizard/ProgressiveDisclosure"
import { UnifiedChatHeader } from "./UnifiedChatHeader"
import { UnifiedChatInput } from "./UnifiedChatInput"
import { UnifiedChatEmptyState } from "./UnifiedChatEmptyState"
import { UnifiedMessageList } from "./UnifiedMessageList"
import type { ChatMode } from "./unified-chat-types"
import {
  formatGlossaryEntryMarkdown,
  lookupGlossaryTerm,
} from "@/services/lia-api/glossary-api"

const DEFINIR_REGEX = /^\/(?:definir|glossario|glossário)(?:\s+(.+))?$/i

const MODE_STORAGE_KEY = "lia-chat-mode"

const WIZARD_STAGE_LABELS: Record<string, string> = {
  intake: "Criando vaga · Início",
  jd_enrichment: "Criando vaga · Descrição",
  bigfive: "Criando vaga · Perfil",
  salary: "Criando vaga · Salário",
  competency: "Criando vaga · Competências",
  wsi_questions: "Criando vaga · Triagem",
  eligibility: "Criando vaga · Elegibilidade",
  review: "Criando vaga · Revisão",
  publish: "Criando vaga · Publicação",
  calibration: "Calibrando · Candidatos",
  handoff: "Criando vaga · Finalização",
  done: "Vaga criada",
}
const WIDTH_STORAGE_KEY = "lia-chat-width"
const DEFAULT_WIDTH = 380
const MIN_WIDTH = 300
const MAX_WIDTH = 600

function getStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar"
  const stored = localStorage.getItem(MODE_STORAGE_KEY)
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen") return stored
  return "sidebar"
}

function getStoredWidth(): number {
  if (typeof window === "undefined") return DEFAULT_WIDTH
  const stored = localStorage.getItem(WIDTH_STORAGE_KEY)
  if (stored) {
    const n = parseInt(stored, 10)
    if (!isNaN(n) && n >= MIN_WIDTH && n <= MAX_WIDTH) return n
  }
  return DEFAULT_WIDTH
}

interface Props {
  renderMode?: "inline" | "overlay"
  initialMode?: ChatMode
  className?: string
}

/**
 * UnifiedChat — Single chat component with 3 visual modes (Notion AI-inspired).
 *
 * Includes:
 * - HITL confirmation cards (all modes)
 * - DynamicContextPanel split view (sidebar expands, fullscreen adds panel)
 * - Auto-scroll, streaming, thinking indicators
 */
export function UnifiedChat({ renderMode = "overlay", initialMode, className }: Props) {
  const [mode, setMode] = useState<ChatMode>(initialMode ?? getStoredMode())
  const [inputText, setInputText] = useState("")
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [showSwitchTask, setShowSwitchTask] = useState(false)
  const [showFullscreenHint, setShowFullscreenHint] = useState(false)
  const fullscreenHintShown = useRef(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [sidebarWidthPx, setSidebarWidthPx] = useState(getStoredWidth)
  const [isResizing, setIsResizing] = useState(false)
  const widthRef = useRef(sidebarWidthPx)

  useEffect(() => {
    if (!isResizing) return
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, window.innerWidth - e.clientX))
      widthRef.current = newWidth
      setSidebarWidthPx(newWidth)
    }
    const handleMouseUp = () => {
      setIsResizing(false)
      localStorage.setItem(WIDTH_STORAGE_KEY, String(widthRef.current))
    }
    document.body.style.cursor = "ew-resize"
    document.body.style.userSelect = "none"
    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
    return () => {
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isResizing])

  const authUser = useAuthStore((s) => s.user)
  const tc = useTranslations('common')
  const userName = authUser?.name || authUser?.email || tc('defaultUserName')

  const {
    isOpen,
    open,
    close,
    contextPage,
    dynamicPanel,
    closeDynamicPanel,
  } = useLiaFloat()

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
  } = useLiaChatContext()

  const { detect: detectNavIntent } = useNavigationIntent()

  // Wire wizard integration (file→wizard, question events, slash commands)
  const { handleSlashCommand } = useWizardIntegration({
    isWizardActive: !!dynamicPanel,
    currentStage: dynamicPanel?.stage ?? null,
    sendMessage: sendChatMessage,
  })

  // Canonical wizard state on the chat surface — listens to the same
  // `lia:wizard-stage-payload` window event that powers `WizardContext` for
  // the right-side panel. Reusing the hook avoids a parallel state channel.
  const wizard = useWizardFlow()
  const {
    currentStage: wizardStage,
    stageData: wizardStageData,
    completeness: wizardCompleteness,
    stageHistory: wizardHistory,
  } = wizard
  const wizardActive =
    wizardStage !== null && wizardStage !== "done" && wizardStage !== "handoff"
  const planCardInsertedRef = useRef(false)
  const publishedCardInsertedRef = useRef(false)

  // Insert the non-persisted "Plano de trabalho" assistant card into the feed
  // the first time the wizard reports stage=`intake`, then keep its
  // `flowSteps` in sync as new stages stream in. Removed when the wizard
  // resets so a fresh run can re-emit it cleanly.
  useEffect(() => {
    if (!wizardStage) {
      planCardInsertedRef.current = false
      return
    }
    const flowSteps = buildPlanFlowSteps(wizardStage)
    setChatMessages((prev) => {
      const exists = prev.some((m) => m.id === WIZARD_PLAN_MESSAGE_ID)
      if (!exists) {
        if (planCardInsertedRef.current) return prev
        planCardInsertedRef.current = true
        const planMsg = {
          id: WIZARD_PLAN_MESSAGE_ID,
          sender: "lia" as const,
          content: WIZARD_PLAN_TITLE,
          timestamp: new Date().toISOString(),
          metadata: { type: "wizard_plan", flowSteps },
        }
        return [...prev, planMsg]
      }
      // Update existing card without forcing a new array if nothing changed.
      let changed = false
      const next = prev.map((m) => {
        if (m.id !== WIZARD_PLAN_MESSAGE_ID) return m
        const prevSteps = (m.metadata?.flowSteps as FlowStep[] | undefined) ?? []
        if (planStepsEqual(prevSteps, flowSteps)) return m
        changed = true
        return { ...m, metadata: { ...(m.metadata ?? {}), type: "wizard_plan", flowSteps } }
      })
      return changed ? next : prev
    })
  }, [wizardStage, setChatMessages])

  // Inject the non-persisted "Vaga publicada" closing card into the feed
  // when the wizard reaches `done`/`handoff`. The plan card and progress
  // bar both unmount at that point, so without this card the conclusion
  // is silent — recruiters lose track of the job they just published.
  useEffect(() => {
    // Reset the dedupe latch on any non-closing stage (including null and a
    // brand-new `intake` after a previous run reached `handoff`). This way a
    // back-to-back wizard run still re-emits its closing card.
    if (!wizardStage || !isWizardClosingStage(wizardStage)) {
      publishedCardInsertedRef.current = false
      return
    }
    const cardData = buildPublishedJobCard(wizardStage, wizardStageData)
    if (!cardData) return
    setChatMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === WIZARD_PUBLISHED_MESSAGE_ID)
      if (idx === -1) {
        if (publishedCardInsertedRef.current) return prev
        publishedCardInsertedRef.current = true
        const publishedMsg = {
          id: WIZARD_PUBLISHED_MESSAGE_ID,
          sender: "lia" as const,
          content: WIZARD_PUBLISHED_TITLE,
          timestamp: new Date().toISOString(),
          metadata: { type: "wizard_published_job", publishedJob: cardData },
        }
        return [...prev, publishedMsg]
      }
      // Same payload re-emitted — keep the existing card to avoid churn.
      const existing = prev[idx]
      const prevData =
        (existing.metadata?.publishedJob as WizardPublishedJobCardData | undefined) ?? null
      if (publishedJobCardsEqual(prevData, cardData)) return prev
      const next = prev.slice()
      next[idx] = {
        ...existing,
        metadata: {
          ...(existing.metadata ?? {}),
          type: "wizard_published_job",
          publishedJob: cardData,
        },
      }
      return next
    })
  }, [wizardStage, wizardStageData, setChatMessages])

  // Persist mode preference
  useEffect(() => {
    localStorage.setItem(MODE_STORAGE_KEY, mode)
  }, [mode])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text) return

    // `/definir <termo>` is resolved locally against the canonical glossary
    // endpoint so recruiters get the official WSI/BARS/Bloom definition without
    // round-tripping the LIA agent (Task #745).
    const definirMatch = text.match(DEFINIR_REGEX)
    if (definirMatch) {
      const term = (definirMatch[1] ?? "").trim()
      const now = new Date().toISOString()
      const userMsg = {
        id: `user-${Date.now()}`,
        sender: "user" as const,
        content: text,
        timestamp: now,
      }
      // Bare `/definir` (no term) — answer locally with usage guidance instead
      // of hitting the backend agent.
      if (!term) {
        const helpMsg = {
          id: `lia-${Date.now()}-glossary-help`,
          sender: "lia" as const,
          content:
            "Informe o termo apos o comando. Exemplos: `/definir WSI`, `/definir Bloom`, `/definir BARS`.",
          timestamp: now,
        }
        setChatMessages((prev) => [...prev, userMsg, helpMsg])
        setInputText("")
        setAttachedFile(null)
        return
      }
      const pendingId = `lia-${Date.now()}-glossary`
      const pendingMsg = {
        id: pendingId,
        sender: "lia" as const,
        content: `Buscando a definicao oficial de **${term}**...`,
        timestamp: now,
      }
      setChatMessages((prev) => [...prev, userMsg, pendingMsg])
      setInputText("")
      setAttachedFile(null)
      void lookupGlossaryTerm(term).then((result) => {
        const replyContent = result.ok
          ? formatGlossaryEntryMarkdown(result.entry)
          : `${result.message}\n\n_Tente outro termo, por exemplo: \`/definir WSI\`._`
        setChatMessages((prev) =>
          prev.map((m) => (m.id === pendingId ? { ...m, content: replyContent } : m)),
        )
      })
      return
    }

    // Intercept slash commands before sending to backend
    if (text.startsWith("/") && handleSlashCommand(text)) {
      setInputText("")
      return
    }
    sendChatMessage(text)
    setInputText("")
    setAttachedFile(null)

    detectNavIntent(text).then((result) => {
      // BUG-18 fix: 0.85 era muito alto — frases naturais como "me leva pra vagas"
      // atingiam no máximo ~0.70 mesmo após fix do dampening no backend.
      // 0.65 captura imperativos de navegação sem falso-positivar perguntas genéricas.
      if (result?.page && result.confidence >= 0.65) {
        window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
          detail: { page: result.page, hint: result.hint },
        }))
      }
    })
  }, [inputText, sendChatMessage, detectNavIntent, handleSlashCommand])

  const handleSuggestionClick = useCallback((prompt: string) => {
    setInputText(prompt)
    setTimeout(() => {
      sendChatMessage(prompt)
      setInputText("")
    }, 100)
  }, [sendChatMessage])

  const handleNewChat = useCallback(() => {
    switchChatContext("general", { conversationId: null })
    setChatMessages([])
    setInputText("")
    setAttachedFile(null)
  }, [switchChatContext, setChatMessages])

  // Switch to a different conversation
  const handleSelectSession = useCallback(async (sessionId: string) => {
    setChatConversationId(sessionId)
    await loadChatHistory(sessionId)
    setShowSwitchTask(false)
  }, [setChatConversationId, loadChatHistory])

  const currentModeRef = useRef(mode)
  currentModeRef.current = mode

  // Suggest fullscreen once when wizard starts in non-fullscreen mode
  useEffect(() => {
    if (
      dynamicPanel?.stage === "intake" &&
      mode !== "fullscreen" &&
      renderMode !== "inline" &&
      !fullscreenHintShown.current
    ) {
      fullscreenHintShown.current = true
      setShowFullscreenHint(true)
      const timer = setTimeout(() => setShowFullscreenHint(false), 7000)
      return () => clearTimeout(timer)
    }
  }, [dynamicPanel?.stage, mode, renderMode])

  // Workflow Rail integration — emit lifecycle events as wizard stage changes
  const prevStageRef = useRef<string | null>(null)
  const wizardWorkflowIdRef = useRef<string | null>(null)

  useEffect(() => {
    const stage = dynamicPanel?.stage ?? null
    const prevStage = prevStageRef.current
    if (stage === prevStage) return
    prevStageRef.current = stage

    if (stage === "intake" && !prevStage) {
      wizardWorkflowIdRef.current = `wizard-${Date.now()}`
      window.dispatchEvent(new CustomEvent("workflow:started", {
        detail: { id: wizardWorkflowIdRef.current, type: "campaign", label: "Criando vaga", stage: "intake" },
      }))
    } else if (stage && wizardWorkflowIdRef.current) {
      if (stage === "done") {
        window.dispatchEvent(new CustomEvent("workflow:completed", {
          detail: { id: wizardWorkflowIdRef.current, outcome: "success" },
        }))
        wizardWorkflowIdRef.current = null
      } else {
        window.dispatchEvent(new CustomEvent("workflow:updated", {
          detail: { id: wizardWorkflowIdRef.current, stage, label: WIZARD_STAGE_LABELS[stage] ?? stage },
        }))
      }
    } else if (!stage && prevStage && wizardWorkflowIdRef.current) {
      window.dispatchEvent(new CustomEvent("workflow:failed", {
        detail: { id: wizardWorkflowIdRef.current, error: "Fluxo interrompido" },
      }))
      wizardWorkflowIdRef.current = null
    }
  }, [dynamicPanel?.stage])

  useEffect(() => {
    if (!wizardWorkflowIdRef.current) return
    window.dispatchEvent(new CustomEvent("workflow:thinking", {
      detail: { id: wizardWorkflowIdRef.current, isThinking: chatIsThinking },
    }))
  }, [chatIsThinking])

  const handleModeChange = useCallback((newMode: ChatMode) => {
    const prevMode = currentModeRef.current
    if (newMode === "minimized") {
      close()
      window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: "minimized", prevMode } }))
      return
    }
    setMode(newMode)
    localStorage.setItem(MODE_STORAGE_KEY, newMode)
    window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: newMode, prevMode } }))
    if (newMode === "fullscreen") {
      close()
      window.dispatchEvent(new CustomEvent("lia:navigate-chat-page", { detail: {} }))
    } else if (newMode === "floating") {
      open()
    } else if (newMode === "sidebar") {
      open()
      if (prevMode === "fullscreen") {
        window.dispatchEvent(new CustomEvent("lia:leave-fullscreen-chat", { detail: { targetMode: newMode } }))
      }
    }
  }, [close, open])

  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileAttach = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.size <= 10 * 1024 * 1024) {
      setAttachedFile(file)
    }
    if (e.target) e.target.value = ""
  }, [])

  const conversationTitle = chatMessages.find(m => m.sender === "user")?.content?.slice(0, 40) || null
  const hasMessages = chatMessages.length > 0
  const hasDynamicPanel = !!dynamicPanel && SPLIT_STAGES.includes(dynamicPanel.stage as WizardStage)
  const activeTaskLabel = dynamicPanel?.stage
    ? (WIZARD_STAGE_LABELS[dynamicPanel.stage] ?? dynamicPanel.stage)
    : null

  if (renderMode === "overlay" && !isOpen && mode !== "fullscreen") return null

  const isInline = renderMode === "inline"
  const effectiveMode: ChatMode = isInline ? "sidebar" : mode

  const dynamicPanelWidth = hasDynamicPanel ? 340 : 0
  const inlineWidth = isInline ? sidebarWidthPx + dynamicPanelWidth : undefined

  return (
    <div
      className={cn(
        "flex bg-lia-bg-primary relative overflow-hidden",
        isInline
          ? "flex-shrink-0 border border-lia-border-subtle rounded-xl h-full"
          : mode === "fullscreen"
            ? "fixed inset-0 z-50"
            : mode === "sidebar"
              ? "fixed top-2 right-2 bottom-2 z-40 border border-lia-border-subtle rounded-xl shadow-xl"
              : "fixed bottom-4 right-4 w-[360px] h-[520px] z-30 rounded-xl border border-lia-border-subtle shadow-xl",
        className
      )}
      style={isInline ? { width: `${inlineWidth}px` } : (!isInline && mode === "sidebar") ? { width: `${sidebarWidthPx + dynamicPanelWidth}px` } : undefined}
      data-chat-mode={effectiveMode}
      data-render-mode={renderMode}
    >
      {(isInline || (!isInline && mode === "sidebar")) && (
        <div
          className="absolute left-0 top-0 w-1.5 h-full cursor-ew-resize z-10 group hover:bg-wedo-cyan/20 active:bg-wedo-cyan/30 transition-colors"
          onMouseDown={(e) => {
            e.preventDefault()
            setIsResizing(true)
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
            />
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
            interactionCount={chatMessages.filter(m => m.sender === "user").length}
          />
        )}

        {/* Fullscreen suggestion hint (once when wizard starts in non-fullscreen) */}
        {showFullscreenHint && (
          <div className="px-4 pb-1">
            <div className="flex items-center justify-between px-3 py-2 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary">
              <span className="text-xs text-lia-text-secondary">
                Tela cheia melhora a experiência do wizard
              </span>
              <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                <button
                  onClick={() => { handleModeChange("fullscreen"); setShowFullscreenHint(false) }}
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
        />
      </div>

      {/* Split View: DynamicContextPanel — wider in fullscreen to use available space */}
      {hasDynamicPanel && (
        <div className={cn(
          "flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto",
          effectiveMode === "fullscreen" ? "w-[420px]" : "w-[340px]"
        )}>
          <DynamicContextPanel
            stage={(dynamicPanel?.stage as WizardStage) ?? null}
            data={dynamicPanel?.data ?? {}}
            requiresApproval={dynamicPanel?.requires_approval ?? false}
            onApprove={() => sendApproval(true)}
            onReject={() => sendApproval(false)}
            onClose={closeDynamicPanel}
            onUpdate={(updates) => sendChatMessage(JSON.stringify({ type: "wizard_update", updates }))}
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
  )
}
