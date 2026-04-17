"use client"

import React from "react"
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
  const iconMap: Record<string, React.ReactNode> = {
    TOKEN_INVALID: <Link2Off className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />,
    TOKEN_EXPIRED: <Clock className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />,
    SESSION_COMPLETED: <ShieldAlert className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-secondary" />,
    RATE_LIMITED: <AlertTriangle className="w-8 h-8 text-status-warning" />,
    SERVER_ERROR: <ServerCrash className="w-8 h-8 text-status-error" />,
  }

  const titleMap: Record<string, string> = {
    TOKEN_INVALID: "Link inválido",
    TOKEN_EXPIRED: "Link expirado",
    SESSION_COMPLETED: "Triagem já concluída",
    RATE_LIMITED: "Muitas tentativas",
    SERVER_ERROR: "Erro no servidor",
  }

  return (
    <ChatContainer>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-sm p-6 text-center space-y-4">
          <div className="flex justify-center">{iconMap[code] || iconMap.SERVER_ERROR}</div>
          <h2 className="text-base font-semibold text-lia-text-primary dark:text-lia-text-primary">
            {titleMap[code] || "Erro"}
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
  return (
    <div className="py-3 px-4 text-center">
      <p className="text-micro text-lia-text-tertiary dark:text-lia-text-secondary">
        Powered by <span className="text-wedo-cyan font-medium">LIA</span> · WeDOTalent ·{" "}
        <a
          href="/privacidade"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-lia-text-primary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
          aria-label="Saiba mais sobre avaliação por IA"
        >
          Política de Privacidade
        </a>
      </p>
    </div>
  )
}

export function TriagemFlow({ hook }: TriagemFlowProps) {
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
    // channel config — no more unconditional rendering. WelcomeCard handles
    // the in-card "Voz no Navegador" CTA; the dedicated VoIPCallButton block
    // below appears only as the secondary affordance after a phone call has
    // been requested OR alongside the welcome card when explicitly enabled.
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
                Ligação solicitada
              </h2>
              <p className="text-sm text-lia-text-secondary leading-relaxed">
                Você receberá uma ligação da LIA em instantes. Fique atento ao seu telefone.
              </p>
              {showVoipButton && (
                <div className="pt-2">
                  <p className="text-xs text-lia-text-tertiary mb-3">
                    Ou ligue diretamente pelo navegador:
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
              isStarting={isSending}
            />
            {showVoipButton && (
              <div className="px-4 pb-4 flex justify-center">
                <div className="w-full max-w-md">
                  {!voipCallActive && (
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex-1 h-px bg-lia-border-subtle" />
                      <span className="text-xs text-lia-text-tertiary whitespace-nowrap">
                        ou ligue pelo navegador
                      </span>
                      <div className="flex-1 h-px bg-lia-border-subtle" />
                    </div>
                  )}
                  <VoIPCallButton
                    token={token}
                    onCallStarted={() => setVoipCallActive(true)}
                    onCallEnded={() => setVoipCallActive(false)}
                    className="w-full"
                  />
                </div>
              </div>
            )}
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
        aria-label="Mensagens da triagem"
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
