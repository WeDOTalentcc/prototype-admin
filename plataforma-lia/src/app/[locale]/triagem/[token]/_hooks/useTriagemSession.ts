"use client"

import { useEffect, useRef, useCallback, useState } from "react"
import { useParams } from "next/navigation"
import { useTriagemChat } from "@/hooks/chat/use-triagem-chat"

const VOICE_AUTOPLAY_KEY = "lia-triagem-voice-autoplay"

export function useTriagemSession() {
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

  const [autoPlayVoice, setAutoPlayVoice] = useState(() => {
    if (typeof window === "undefined") return false
    try {
      return localStorage.getItem(VOICE_AUTOPLAY_KEY) === "true"
    } catch {
      return false
    }
  })

  const [phoneModalOpen, setPhoneModalOpen] = useState(false)
  const [phoneCallLoading, setPhoneCallLoading] = useState(false)
  const [phoneCallError, setPhoneCallError] = useState<string | null>(null)
  const [phoneCallStatus, setPhoneCallStatus] = useState<"idle" | "done">("idle")
  const [voipCallActive, setVoipCallActive] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initSession()
  }, [initSession])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLiaTyping])

  const handleStartChat = useCallback(
    // Task #425 — when the candidate clicks "Voz no Navegador" inside WelcomeCard,
    // WelcomeCard calls onStart(true). Honor that explicit voiceMode argument so
    // the voice-web channel actually starts in voice mode regardless of the
    // autoPlayVoice toggle. Falls back to autoPlayVoice for the chat CTA.
    (voiceMode?: boolean) => {
      const effective = typeof voiceMode === "boolean" ? voiceMode : autoPlayVoice
      startChat(effective)
    },
    [startChat, autoPlayVoice]
  )

  const handleSendText = useCallback(
    (text: string) => {
      sendMessage({ content: text, type: "text", voiceMode: autoPlayVoice })
    },
    [sendMessage, autoPlayVoice]
  )

  const handleAudioTranscription = useCallback(
    (text: string) => {
      sendMessage({ content: text, type: "audio", voiceMode: autoPlayVoice })
    },
    [sendMessage, autoPlayVoice]
  )

  const handleMultipleChoiceSelect = useCallback(
    (optionId: string, optionLabel: string) => {
      sendMessage({ content: optionLabel, type: "multiple_choice", selectedOption: optionId, voiceMode: autoPlayVoice })
    },
    [sendMessage, autoPlayVoice]
  )

  const handleLikertSelect = useCallback(
    (value: number) => {
      sendMessage({ content: String(value), type: "likert_scale", likertValue: value, voiceMode: autoPlayVoice })
    },
    [sendMessage, autoPlayVoice]
  )

  const handleToggleAutoPlayVoice = useCallback(() => {
    setAutoPlayVoice((prev) => {
      const next = !prev
      try {
        localStorage.setItem(VOICE_AUTOPLAY_KEY, String(next))
      } catch {}
      return next
    })
  }, [])

  const handleOpenPhoneModal = useCallback(() => {
    setPhoneCallError(null)
    setPhoneModalOpen(true)
  }, [])

  const handleRequestCall = useCallback(
    async (phone: string) => {
      setPhoneCallLoading(true)
      setPhoneCallError(null)
      try {
        const res = await fetch(`/api/backend-proxy/triagem/${token}/request-call`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidate_phone: phone }),
        })
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.detail || "Falha ao solicitar ligação")
        }
        setPhoneCallStatus("done")
        setPhoneModalOpen(false)
      } catch (err: unknown) {
        setPhoneCallError(err instanceof Error ? err.message : "Erro ao solicitar ligação")
      } finally {
        setPhoneCallLoading(false)
      }
    },
    [token]
  )

  const handleClose = useCallback(() => {
    if (typeof window !== "undefined") {
      window.close()
    }
  }, [])

  return {
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
  }
}
