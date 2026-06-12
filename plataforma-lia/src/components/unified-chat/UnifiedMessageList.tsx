"use client"

import React, { useEffect, useMemo, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import { Copy, Plus, ThumbsUp, ThumbsDown, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import FlowStepMessage from "@/components/unified-chat/FlowStepMessage"
import { AgentActivityTimeline } from "./AgentActivityTimeline"
import { AgentActivitySummary } from "./AgentActivitySummary"
import { OutreachCard } from "./OutreachCard"
import { WizardPublishedJobCard } from "./wizard/WizardPublishedJobCard"
import { WizardPipelineTemplateCard } from "./wizard/WizardPipelineTemplateCard"
import { WizardJdCard } from "./wizard/WizardJdCard"
import { WizardWsiCard } from "./wizard/WizardWsiCard"
import { WizardCalibrationCard } from "./wizard/WizardCalibrationCard"
import { WebsiteProposalCard } from "./WebsiteProposalCard"
import { CandidateProfileCard, type CandidateProfileActionId } from "./candidate/CandidateProfileCard"
import { CandidateEvaluationCard } from "./candidate/CandidateEvaluationCard"
import {
  CANDIDATE_PROFILE_CARD_TYPE,
  CANDIDATE_EVALUATION_CARD_TYPE,
  type CandidateProfileCardData,
  type CandidateEvaluationCardData,
} from "./candidate/candidate-card-data"
import type { PipelineTemplateCardData, PipelineTemplateOption, WizardPublishedJobCardData } from "./wizard/wizard-plan-card"
import { renderMarkdown } from "@/lib/render-markdown"
import { submitThumbsFeedback } from "@/services/lia-api/feedback-api"
import { toast } from "@/lib/toast"
import type { LiaChatMessage } from "@/hooks/chat/use-lia-chat-connection"
import { useTypewriter } from "@/hooks/chat/useTypewriter"
import { WIZARD_PLAN_MESSAGE_ID } from "./wizard/wizard-plan-card"
import { NavigationHintCard } from "./NavigationHintCard"
import { ProactiveSuggestionCard } from "./ProactiveSuggestionCard"
import { ResponseBlockRenderer } from "./ResponseBlockRenderer"
import { PROACTIVE_HINTS_MESSAGE_TYPE } from "./proactive-suggestion-injector"
import type { ProactiveHint } from "@/hooks/proactive/use-proactive-hints"
import { TastingInsightCard } from "./TastingInsightCard"
import { WeeklyDigestChatMessage } from "@/components/notifications/weekly-digest-chat-message"
import type { WeeklyDigestData } from "@/components/notifications/weekly-digest-notification"
import type { ChatMode } from "./unified-chat-types"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Textarea } from "@/components/ui/textarea"

/**
 * Task #570 audit — qualitative reason categories surfaced in the thumbs-down
 * popover. Keys must match `chat.messageActions.thumbsDownCategory.*` in
 * `messages/{en,pt-BR}.json` and the backend's `category` enum.
 */
const THUMBS_DOWN_CATEGORIES = ["inaccurate", "wrong_tone", "hallucinated"] as const
type ThumbsDownCategory = (typeof THUMBS_DOWN_CATEGORIES)[number]

function isWeeklyDigestMeta(meta: Record<string, unknown> | undefined): meta is Record<string, unknown> & { digest: WeeklyDigestData; recruiterName?: string } {
  if (!meta || meta.type !== "weekly_digest") return false
  const d = meta.digest as Record<string, unknown> | undefined
  return d != null && typeof d === "object" && "pipeline" in d && "atRiskJobs" in d && "compliance" in d
}

interface Props {
  mode: ChatMode
  messages: LiaChatMessage[]
  isStreaming: boolean
  streamingContent: string
  isThinking: boolean
  thinkingSteps: string[]
  userName: string
  conversationId?: string | null
  /**
   * Called when the user clicks a clarification option chip (Tier 8 fallback).
   * The handler typically forwards the chip's `value` to sendChatMessage.
   */
  onChipClick?: (value: string) => void
  /**
   * Task #570 P1 — invoked with the assistant message id when the user
   * presses the regenerate button. The parent forwards it to
   * `requestRegeneration` + `sendMessage(prevUserText, …, { regenerateOf })`.
   */
  onRegenerate?: (messageId: string) => void
}

function MessageActions({
  messageId,
  content,
  conversationId,
  initialThumbs,
  onRegenerate,
}: {
  messageId: string
  content: string
  conversationId?: string | null
  /**
   * Audit gap F3 — hydrated from `LiaChatMessage.thumbs` (which itself
   * is fed by `/lia/feedback/by-conversation`). Lets the action row reflect
   * a prior rating on first render so a refresh doesn't blank it out.
   */
  initialThumbs?: "up" | "down" | null
  onRegenerate?: (messageId: string) => void
}) {
  const t = useTranslations('chat.messageActions')
  const [thumbsState, setThumbsState] = useState<"up" | "down" | null>(initialThumbs ?? null)
  const [downOpen, setDownOpen] = useState(false)
  const [downCategory, setDownCategory] = useState<ThumbsDownCategory | null>(null)
  const [downText, setDownText] = useState("")

  // `useChatMessages` populates `LiaChatMessage.thumbs` asynchronously after
  // the history fetch + `/lia/feedback/by-conversation` resolves, which lands
  // *after* this component's first render. Sync local state when the
  // hydrated value flips, but only when the user hasn't already clicked
  // (we never want a late hydration to overwrite a fresh in-flight click).
  const hydratedRef = useRef(initialThumbs ?? null)
  useEffect(() => {
    const next = initialThumbs ?? null
    if (next === hydratedRef.current) return
    hydratedRef.current = next
    setThumbsState((prev) => (prev == null ? next : prev))
  }, [initialThumbs])

  const handleThumbsUp = () => {
    if (thumbsState === "up") return
    // Task #1297 fail-loud: sem conversationId não há como persistir — avisa o
    // usuário em vez de fingir sucesso com estado só-otimista (canonical-fix:
    // proibido silent fallback). Era O bug da captura morta (id nunca chegava).
    if (!conversationId) {
      toast.error(t('feedbackErrorToast'))
      return
    }
    setThumbsState("up")
    submitThumbsFeedback(conversationId, messageId, "up", {
      messageContext: { lia_response: content },
    })
      .then(() => {
        toast.success(t('feedbackThanksToast'))
      })
      .catch(() => {
        setThumbsState(initialThumbs ?? null)
        toast.error(t('feedbackErrorToast'))
      })
  }

  const handleThumbsDownClick = () => {
    // Record the immediate "down" signal once; the popover collects extra
    // qualitative context (category / free text) which is sent on submit.
    if (thumbsState !== "down") {
      if (!conversationId) {
        toast.error(t('feedbackErrorToast'))
        return
      }
      setThumbsState("down")
      submitThumbsFeedback(conversationId, messageId, "down", {
        messageContext: { lia_response: content },
      }).catch(() => {
        setThumbsState(initialThumbs ?? null)
        toast.error(t('feedbackErrorToast'))
      })
    }
    setDownOpen(true)
  }

  const submitDownDetails = () => {
    if (conversationId && (downCategory || downText.trim())) {
      submitThumbsFeedback(conversationId, messageId, "down", {
        category: downCategory ?? undefined,
        feedbackText: downText.trim() || undefined,
        messageContext: { lia_response: content },
      })
        .then(() => {
          toast.success(t('feedbackThanksToast'))
        })
        .catch(() => {
          // The "down" signal was already persisted on the first click, so we
          // don't roll back the rating — but surface the follow-up failure so
          // the user knows the extra detail didn't save (fail-loud).
          toast.error(t('feedbackErrorToast'))
        })
    }
    setDownOpen(false)
  }

  const isUpActive = thumbsState === "up"
  const isDownActive = thumbsState === "down"

  return (
    <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title={t('copyTitle')}
        aria-label={t('copyAriaLabel')}
        onClick={() => {
          navigator.clipboard.writeText(content)
        }}
      >
        <Copy className="w-3.5 h-3.5" />
      </button>
      <button
        className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
        title={t('insertTitle')}
        aria-label={t('insertAriaLabel')}
        onClick={() => {
          window.dispatchEvent(
            new CustomEvent("lia:prefill-message", {
              detail: { message: content },
            })
          )
        }}
      >
        <Plus className="w-3.5 h-3.5" />
      </button>
      <button
        className={cn(
          "p-1 rounded hover:bg-lia-interactive-hover hover:text-lia-text-secondary",
          isUpActive ? "text-status-success" : "text-lia-text-disabled",
        )}
        title={isUpActive ? t('helpfulActiveTitle') : t('helpfulTitle')}
        aria-label={isUpActive ? t('helpfulActiveAriaLabel') : t('helpfulAriaLabel')}
        aria-pressed={isUpActive}
        onClick={handleThumbsUp}
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <Popover open={downOpen} onOpenChange={setDownOpen}>
        <PopoverTrigger asChild>
          <button
            className={cn(
              "p-1 rounded hover:bg-lia-interactive-hover hover:text-lia-text-secondary",
              isDownActive ? "text-status-error" : "text-lia-text-disabled",
            )}
            title={isDownActive ? t('notHelpfulActiveTitle') : t('notHelpfulTitle')}
            aria-label={isDownActive ? t('notHelpfulActiveAriaLabel') : t('notHelpfulAriaLabel')}
            aria-pressed={isDownActive}
            onClick={handleThumbsDownClick}
          >
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-3" align="start" sideOffset={8}>
          <div className="flex flex-col gap-3">
            <span className="text-xs font-medium text-lia-text-primary">
              {t('thumbsDownReasonTitle')}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {THUMBS_DOWN_CATEGORIES.map((cat) => {
                const active = downCategory === cat
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setDownCategory(active ? null : cat)}
                    className={cn(
                      "px-2 py-1 text-[12px] rounded-md border transition-colors",
                      active
                        ? "bg-lia-interactive-hover border-lia-border-medium text-lia-text-primary"
                        : "border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover",
                    )}
                    aria-pressed={active}
                  >
                    {t(`thumbsDownCategory.${cat}`)}
                  </button>
                )
              })}
            </div>
            <Textarea
              value={downText}
              onChange={(e) => setDownText(e.target.value)}
              placeholder={t('thumbsDownPlaceholder')}
              className="min-h-16 text-xs"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDownOpen(false)}
                className="px-2 py-1 text-[12px] rounded-md text-lia-text-secondary hover:bg-lia-interactive-hover"
              >
                {t('thumbsDownCancel')}
              </button>
              <button
                type="button"
                onClick={submitDownDetails}
                className="px-2 py-1 text-[12px] rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:opacity-90"
              >
                {t('thumbsDownSubmit')}
              </button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
      {onRegenerate && (
        <button
          className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-disabled hover:text-lia-text-secondary"
          title={t('regenerateTitle')}
          aria-label={t('regenerateAriaLabel')}
          onClick={() => onRegenerate(messageId)}
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  )
}

