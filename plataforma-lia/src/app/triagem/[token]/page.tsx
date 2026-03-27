"use client"

import React, { useEffect, useRef, useCallback, useState } from "react"
import { useParams } from "next/navigation"
import { useTriagemChat } from "@/hooks/use-triagem-chat"
import { ChatContainer } from "@/components/triagem/ChatContainer"
import { MessageBubble } from "@/components/triagem/MessageBubble"
import { InputBar } from "@/components/triagem/InputBar"
import { ProgressBar } from "@/components/triagem/ProgressBar"
import { WelcomeCard } from "@/components/triagem/WelcomeCard"
import { CompletionCard } from "@/components/triagem/CompletionCard"
import { ConfirmationCard } from "@/components/triagem/ConfirmationCard"
import { TypingIndicator } from "@/components/triagem/TypingIndicator"
import { MultipleChoiceCard } from "@/components/triagem/MultipleChoiceCard"
import { LikertScaleCard } from "@/components/triagem/LikertScaleCard"
import type { TriagemMessage } from "@/components/triagem/types"
import { AlertTriangle, Clock, Link2Off, ShieldAlert, ServerCrash } from "lucide-react"

function LoadingSkeleton() {
  return (
    <ChatContainer>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md space-y-4 animate-pulse">
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-md w-2/3 mx-auto" />
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-md w-1/2 mx-auto" />
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-md" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-md" />
        </div>
      </div>
    </ChatContainer>
  )
}

function ErrorCard({ code, message }: { code: string; message: string }) {
  const iconMap: Record<string, React.ReactNode> = {
    TOKEN_INVALID: <Link2Off className="w-8 h-8 text-gray-400 dark:text-gray-500" />,
    TOKEN_EXPIRED: <Clock className="w-8 h-8 text-gray-400 dark:text-gray-500" />,
    SESSION_COMPLETED: <ShieldAlert className="w-8 h-8 text-gray-400 dark:text-gray-500" />,
    RATE_LIMITED: <AlertTriangle className="w-8 h-8 text-yellow-500" />,
    SERVER_ERROR: <ServerCrash className="w-8 h-8 text-red-400" />,
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
        <div className="w-full max-w-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm p-6 text-center space-y-4">
          <div className="flex justify-center">{iconMap[code] || iconMap.SERVER_ERROR}</div>
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]">
            {titleMap[code] || "Erro"}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif]">
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
}: {
  message: TriagemMessage
  candidateName: string
  onMultipleChoiceSelect: (optionId: string, optionLabel: string) => void
  onLikertSelect: (value: number) => void
  disabled: boolean
  autoPlayAudio?: boolean
}) {
  if (message.type === "multiple_choice" && message.role === "lia" && message.options) {
    return (
      <div key={message.id}>
        <MessageBubble message={message} candidateName={candidateName} autoPlayAudio={autoPlayAudio} />
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
        <MessageBubble message={message} candidateName={candidateName} autoPlayAudio={autoPlayAudio} />
        <LikertScaleCard
          question=""
          labels={message.likertLabels}
          onSelect={onLikertSelect}
          disabled={disabled}
        />
      </div>
    )
  }

  return <MessageBubble key={message.id} message={message} candidateName={candidateName} autoPlayAudio={autoPlayAudio} />
}

export default function TriagemPage() {
  const params = useParams()
  const token = params.token as string

  const {
    pageState,
    session,
    config,
    messages,
    progress,
    error,
    completionSummary,
    isLiaTyping,
    isSending,
    initSession,
    startChat,
    sendMessage,
    completeSession,
    reviewSession,
  } = useTriagemChat(token)

  const [isVoiceMode, setIsVoiceMode] = useState(false)
  const [isMuted, setIsMuted] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initSession()
  }, [initSession])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLiaTyping])

  const handleStartChat = useCallback(
    (voiceMode?: boolean) => {
      const voice = voiceMode ?? false
      setIsVoiceMode(voice)
      startChat(voice)
    },
    [startChat]
  )

  const handleSendText = useCallback(
    (text: string) => {
      sendMessage({ content: text, type: "text", voiceMode: isVoiceMode })
    },
    [sendMessage, isVoiceMode]
  )

  const handleAudioTranscription = useCallback(
    (text: string) => {
      sendMessage({ content: text, type: "audio", voiceMode: isVoiceMode })
    },
    [sendMessage, isVoiceMode]
  )

  const handleMultipleChoiceSelect = useCallback(
    (optionId: string, optionLabel: string) => {
      sendMessage({ content: optionLabel, type: "multiple_choice", selectedOption: optionId, voiceMode: isVoiceMode })
    },
    [sendMessage, isVoiceMode]
  )

  const handleLikertSelect = useCallback(
    (value: number) => {
      sendMessage({ content: String(value), type: "likert_scale", likertValue: value, voiceMode: isVoiceMode })
    },
    [sendMessage, isVoiceMode]
  )

  const handleToggleMute = useCallback(() => {
    setIsMuted((prev) => !prev)
  }, [])

  const handleEndConversation = useCallback(() => {
    completeSession()
  }, [completeSession])

  const handleClose = useCallback(() => {
    if (typeof window !== "undefined") {
      window.close()
    }
  }, [])

  if (pageState === "loading") {
    return <LoadingSkeleton />
  }

  if (pageState === "error" && error) {
    return <ErrorCard code={error.code} message={error.message} />
  }

  if (pageState === "welcome" && config) {
    return (
      <ChatContainer>
        <WelcomeCard config={config} onStart={handleStartChat} isStarting={isSending} />
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
            autoPlayAudio={isVoiceMode && !isMuted && msg.role === "lia" && idx === messages.length - 1}
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
          voiceMode={isVoiceMode}
          isMuted={isMuted}
          onToggleMute={handleToggleMute}
          onEndConversation={handleEndConversation}
        />
      )}

      <LGPDFooter />
    </ChatContainer>
  )
}

function LGPDFooter() {
  return (
    <div className="py-3 px-4 text-center">
      <p className="text-micro text-gray-400 dark:text-gray-500 font-['Open_Sans',sans-serif]">
        Powered by <span className="text-wedo-cyan font-medium">LIA</span> · WeDOTalent ·{" "}
        <a
          href="/privacidade"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-gray-500 dark:hover:text-gray-400 transition-colors"
          aria-label="Saiba mais sobre avaliação por IA"
        >
          Política de Privacidade
        </a>
      </p>
    </div>
  )
}
