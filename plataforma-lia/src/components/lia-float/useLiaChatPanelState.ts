"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useActionIntent, actionTypeToDomain, type ActionType } from "@/hooks/use-action-intent"
import { useFloatStreaming } from "@/hooks/use-float-streaming"
import {
  useFloatConversation,
  formatMessageTime,
  type FloatMessage,
} from "@/hooks/use-float-conversation"
import { resolveScopeFromPathname } from "@/hooks/use-current-scope"
import { useCvScreening } from "@/hooks/use-cv-screening"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

const MAX_INPUT_CHARS = 2000

export { MAX_INPUT_CHARS }
export type { FloatMessage }

export function useLiaChatPanelState() {
  const {
    isOpen, conversationId: ctxConvId, close, expand, openSplitView,
    sharedMessages, addSharedMessage, setSharedMessages,
    sharedConversationId, setSharedConversationId,
  } = useLiaFloat()
  const { result: navIntent, detect: detectIntent, clear: clearIntent } = useNavigationIntent()
  const { detect: detectAction } = useActionIntent()
  const currentScope = resolveScopeFromPathname(typeof window !== 'undefined' ? window.location.pathname : '')
  const [activeActionType, setActiveActionType] = useState<ActionType>(null)
  const [attachedCvFile, setAttachedCvFile] = useState<File | null>(null)
  const cvFileInputRef = React.useRef<HTMLInputElement>(null)
  const { screenCv, isScreening } = useCvScreening()
  const [actionLabel, setActionLabel] = useState<string | null>(null)

  const {
    conversationId: localConvId,
    isCreating,
    isFetchingHistory,
    initConversation,
    loadHistory,
  } = useFloatConversation(ctxConvId, setSharedMessages)

  const conversationId = sharedConversationId ?? localConvId
  const messages = sharedMessages
  const addMessage = addSharedMessage
  const setMessages = setSharedMessages
  const setConversationId = useCallback((id: string | null) => {
    setSharedConversationId(id)
  }, [setSharedConversationId])

  const [inputText, setInputText] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string; timestamp: number }>>([])
  const [isUploadingFile, setIsUploadingFile] = useState(false)
  const [uploadedFileInfo, setUploadedFileInfo] = useState<{ name: string; fields: Record<string, string>; candidateId?: string } | null>(null)
  const [pendingCvFields, setPendingCvFields] = useState<Record<string, string> | null>(null)
  const [awaitingCandidateName, setAwaitingCandidateName] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const wsSessionId = conversationId ?? "float-pending"

  const handleStreamComplete = useCallback((content: string, executionPlan?: Record<string, unknown>) => {
    const msg: FloatMessage = {
      id: `lia-${Date.now()}`,
      sender: "lia",
      content,
      timestamp: formatMessageTime(),
    }
    if (executionPlan) {
      msg.executionPlan = executionPlan
    }
    addMessage(msg)
  }, [addMessage])

  const {
    isConnected,
    isStreaming,
    isReconnecting,
    reconnectAttempt,
    streamingContent,
    error: wsError,
    hitlPending,
    fairnessWarnings,
    dismissFairnessWarnings,
    sendMessage: wsSend,
    sendApproval,
    connect: wsConnect,
    disconnect: wsDisconnect,
  } = useFloatStreaming(wsSessionId, handleStreamComplete)

  useEffect(() => {
    if (isOpen && conversationId) {
      wsConnect()
    }
    if (!isOpen) {
      wsDisconnect()
    }
  }, [isOpen, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (ctxConvId && ctxConvId !== conversationId) {
      setConversationId(ctxConvId)
      setMessages([])
      setActiveActionType(null)
      setActionLabel(null)
    }
  }, [ctxConvId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isOpen && conversationId) {
      loadHistory(conversationId)
    }
  }, [isOpen, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isStreaming, hitlPending])

  const handleCvFileAttach = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 10 * 1024 * 1024) {
      addMessage({ id: `err-${Date.now()}`, sender: "lia", content: "Arquivo muito grande. Máximo 10MB.", timestamp: formatMessageTime() })
      return
    }
    setAttachedCvFile(file)
    addMessage({
      id: `cv-attach-${Date.now()}`,
      sender: "lia",
      content: `📎 **${file.name}** anexado. Para analisar este CV para uma vaga específica, me diga o título da vaga. Ou envie para análise geral.`,
      timestamp: formatMessageTime(),
    })
    if (e.target) e.target.value = ""
  }, [addMessage])

  const handleCvFileButtonClick = useCallback(() => {
    cvFileInputRef.current?.click()
  }, [])

  const handleExpand = useCallback(() => {
    expand()
  }, [expand])

  const handleNewChat = useCallback(() => {
    wsDisconnect()
    setMessages([])
    setConversationId(null)
    setActiveActionType(null)
    setActionLabel(null)
    clearIntent()
    setShowHistory(false)
  }, [wsDisconnect, setMessages, setConversationId, clearIntent])

  const handleClear = useCallback(() => {
    setMessages([])
    setShowHistory(false)
  }, [setMessages])

  const handleToggleHistory = useCallback(() => {
    if (!showHistory) {
      const items = useUIPreferencesStore.getState().liaRecentItems
      setRecentChats(items.filter(i => i.type === "chat").slice(0, 10))
    }
    setShowHistory(prev => !prev)
  }, [showHistory])

  const handleLoadConversation = useCallback((id: string) => {
    setMessages([])
    setConversationId(id)
    setActiveActionType(null)
    setActionLabel(null)
    setShowHistory(false)
    loadHistory(id)
  }, [setMessages, setConversationId, loadHistory])

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    const maxSizeBytes = 10 * 1024 * 1024

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|txt|xls|xlsx)$/i)) {
      addMessage({
        id: `err-${Date.now()}`,
        sender: "lia",
        content: "Formato de arquivo não suportado. Use PDF, DOC, DOCX, TXT, XLS ou XLSX.",
        timestamp: formatMessageTime(),
      })
      return
    }

    if (file.size > maxSizeBytes) {
      addMessage({
        id: `err-${Date.now()}`,
        sender: "lia",
        content: "Arquivo muito grande. O limite é 10MB.",
        timestamp: formatMessageTime(),
      })
      return
    }

    setIsUploadingFile(true)

    addMessage({
      id: `user-file-${Date.now()}`,
      sender: "user",
      content: `📎 Arquivo enviado: **${file.name}**`,
      timestamp: formatMessageTime(),
    })

    addMessage({
      id: `lia-analyzing-${Date.now()}`,
      sender: "lia",
      content: `Analisando o arquivo **${file.name}**...`,
      timestamp: formatMessageTime(),
    })

    try {
      const formData = new FormData()
      formData.append("file", file)

      const res = await fetch("/api/backend-proxy/analysis/file", {
        method: "POST",
        body: formData,
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      if (data.success && data.entities) {
        const FIELD_API_KEYS: Record<string, string> = {
          email: "email", phone: "telefone", current_title: "cargo atual",
          current_company: "empresa atual", location_city: "cidade",
          location_state: "estado", linkedin_url: "linkedin",
          education_level: "formação", languages: "idiomas",
        }
        const fieldLabels: Record<string, string> = {
          email: "Email", phone: "Telefone", current_title: "Cargo atual",
          current_company: "Empresa atual", location_city: "Cidade",
          location_state: "Estado", linkedin_url: "LinkedIn",
          education_level: "Formação", languages: "Idiomas",
        }
        const entityMap = data.entities as Record<string, unknown>
        const fields: Record<string, string> = {}
        const fieldApiMap: Record<string, string> = {}

        for (const [key, label] of Object.entries(fieldLabels)) {
          const val = entityMap[key]
          if (val && typeof val === "string" && val.trim()) {
            fields[label] = val.trim()
            fieldApiMap[FIELD_API_KEYS[key]] = val.trim()
          }
        }

        const hasFields = Object.keys(fields).length > 0
        setUploadedFileInfo({ name: file.name, fields, candidateId: data.candidate_id as string | undefined })

        if (hasFields) {
          setPendingCvFields(fieldApiMap)
          const fieldsList = Object.entries(fields)
            .map(([k, v]) => `- **${k}:** ${v}`)
            .join("\n")
          addMessage({
            id: `lia-file-result-${Date.now()}`,
            sender: "lia",
            content: `Encontrei os seguintes dados no arquivo **${file.name}**:\n\n${fieldsList}\n\nDeseja que eu atualize o cadastro do candidato com essas informações? Responda **sim** para confirmar ou **não** para cancelar.`,
            timestamp: formatMessageTime(),
          })
        } else {
          addMessage({
            id: `lia-file-result-${Date.now()}`,
            sender: "lia",
            content: `Analisei o arquivo **${file.name}** mas não encontrei dados estruturados de CV.${data.summary ? ` Resumo: ${data.summary}` : ""}`,
            timestamp: formatMessageTime(),
          })
        }
      } else {
        addMessage({
          id: `lia-file-err-${Date.now()}`,
          sender: "lia",
          content: `Não consegui extrair dados do arquivo **${file.name}**. ${data.error ?? ""}`.trim(),
          timestamp: formatMessageTime(),
        })
      }
    } catch (err) {
      addMessage({
        id: `lia-file-err-${Date.now()}`,
        sender: "lia",
        content: "Erro ao processar o arquivo. Verifique o formato e tente novamente.",
        timestamp: formatMessageTime(),
      })
    } finally {
      setIsUploadingFile(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }, [addMessage])

  const handleChipSend = React.useCallback(async (text: string) => {
    addMessage({
      id: `user-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: formatMessageTime(),
    })
    let convId = conversationId
    if (!convId) {
      convId = await initConversation(text)
      if (!convId) return
      setSharedConversationId(convId)
      wsConnect()
    }
    wsSend(text, "", currentScope)
  }, [conversationId, addMessage, initConversation, setSharedConversationId, wsConnect, wsSend, currentScope])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || isCreating || isStreaming) return
    setInputText("")

    addMessage({
      id: `user-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: formatMessageTime(),
    })

    if (awaitingCandidateName && pendingCvFields && Object.keys(pendingCvFields).length > 0) {
      const normalized = text.toLowerCase().trim()
      const isCancel = /^(não|nao|no|cancelar|cancela|n)/.test(normalized)
      if (isCancel) {
        setAwaitingCandidateName(false)
        setPendingCvFields(null)
        setUploadedFileInfo(null)
        addMessage({
          id: `lia-cv-cancel-${Date.now()}`,
          sender: "lia",
          content: "Ok, atualização cancelada. Como posso te ajudar?",
          timestamp: formatMessageTime(),
        })
        return
      }
      const candidateName = text.trim()
      const fieldsToUpdate = { ...pendingCvFields }
      const updates = Object.entries(fieldsToUpdate)
      setAwaitingCandidateName(false)
      setPendingCvFields(null)
      addMessage({
        id: `lia-cv-name-${Date.now()}`,
        sender: "lia",
        content: `Procurando "${candidateName}" e atualizando ${updates.length} campo(s)...`,
        timestamp: formatMessageTime(),
      })
      try {
        const resp = await fetch("/api/backend-proxy/chat/actions/candidate-field-update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidate_name: candidateName, fields: fieldsToUpdate }),
        })
        const data = await resp.json()
        const count = data.updated_count ?? 0
        addMessage({
          id: `lia-cv-done-${Date.now()}`,
          sender: "lia",
          content: data.success
            ? `${count} campo(s) atualizados para "${candidateName}" com sucesso!`
            : data.error || `Não foi possível encontrar ou atualizar o candidato "${candidateName}".`,
          timestamp: formatMessageTime(),
        })
      } catch {
        addMessage({
          id: `lia-cv-err-${Date.now()}`,
          sender: "lia",
          content: "Não foi possível atualizar os campos. Tente novamente.",
          timestamp: formatMessageTime(),
        })
      }
      return
    }

    if (pendingCvFields && Object.keys(pendingCvFields).length > 0) {
      const normalized = text.toLowerCase().trim()
      const isConfirm = /^(sim|yes|confirma|confirmar|ok|s|yep|claro|pode)/.test(normalized)
      const isReject = /^(não|nao|no|cancelar|cancela|n)/.test(normalized)

      if (isConfirm) {
        const candidateId = uploadedFileInfo?.candidateId
        const fieldsToUpdate = { ...pendingCvFields }

        if (candidateId) {
          setPendingCvFields(null)
          const updates = Object.entries(fieldsToUpdate)
          addMessage({
            id: `lia-cv-confirm-${Date.now()}`,
            sender: "lia",
            content: `Perfeito! Atualizando ${updates.length} campo(s) do candidato...`,
            timestamp: formatMessageTime(),
          })
          try {
            const resp = await fetch("/api/backend-proxy/chat/actions/candidate-field-update", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ candidate_id: candidateId, fields: fieldsToUpdate }),
            })
            const data = await resp.json()
            const count = data.updated_count ?? updates.length
            addMessage({
              id: `lia-cv-done-${Date.now()}`,
              sender: "lia",
              content: data.success
                ? `${count} campo(s) atualizados com sucesso!`
                : `Alguns campos não puderam ser atualizados (${count}/${updates.length}).`,
              timestamp: formatMessageTime(),
            })
          } catch {
            addMessage({
              id: `lia-cv-err-${Date.now()}`,
              sender: "lia",
              content: "Não foi possível atualizar os campos. Tente novamente.",
              timestamp: formatMessageTime(),
            })
          }
        } else {
          setAwaitingCandidateName(true)
          addMessage({
            id: `lia-cv-ask-name-${Date.now()}`,
            sender: "lia",
            content: "Qual candidato devo atualizar? Informe o nome completo (ou 'cancelar' para desistir).",
            timestamp: formatMessageTime(),
          })
        }
        return
      }

      if (isReject) {
        setPendingCvFields(null)
        setUploadedFileInfo(null)
        addMessage({
          id: `lia-cv-cancel-${Date.now()}`,
          sender: "lia",
          content: "Ok, atualização cancelada. Como posso te ajudar?",
          timestamp: formatMessageTime(),
        })
        return
      }
    }

    const actionResult = detectAction(text)

    if (actionResult.actionType === "wizard") {
      openSplitView("Vagas", conversationId ?? undefined)
      return
    }

    if (actionResult.actionType) {
      setActiveActionType(actionResult.actionType)
      setActionLabel(actionResult.label)
    }

    detectIntent(text).catch(() => {})

    let convId = conversationId
    if (!convId) {
      convId = await initConversation(text)
      if (!convId) {
        addMessage({
          id: `err-${Date.now()}`,
          sender: "lia",
          content: "Não consegui iniciar a conversa. Tente novamente.",
          timestamp: formatMessageTime(),
        })
        return
      }
      setSharedConversationId(convId)
      wsConnect()
    }

    if (attachedCvFile) {
      const vacancyHint = text.length > 3 ? text : undefined
      addMessage({ id: `user-cv-${Date.now()}`, sender: "user", content: text || "Analisar CV", timestamp: formatMessageTime() })
      addMessage({ id: `thinking-cv-${Date.now()}`, sender: "lia", content: "⏳ Analisando CV com IA...", timestamp: formatMessageTime() })
      const cvFile = attachedCvFile
      setAttachedCvFile(null)
      setInputText("")

      screenCv({
        file: cvFile,
        vacancyTitle: vacancyHint,
        runBars: true,
        onProgress: () => {},
      }).then(result => {
        addMessage({
          id: `cv-result-${Date.now()}`,
          sender: "lia",
          content: result.message,
          timestamp: formatMessageTime(),
        })
      }).catch(() => {
        addMessage({ id: `cv-err-${Date.now()}`, sender: "lia", content: "❌ Erro ao analisar CV. Tente novamente.", timestamp: formatMessageTime() })
      })
      return
    }

    const domain = actionResult.actionType ? actionTypeToDomain(actionResult.actionType) : ""
    wsSend(text, domain, currentScope)

  }, [
    inputText, conversationId, isCreating, isStreaming,
    addMessage, initConversation, detectAction, detectIntent,
    openSplitView, wsSend, wsConnect, setSharedConversationId, currentScope,
    pendingCvFields, uploadedFileInfo, setPendingCvFields, setUploadedFileInfo,
  ])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const canSend = inputText.trim().length > 0 && !isCreating && !isStreaming
  const isEmpty = messages.length === 0 && !isStreaming && !isFetchingHistory

  return {
    isOpen, close, expand, openSplitView, conversationId, messages, addMessage,
    setMessages, setConversationId, setSharedConversationId,
    navIntent, detectIntent, clearIntent, detectAction, currentScope,
    activeActionType, setActiveActionType, actionLabel, setActionLabel,
    attachedCvFile, setAttachedCvFile, cvFileInputRef, screenCv, isScreening,
    isCreating, isFetchingHistory, initConversation,
    inputText, setInputText, showHistory, recentChats,
    isUploadingFile, uploadedFileInfo, setUploadedFileInfo,
    pendingCvFields, setPendingCvFields,
    awaitingCandidateName, setAwaitingCandidateName,
    messagesEndRef, inputRef, fileInputRef,
    isConnected, isStreaming, isReconnecting, reconnectAttempt,
    streamingContent, wsError, hitlPending, fairnessWarnings,
    dismissFairnessWarnings, wsSend, sendApproval, wsConnect, wsDisconnect,
    handleCvFileAttach, handleCvFileButtonClick, handleExpand,
    handleNewChat, handleClear, handleToggleHistory, handleLoadConversation,
    handleFileUpload, handleChipSend, handleSend, handleKeyDown,
    canSend, isEmpty, MAX_INPUT_CHARS,
  }
}