export function UnifiedMessageList({
  mode,
  messages,
  isStreaming,
  streamingContent,
  isThinking,
  thinkingSteps,
  userName,
  conversationId,
  onChipClick,
  onRegenerate,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Typewriter (2026-06-04): o provider entrega a resposta num burst (sem
  // streaming incremental real). Revelamos a mensagem LIA mais recente
  // char-a-char (efeito Manus). Dirigido pelo conteudo da msg mais nova, entao
  // funciona tanto pra append novo quanto pra update in-place.
  const _newestLiaId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].sender === "lia") return messages[i].id
    }
    return null
  }, [messages])
  const _newestLiaContent = useMemo(
    () => messages.find((m) => m.id === _newestLiaId)?.content ?? "",
    [messages, _newestLiaId],
  )
  // Gate the reveal on `liveActive` (set below): while the live reasoning
  // timeline is still showing, the answer is held back so the recruiter reads
  // the reasoning FIRST and the answer types out AFTER it settles (Replit-style).
  // enabled flips false→true on hand-off, which restarts the typewriter from 0.

  // Live activity lifecycle (2026-06-04): decouple the timeline's mount from the
  // raw isThinking/isStreaming flags. They flip to false the instant the
  // `message` event lands, which used to yank the live timeline mid-turn (hard
  // cut). We turn `liveActive` ON when the turn starts and let the timeline tell
  // us when it has finished its graceful terminal frame (`onFinished`), so the
  // box settles into "✓ N ações" and hands off to the persistent summary instead
  // of disappearing abruptly.
  const [liveActive, setLiveActive] = useState(false)
  // Bug fix (2026-06-05): id da LIA msg mais nova QUANDO o turno comecou.
  // Sem isso, durante o pensando de uma nova pergunta o _newestLiaId ainda
  // aponta pra resposta ANTERIOR -> ela some e volta no fim. So a resposta
  // NOVA (id != baseline) deve ser segurada; a anterior fica visivel.
  const _heldBaselineRef = useRef<string | null>(null)
  useEffect(() => {
    if (isThinking || isStreaming) {
      if (!liveActive) _heldBaselineRef.current = _newestLiaId ?? null
      setLiveActive(true)
    }
  }, [isThinking, isStreaming, liveActive, _newestLiaId])
  useEffect(() => {
    if (!liveActive) _heldBaselineRef.current = null
  }, [liveActive])
  // Failsafe: `liveActive` is normally cleared by the timeline's `onFinished`
  // hand-off (which paces out any remaining reasoning steps one-by-one before
  // firing). If that signal never arrives (e.g. the turn ends without the
  // timeline mounting), the held answer would stay hidden forever — so once the
  // raw turn flags are both off, force the reveal after a generous ceiling that
  // comfortably outlasts a normal paced hand-off and only rescues a stuck UI.
  useEffect(() => {
    if (!liveActive || isThinking || isStreaming) return
    const t = setTimeout(() => setLiveActive(false), 3000)
    return () => clearTimeout(t)
  }, [liveActive, isThinking, isStreaming])

  const { displayed: _newestLiaDisplayed } = useTypewriter(_newestLiaContent, {
    enabled: _newestLiaId != null && !liveActive,
  })

  // Auto-scroll to bottom (FE-2 2026-06-05): track the typewriter reveal
  // (`_newestLiaDisplayed`) and `liveActive` so the view follows each typed
  // chunk — not just new messages / raw streaming flags. Declared AFTER the
  // typewriter so it can depend on its output (no early return between hooks).
  // `behavior: "auto"` while content is revealing avoids smooth-scroll fighting
  // the rapid per-char updates; smooth otherwise for a calm settle.
  const _isRevealing = _newestLiaId != null && !liveActive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: _isRevealing ? "auto" : "smooth",
    })
  }, [
    messages.length,
    streamingContent,
    isThinking,
    _newestLiaDisplayed,
    liveActive,
    _isRevealing,
  ])

  // Auto-scroll robusto (2026-06-06): o reasoning timeline (AgentActivityTimeline)
  // revela passos via setTimeout INTERNO — esse crescimento NAO e dependencia do
  // efeito de scroll acima, entao enquanto a IA "constroi" (fase de raciocinio) a
  // view nao acompanhava (Paulo: "o chat nao sobe quando esta construindo"). Um
  // ResizeObserver no conteudo segue QUALQUER crescimento de altura e fixa no fim
  // — desde que o usuario JA esteja perto do fim (≤120px), respeitando quem rolou
  // pra cima pra reler durante o turno. Cobre reasoning, blocos RRP e typewriter.
  // (jsdom nao tem ResizeObserver → feature-guard mantem os testes verdes.)
  useEffect(() => {
    if (typeof ResizeObserver === "undefined") return
    const container = containerRef.current
    const content = contentRef.current
    if (!container || !content) return
    const ro = new ResizeObserver(() => {
      const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight
      if (distanceFromBottom <= 120) {
        bottomRef.current?.scrollIntoView({ behavior: "auto" })
      }
    })
    ro.observe(content)
    return () => ro.disconnect()
  }, [])

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto"
    >
      <div
        ref={contentRef}
        className={cn(
          "px-4 py-4 space-y-4",
          mode === "fullscreen" ? "max-w-[720px] mx-auto w-full" : ""
        )}
      >
      {messages.map((message) => {
        const isLia = message.sender === "lia"
        const meta = message.metadata
        const hasPlan = message.executionPlan != null
        const hasFlowSteps = meta?.flowSteps != null
        const hasNavHint = meta?.navigation_hint != null
        const hasTastingInsights = Array.isArray(meta?.tasting_insights) && (meta!.tasting_insights as unknown[]).length > 0
        const weeklyDigestMeta = isWeeklyDigestMeta(meta)
        const hasOutreach = meta?.type === "outreach_message" && meta?.outreach != null
        const hasPublishedJob =
          meta?.type === "wizard_published_job" && meta?.publishedJob != null
        const hasTemplateCard =
          meta?.type === "wizard_template_select" && meta?.templateCard != null
        const hasWizardJdCard =
          meta?.type === "wizard_stage_card" && meta?.wizardStage === "jd_enrichment"
        const hasWizardWsiCard =
          meta?.type === "wizard_stage_card" && meta?.wizardStage === "wsi_questions"
        const hasWizardCalibrationCard =
          meta?.type === "wizard_stage_card" && meta?.wizardStage === "calibration"
        const hasWebsiteProposal =
          meta?.type === "website_proposal" && meta?.websiteProposal != null
        const hasCandidateProfile =
          meta?.type === CANDIDATE_PROFILE_CARD_TYPE && meta?.candidate != null
        const hasCandidateEvaluation =
          meta?.type === CANDIDATE_EVALUATION_CARD_TYPE && meta?.evaluation != null
        const hasProactiveHints =
          meta?.type === PROACTIVE_HINTS_MESSAGE_TYPE &&
          Array.isArray(meta?.proactiveHints)

        return (
          <div
            key={message.id}
            data-testid={message.id === WIZARD_PLAN_MESSAGE_ID ? "wizard-plan-card" : undefined}
            className={cn(
              "group",
              isLia ? "" : "flex justify-end"
            )}
          >
            {isLia ? (
              /* LIA message — Notion style: plain text, no bubble bg, left-aligned */
              <div className="max-w-[90%]">
                {weeklyDigestMeta ? (
                  <WeeklyDigestChatMessage
                    digest={meta!.digest as WeeklyDigestData}
                    recruiterName={meta!.recruiterName as string | undefined}
                  />
                ) : (
                  <>
                    {/* Reasoning record ABOVE the answer (Replit/Manus-style):
                        a fixed, expandable trail of what LIA did, so the turn
                        reads reasoning-first / answer-after. Suppressed for the
                        newest turn while the live timeline still owns the
                        hand-off (onFinished), to avoid duplicating it. */}
                    {Array.isArray(
                      (meta as Record<string, unknown> | undefined)?.agent_activity,
                    ) &&
                      ((meta as Record<string, unknown>).agent_activity as unknown[])
                        .length > 0 &&
                      !(message.id === _newestLiaId && liveActive && message.id !== _heldBaselineRef.current) && (
                        <div className="mb-2">
                          <AgentActivitySummary
                            items={
                              (meta as Record<string, unknown>).agent_activity as never
                            }
                          />
                        </div>
                      )}

                    {/* Answer — held while the newest turn's live reasoning is
                        still showing, so the text types out AFTER it settles
                        instead of competing with the reasoning card. */}
                    {!(message.id === _newestLiaId && liveActive && message.id !== _heldBaselineRef.current) && (
                      <div
                        className="text-[13px] leading-relaxed text-lia-text-primary lia-markdown-content"
                        dangerouslySetInnerHTML={{
                          __html: renderMarkdown(
                            message.id === _newestLiaId
                              ? _newestLiaDisplayed
                              : message.content,
                          ),
                        }}
                      />
                    )}
                  </>
                )}

                {/* Execution plan */}
                {hasPlan && (
                  <PlanProgressCard
                    plan={message.executionPlan as unknown as ExecutionPlanData}
                  />
                )}

                {/* Flow steps (workflow visual) */}
                {hasFlowSteps && (
                  <FlowStepMessage
                    steps={meta!.flowSteps as unknown as import("@/components/unified-chat/FlowStepMessage").FlowStep[]}
                    question={meta!.flowQuestion as string | undefined}
                    compact
                  />
                )}

                {/* Navigation hint (e.g., "Go to Agent Studio") */}
                {hasNavHint && (
                  <NavigationHintCard
                    hint={meta!.navigation_hint as { page: string; entity_id?: string }}
                  />
                )}

                {/* Proactive suggestion cards (WT-2022) — scheduler-driven
                    hints surfaced conversationally, replacing the retired
                    ProactiveHintsBadge dropdown. */}
                {hasProactiveHints && (
                  <ProactiveSuggestionCard
                    hints={meta!.proactiveHints as ProactiveHint[]}
                  />
                )}

                {message.response_blocks && message.response_blocks.length > 0 && (
                  <ResponseBlockRenderer blocks={message.response_blocks} mode={mode} />
                )}

                {hasTastingInsights && (
                  <TastingInsightCard
                    insights={meta!.tasting_insights as { module_name: string; module_label: string; insight_type: string; summary: string; cta: string; badge: string }[]}
                  />
                )}

                {/* Clarification option chips (Tier 8 fallback from cascaded_router) */}
                {message.options && message.options.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {message.options.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => onChipClick?.(opt.value)}
                        className="px-3 py-1 text-[12px] rounded-md border border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover transition-colors"
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                {/* Outreach card — inline multi-channel approval before sending */}
                {hasOutreach && (
                  <OutreachCard data={meta!.outreach as import("./OutreachCard").OutreachData} />
                )}

                {/* Pipeline template picker — Onda 28/E.8. Surfaced when
                    backend recommends a preset; click forwards a chat
                    reply to LIA so the recruiter's pick re-uses the same
                    NLU path as a typed answer. */}
                {hasTemplateCard && (
                  <WizardPipelineTemplateCard
                    data={meta!.templateCard as PipelineTemplateCardData}
                    onSelect={(option) => {
                      const cb = meta!.onSelectTemplate as
                        | ((opt: PipelineTemplateOption) => void)
                        | undefined
                      cb?.(option)
                    }}
                  />
                )}

                {/* Website proposal — Task #1180. Card de proposta extraído
                    do site institucional, com edição inline e botões de
                    Salvar tudo/Salvar selecionados/Cancelar que disparam os
                    saves REST diretamente. */}
                {hasWebsiteProposal && (
                  <WebsiteProposalCard
                    data={meta!.websiteProposal as import("@/components/unified-chat/WebsiteProposalCard").WebsiteProposalCardData}
                  />
                )}

                {/* JD enrichment card — rendered when wizard stage jd_enrichment
                    emits ws_stage_payload; shows quality score + expandable details. */}
                {hasWizardJdCard && (
                  <WizardJdCard
                    data={meta!.wizardStageData as Record<string, unknown>}
                  />
                )}

                {/* WSI questions card — rendered when wizard stage wsi_questions
                    emits ws_stage_payload; collapsible list with type badges. */}
                {hasWizardWsiCard && (
                  <WizardWsiCard
                    data={meta!.wizardStageData as Record<string, unknown>}
                  />
                )}

                {/* Calibration card — rendered when wizard stage calibration
                    emits ws_stage_payload; approve/reject/skip inline with
                    approve count progress. Serves as primary interaction when
                    in sidebar/floating mode; secondary checkpoint in fullscreen. */}
                {hasWizardCalibrationCard && (
                  <WizardCalibrationCard
                    data={meta!.wizardStageData as Record<string, unknown>}
                  />
                )}

                {/* Closing card — "Vaga publicada" injected when the wizard
                    reaches done/handoff so the conclusion isn't silent. */}
                {hasPublishedJob && (
                  <WizardPublishedJobCard
                    data={meta!.publishedJob as WizardPublishedJobCardData}
                  />
                )}

                {/* Candidate profile card — surfaced when LIA brings a
                    candidate into focus. Backend-driven (meta.type), same
                    pattern as outreach/website_proposal. Optional shortcuts
                    only render when the surface wires `onCandidateAction`. */}
                {hasCandidateProfile && (
                  <CandidateProfileCard
                    raw={meta!.candidate}
                    onAction={
                      meta!.onCandidateAction as
                        | ((action: CandidateProfileActionId, data: CandidateProfileCardData) => void)
                        | undefined
                    }
                  />
                )}

                {/* Candidate evaluation card — BARS / CV-screening result
                    consuming the canonical `_build_screening_result` schema.
                    Shows the "não salva" seal for non-persisted dry-runs. */}
                {hasCandidateEvaluation && (
                  <CandidateEvaluationCard
                    raw={meta!.evaluation}
                    onViewReport={
                      meta!.onViewEvaluationReport as
                        | ((data: CandidateEvaluationCardData) => void)
                        | undefined
                    }
                  />
                )}

                {/* Notion-style action icons */}
                <MessageActions
                  messageId={message.id}
                  content={message.content}
                  conversationId={conversationId}
                  initialThumbs={message.thumbs ?? null}
                  onRegenerate={onRegenerate}
                />
              </div>
            ) : (
              /* User message — Notion style: dark pill, right-aligned */
              <div className="max-w-[80%]">
                <div className="inline-block px-4 py-2.5 rounded-md bg-lia-bg-inverse dark:bg-lia-bg-tertiary text-white dark:text-lia-text-primary">
                  <p className="text-[13px]">
                    {message.content}
                  </p>
                </div>
              </div>
            )}
          </div>
        )
      })}

      {/* Streaming indicator */}
      {/* Live task feed (Manus) — timeline única e contínua que morfa: pensa →
          revela passos um-a-um (cadência adaptativa) → frame terminal
          "✓ N ações" → conclui e cede ao AgentActivitySummary persistente.
          `completed` dispara o encerramento gracioso (sem corte brusco);
          `onFinished` desmonta a timeline só depois do hand-off. */}
      {liveActive && (
        <div className="group">
          <AgentActivityTimeline
            fallbackSteps={thinkingSteps}
            showFallback={isThinking && !streamingContent}
            completed={!isThinking && !isStreaming}
            onFinished={() => setLiveActive(false)}
          />
        </div>
      )}

      {isStreaming && streamingContent && (
        <div className="group">
          <div className="max-w-[90%]">
            <div
              className="text-[13px] leading-relaxed text-lia-text-primary lia-markdown-content"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(streamingContent),
              }}
            />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
      </div>
    </div>
  )
}
