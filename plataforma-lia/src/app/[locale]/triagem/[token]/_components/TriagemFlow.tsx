"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { ChatContainer } from "@/components/triagem/ChatContainer"
import { MessageBubble } from "@/components/triagem/MessageBubble"
import { InputBar } from "@/components/triagem/InputBar"
import { ProgressBar } from "@/components/triagem/ProgressBar"
import { WelcomeCard } from "@/components/triagem/WelcomeCard"
import { PhoneConfirmModal } from "@/components/triagem/PhoneConfirmModal"
import { CompletionCard } from "@/components/triagem/CompletionCard"
import { ConfirmationCard } from "@/components/triagem/ConfirmationCard"
import { TypingIndicator } from "@/components/triagem/TypingIndicator"
import { MultipleChoiceCard } from "@/components/triagem/MultipleChoiceCard"
import { LikertScaleCard } from "@/components/triagem/LikertScaleCard"
import type { TriagemMessage } from "@/components/triagem/types"
import { AlertTriangle, Clock, Link2Off, Phone, ShieldAlert, ServerCrash } from "lucide-react"
import { VoIPCallButton } from "@/components/triagem/VoIPCallButton"
import type { useTriagemSession } from "../_hooks/useTriagemSession"

type TriagemSessionReturn = ReturnType<typeof useTriagemSession>

interface TriagemFlowProps {
  hook: TriagemSessionReturn
}

function LoadingSkeleton() {
  return (
    <ChatContainer>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md space-y-4 animate-pulse motion-reduce:animate-none">
          <div className="h-12 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl w-2/3 mx-auto" />
          <div className="h-6 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl w-1/2 mx-auto" />
          <div className="h-32 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl" />
          <div className="h-10 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl" />
        </div>
      </div>
    </ChatContainer>
  )
}

function ErrorCard({ code, message }: { code: string; message: string }) {
  const t = useTranslations("triagem.errorCard")
  const iconMap: Record<string, React.ReactNode> = {
    TOKEN_INVALID: <Link2Off className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />,
    TOKEN_EXPIRED: <Clock className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />,
    SESSION_COMPLETED: <ShieldAlert className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />,
    RATE_LIMITED: <AlertTriangle className="w-8 h-8 text-status-warning" />,
    SERVER_ERROR: <ServerCrash className="w-8 h-8 text-status-error" />,
  }

  const knownTitleKeys: readonly string[] = ["TOKEN_INVALID", "TOKEN_EXPIRED", "SESSION_COMPLETED", "RATE_LIMITED", "SERVER_ERROR"]
  const titleKey = knownTitleKeys.includes(code) ? `title.${code}` : "title.fallback"

  return (
    <ChatContainer>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-sm p-6 text-center space-y-4">
          <div className="flex justify-center">{iconMap[code] || iconMap.SERVER_ERROR}</div>
          <h2 className="text-base font-semibold text-lia-text-primary dark:text-lia-text-primary">
            {t(titleKey)}
          </h2>
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
            {message}
          </p>
        </div>
      </div>
    </ChatContainer>
  )
}

function MessageRenderer({
  message,
  candidateName,
  onMultipleChoiceSelect,
  onLikertSelect,
  disabled,
  autoPlayAudio,
  ttsToken,
}: {
  message: TriagemMessage
  candidateName: string
  onMultipleChoiceSelect: (optionId: string, optionLabel: string) => void
  onLikertSelect: (value: number) => void
  disabled: boolean
  autoPlayAudio?: boolean
  ttsToken?: string
}) {
  if (message.type === "multiple_choice" && message.role === "lia" && message.options) {
    return (
      <div key={message.id}>
        <MessageBubble message={message} candidateName={candidateName} autoPlayAudio={autoPlayAudio} ttsToken={ttsToken} />
        <MultipleChoiceCard
          question=""
          options={message.options}
          onSelect={onMultipleChoiceSelect}
          disabled={disabled}
        />
      </div>
    )
  }

  if (message.type === "likert_scale" && message.role === "lia" && message.likertLabels) {
    return (
      <div key={message.id}>
        <MessageBubble message={message} candidateName={candidateName} autoPlayAudio={autoPlayAudio} ttsToken={ttsToken} />
        <LikertScaleCard
          question=""
          labels={message.likertLabels}
          onSelect={onLikertSelect}
          disabled={disabled}
        />
      </div>
    )
  }

  return <MessageBubble key={message.id} message={message} candidateName={candidateName} autoPlayAudio={autoPlayAudio} ttsToken={ttsToken} />
}

function LGPDFooter() {
  const t = useTranslations("triagem.lgpdFooter")
  return (
    <div className="py-3 px-4 text-center">
      <p className="text-micro text-lia-text-tertiary dark:text-lia-text-secondary">
        Powered by WeDoTalent ·{" "}
        <a
          href="/privacidade"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-lia-text-primary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
          aria-label={t("privacyPolicyAria")}
        >
          {t("privacyPolicy")}
        </a>
      </p>
    </div>
  )
}

export function TriagemFlow({ hook }: TriagemFlowProps) {
  const tPhoneCall = useTranslations("triagem.phoneCallDone")
  const tMessages = useTranslations("triagem.messagesList")
  const [whatsappModalOpen, setWhatsappModalOpen] = useState(false)
  const {
    token,
    pageState,
    session,
    config,
    messages,
    progress,
    error,
    completionSummary,
    isLiaTyping,
    isSending,
    completeSession,
    reviewSession,
    autoPlayVoice,
    phoneModalOpen,
    setPhoneModalOpen,
    phoneCallLoading,
    phoneCallError,
    phoneCallStatus,
    voipCallActive,
    setVoipCallActive,
    messagesEndRef,
    messagesContainerRef,
    handleStartChat,
    handleSendText,
    handleAudioTranscription,
    handleMultipleChoiceSelect,
    handleLikertSelect,
    handleToggleAutoPlayVoice,
    handleOpenPhoneModal,
    handleRequestCall,
    handleClose,
  } = hook

  if (pageState === "loading") {
    return <LoadingSkeleton />
  }

  if (pageState === "error" && error) {
    return <ErrorCard code={error.code} message={error.message} />
  }

  if (pageState === "welcome" && config) {
    // Task #425: voice-in-browser is now driven strictly by the recruiter's
    // channel config — no more unconditional rendering. WelcomeCard owns the
    // primary "Voz no Navegador" CTA when channel is enabled; we only render
    // the standalone VoIPCallButton as a secondary affordance after the
    // candidate has already requested a phone call (post-call branch).
    const showVoipButton = !!config.voiceWebEnabled

    return (
      <ChatContainer>
        {phoneCallStatus === "done" ? (
          <div className="flex-1 flex items-center justify-center px-4 py-8">
            <div className="w-full max-w-md bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl shadow-lia-sm p-6 text-center space-y-4">
              <div className="flex justify-center">
                <div className="w-12 h-12 rounded-full bg-wedo-cyan/10 flex items-center justify-center">
                  <Phone className="w-6 h-6 text-wedo-cyan" />
                </div>
              </div>
              <h2 className="text-base font-semibold text-lia-text-primary">
                {tPhoneCall("title")}
              </h2>
              <p className="text-sm text-lia-text-secondary leading-relaxed">
                {tPhoneCall("description")}
              </p>
              {showVoipButton && (
                <div className="pt-2">
                  <p className="text-xs text-lia-text-tertiary mb-3">
                    {tPhoneCall("voipPrompt")}
                  </p>
                  <VoIPCallButton
                    token={token}
                    onCallStarted={() => setVoipCallActive(true)}
                    onCallEnded={() => setVoipCallActive(false)}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col">
            <WelcomeCard
              config={config}
              onStart={handleStartChat}
              onRequestCall={handleOpenPhoneModal}
              onRequestWhatsapp={() => setWhatsappModalOpen(true)}
              isStarting={isSending}
            />
          </div>
        )}
        <PhoneConfirmModal
          open={phoneModalOpen}
          onClose={() => setPhoneModalOpen(false)}
          onConfirm={handleRequestCall}
          isLoading={phoneCallLoading}
          error={phoneCallError}
          initialPhone={config?.candidatePhone ?? null}
        />
        <PhoneConfirmModal
          mode="whatsapp"
          open={whatsappModalOpen}
          onClose={() => setWhatsappModalOpen(false)}
          onConfirm={async (e164: string) => {
            try {
              const resp = await fetch(
                `/api/backend-proxy/triagem/${encodeURIComponent(token)}/whatsapp-initiate`,
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ phone_number: e164 }),
                }
              )
              const data = await resp.json().catch(() => ({}))
              // Task #425 — backend returns one of three shapes depending on the
              // recruiter-configured WhatsApp delivery mode:
              //   wa_link      → { success: true, wa_url }
              //   twilio_direct → { success: true, twilio: {...} } (no wa_url)
              //   both         → { success: true, wa_url, twilio: {...} }
              // Treat the response as success whenever HTTP is OK and the
              // payload reports success, even if no wa_url is present.
              if (!resp.ok || data?.success === false) {
                console.error("[Triagem] whatsapp-initiate failed", data)
                return
              }
              if (data?.wa_url) {
                window.open(data.wa_url, "_blank", "noopener,noreferrer")
              }
              setWhatsappModalOpen(false)
            } catch (err) {
              console.error("[Triagem] whatsapp-initiate error", err)
            }
          }}
          initialPhone={config?.candidatePhone ?? null}
        />
        <LGPDFooter />
      </ChatContainer>
    )
  }

  if (pageState === "completion" && completionSummary) {
    return (
      <ChatContainer>
        <CompletionCard
          candidateName={config?.candidateName || session?.candidateName || ""}
          summary={completionSummary}
          onClose={handleClose}
        />
        <LGPDFooter />
      </ChatContainer>
    )
  }

  const isCompleted = pageState === "completion"
  const candidateName = config?.candidateName || session?.candidateName || ""

  return (
    <ChatContainer>
      {progress && <ProgressBar progress={progress} />}

      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
        role="log"
        aria-live="polite"
        aria-label={tMessages("ariaLabel")}
      >
        {messages.map((msg, idx) => (
          <MessageRenderer
            key={msg.id}
            message={msg}
            candidateName={candidateName}
            onMultipleChoiceSelect={handleMultipleChoiceSelect}
            onLikertSelect={handleLikertSelect}
            disabled={isSending || isCompleted}
            autoPlayAudio={autoPlayVoice && msg.role === "lia" && idx === messages.length - 1}
            ttsToken={token}
          />
        ))}

        {isLiaTyping && <TypingIndicator />}

        {pageState === "confirmation" && (
          <ConfirmationCard
            questionsAnswered={progress?.questionsAnswered || 0}
            durationMinutes={
              session?.startedAt
                ? Math.round((Date.now() - new Date(session.startedAt).getTime()) / 60000)
                : 0
            }
            onConfirm={completeSession}
            onReview={reviewSession}
            isSubmitting={isSending}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {(pageState === "chat" || pageState === "confirmation") && !isCompleted && (
        <InputBar
          onSend={handleSendText}
          onAudioTranscription={handleAudioTranscription}
          isSending={isSending}
          disabled={pageState === "confirmation"}
          audioEnabled={config?.audioEnabled ?? true}
          autoPlayVoice={autoPlayVoice}
          onToggleAutoPlayVoice={handleToggleAutoPlayVoice}
          transcriptionUrl={`/api/backend-proxy/triagem/${token}/audio`}
        />
      )}

      <LGPDFooter />
    </ChatContainer>
  )
}
