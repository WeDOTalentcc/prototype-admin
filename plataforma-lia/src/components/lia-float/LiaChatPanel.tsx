"use client"

/**
 * LiaChatPanel — Painel flutuante de conversa com a LIA.
 *
 * Dimensões: 420×580px, fixo bottom-right acima do LiaChatButton.
 *
 * Nível 3 — capacidades:
 *   - WebSocket com streaming de tokens em tempo real
 *   - HITL: card de aprovação para ações reais (mover candidato, agendar, enviar email)
 *   - Roteamento inteligente: detecta intent e abre área especializada
 *   - Wizard: redireciona para Vagas + split-view com o agente
 *   - Markdown: renderização completa (bold, links, listas)
 *
 * Compatível com Vue/Nuxt: sem React-only patterns; lógica em hooks separados.
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { Brain, X, Maximize2, Loader2, Send, ArrowRight, Plus, Eraser, History, Clock, User, Paperclip, FileText, XCircle, CheckCircle2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useActionIntent, actionTypeToDomain, type ActionType } from "@/hooks/use-action-intent"
import { useFloatStreaming } from "@/hooks/use-float-streaming"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { FairnessWarningBanner } from "@/components/fairness-warning-banner"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { MessageFeedback } from "@/components/chat/message-feedback"
import {
  useFloatConversation,
  formatMessageTime,
  type FloatMessage,
} from "@/hooks/use-float-conversation"
import { resolveScopeFromPathname } from "@/hooks/use-current-scope"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { sanitizeHtml } from "@/lib/sanitize"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import { useCvScreening } from "@/hooks/use-cv-screening"

const MAX_INPUT_CHARS = 2000

export function LiaChatPanel() {
  const {
    isOpen, conversationId: ctxConvId, close, expand, openSplitView,
    sharedMessages, addSharedMessage, setSharedMessages,
    sharedConversationId, setSharedConversationId,
  } = useLiaFloat()
  const { result: navIntent, detect: detectIntent, clear: clearIntent } = useNavigationIntent()
  const { detect: detectAction } = useActionIntent()
  const currentScope = resolveScopeFromPathname(typeof window !== 'undefined' ? window.location.pathname : '')
  const [activeActionType, setActiveActionType] = useState<ActionType>(null)
  // CV file attachment state
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

  const handleStreamComplete = useCallback((content: string) => {
    addMessage({
      id: `lia-${Date.now()}`,
      sender: "lia",
      content,
      timestamp: formatMessageTime(),
    })
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

    // CV upload closed-loop: candidate name resolution phase (after user confirms with no candidate_id)
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
      // Treat any non-cancel message as the candidate name — search and update
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
          // Use structured endpoint — candidate_id passed explicitly, not reconstructed from text
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
          // No candidate_id from CV analysis — ask user for name, keep fields
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

    // If a CV file is attached, screen it via HTTP instead of WS
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
      try {
        const raw = localStorage.getItem("lia-recent-items")
        const items = raw
          ? (JSON.parse(raw) as Array<{ id: string; type: string; title: string; timestamp: number }>)
          : []
        setRecentChats(items.filter(i => i.type === "chat").slice(0, 10))
      } catch {
        setRecentChats([])
      }
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
          email: "email",
          phone: "telefone",
          current_title: "cargo atual",
          current_company: "empresa atual",
          location_city: "cidade",
          location_state: "estado",
          linkedin_url: "linkedin",
          education_level: "formação",
          languages: "idiomas",
        }
        const fieldLabels: Record<string, string> = {
          email: "Email",
          phone: "Telefone",
          current_title: "Cargo atual",
          current_company: "Empresa atual",
          location_city: "Cidade",
          location_state: "Estado",
          linkedin_url: "LinkedIn",
          education_level: "Formação",
          languages: "Idiomas",
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

  const canSend = inputText.trim().length > 0 && !isCreating && !isStreaming
  const isEmpty = messages.length === 0 && !isStreaming && !isFetchingHistory

  if (!isOpen) return null

  return (
    <div
      className={cn(
 "fixed bottom-[84px] right-6 z-50" /* [OPT-022] bottom-[84px] px arbitrário — sem canônico Tailwind */,
        "w-[420px] h-[580px]",
        "flex flex-col",
        "bg-lia-bg-primary",
        "border border-lia-border-subtle",
        "rounded-xl shadow-lia-lg overflow-hidden"
      )}
      role="dialog"
      aria-label="Chat LIA"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
          </div>
          <span className="text-base-ui font-bold text-lia-text-primary" >LIA</span>
          {isConnected && (
            <span className="w-1.5 h-1.5 rounded-full bg-status-success flex-shrink-0" title="Conectado" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Novo chat"
            aria-label="Iniciar novo chat"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleClear}
            disabled={messages.length === 0}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none disabled:opacity-30 disabled:cursor-not-allowed"
            title="Limpar mensagens"
            aria-label="Limpar mensagens"
          >
            <Eraser className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleToggleHistory}
            className={cn(
 "p-1.5 rounded-md transition-colors",
              showHistory
                ? "text-chat-cyan bg-lia-bg-tertiary"
                : "text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
            )}
            title="Histórico de conversas"
            aria-label="Ver histórico de conversas"
            aria-expanded={showHistory}
          >
            <History className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-lia-interactive-active mx-0.5" />
          <button
            onClick={handleExpand}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Expandir para chat completo"
            aria-label="Expandir chat"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={close}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Fechar"
            aria-label="Fechar chat"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Action mode banner */}
      {activeActionType && actionLabel && (
        <div className="px-4 py-1.5 bg-lia-bg-secondary border-b border-lia-border-subtle flex items-center justify-between flex-shrink-0">
          <span className="text-xs text-lia-text-tertiary font-medium">
            {actionLabel}
          </span>
          <button
            onClick={() => { setActiveActionType(null); setActionLabel(null) }}
            className="text-xs text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
            aria-label="Sair do modo de ação"
          >
            Sair
          </button>
        </div>
      )}

      {/* WebSocket status banner */}
      {isReconnecting && (
        <div className="px-4 py-1.5 border-b flex-shrink-0 bg-status-warning/10 border-status-warning/30 dark:border-status-warning/30">
          <p className="text-xs text-status-warning">
            {`Reconectando… (tentativa ${reconnectAttempt}/3)`}
          </p>
        </div>
      )}

      {/* History panel */}
      {showHistory && (
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
          <p className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wide mb-2" >
            Conversas recentes
          </p>
          {recentChats.length === 0 ? (
            <p className="text-sm-ui text-lia-text-disabled text-center mt-6">
              Nenhuma conversa anterior encontrada.
            </p>
          ) : (
            recentChats.map(chat => (
              <button
                key={chat.id}
                onClick={() => handleLoadConversation(chat.id)}
                className="w-full flex items-start gap-2.5 px-3 py-2.5 rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none text-left group"
              >
                <Clock className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm-ui text-lia-text-secondary truncate group-hover:text-lia-text-primary dark:group-hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none">
                    {chat.title}
                  </p>
                  <p className="text-xs text-lia-text-disabled mt-0.5">
                    {new Date(chat.timestamp).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {!showHistory && (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
          {isFetchingHistory ? (
            <div className="flex justify-center items-center h-full" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          ) : isEmpty ? (
            <EmptyState />
          ) : (
            <>
              {messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} conversationId={conversationId} />
              ))}

              {hitlPending && (
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
                    </div>
                    <HITLConfirmCard
                      action={hitlPending.action}
                      description={hitlPending.description}
                      onConfirm={() => sendApproval(true)}
                      onCancel={() => sendApproval(false)}
                    />
                  </div>
                </div>
              )}

              {isStreaming && !hitlPending && (
                streamingContent
                  ? <StreamingBubble content={streamingContent} />
                  : <ThinkingIndicator />
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* FAR-2/C: Fairness warning banner */}
      <FairnessWarningBanner
        warnings={fairnessWarnings}
        onDismiss={dismissFairnessWarnings}
      />

      {/* Navigation hint */}
      {navIntent?.page && (
        <div className="px-4 py-2 border-t border-lia-border-subtle flex-shrink-0">
          <button
            onClick={() => {
              if (navIntent.page) {
                openSplitView(navIntent.page, conversationId ?? undefined)
                clearIntent()
              }
            }}
            className="flex items-center gap-2 text-sm-ui text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none group w-full text-left"
            aria-label={`Abrir ${navIntent.page}`}
          >
            <ArrowRight className="w-3.5 h-3.5 flex-shrink-0 text-chat-cyan group-hover:translate-x-0.5 transition-transform motion-reduce:transition-none" />
            <span>{navIntent.hint ?? `Ver em ${navIntent.page}`}</span>
          </button>
        </div>
      )}

      {/* Input */}
      <div className="px-4 pb-4 pt-2 flex-shrink-0 border-t border-lia-border-subtle">
        {/* Attached CV file chip */}
        {attachedCvFile && (
          <div className="flex items-center gap-2 mb-2 px-2 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle">
            <FileText className="w-3.5 h-3.5 text-chat-cyan flex-shrink-0" />
            <span className="text-xs text-lia-text-primary truncate flex-1">{attachedCvFile.name}</span>
            <button
              onClick={() => setAttachedCvFile(null)}
              className="p-0.5 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary"
              aria-label="Remover arquivo"
            >
              <XCircle className="w-3 h-3" />
            </button>
          </div>
        )}
        <div className="flex items-center gap-2 px-3 py-2 rounded-[24px] bg-lia-bg-primary border border-lia-border-subtle">
          <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => {
              if (e.target.value.length <= MAX_INPUT_CHARS) setInputText(e.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder={hitlPending ? "Confirme ou cancele a ação acima..." : "Envie mensagem para a LIA..."}
            disabled={isCreating || isStreaming || !!hitlPending}
            maxLength={MAX_INPUT_CHARS}
            aria-label="Mensagem para a LIA"
            className="flex-1 text-base-ui bg-transparent focus:outline-none text-lia-text-primary placeholder:text-lia-text-disabled disabled:opacity-50 min-w-0"
           
          />
          {/* Hidden file input for CV upload */}
          <input
            ref={cvFileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.xls,.xlsx"
            onChange={handleCvFileAttach}
            className="hidden"
            aria-hidden="true"
          />
          {/* CV file attach button */}
          <button
            type="button"
            onClick={handleCvFileButtonClick}
            disabled={isCreating || isStreaming || isScreening || !!hitlPending}
            title="Anexar CV (PDF, DOCX, XLS — máx 10MB)"
            aria-label="Anexar currículo"
            className={cn(
              "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors motion-reduce:transition-none",
              isScreening
                ? "text-chat-cyan animate-pulse"
                : "text-lia-text-disabled hover:text-lia-text-secondary disabled:opacity-40"
            )}
          >
            {isScreening
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <Paperclip className="w-3.5 h-3.5" />
            }
          </button>
          <AudioRecordButton
            onTranscription={(text) => setInputText(prev => prev ? `${prev} ${text}` : text)}
            className="p-1.5"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Enviar mensagem"
            className={cn(
 "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors",
              canSend
                ? "bg-chat-cyan text-white hover:opacity-90"
                : "bg-lia-interactive-active text-lia-text-disabled"
            )}
          >
            {isCreating || isStreaming
              ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-white" />
              : <Send className="w-3.5 h-3.5" />
            }
          </button>
        </div>
        {inputText.length > MAX_INPUT_CHARS * 0.9 && (
          <p className="text-xs text-lia-text-secondary mt-1 text-right">
            {inputText.length}/{MAX_INPUT_CHARS}
          </p>
        )}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
      <div className="w-10 h-10 rounded-full flex items-center justify-center">
        <Brain className="w-5 h-5 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div>
        <p className="text-base-ui font-medium text-lia-text-secondary" >
          Como posso ajudar?
        </p>
        <p className="text-sm-ui text-lia-text-disabled mt-1" aria-live="polite" aria-atomic="true">
          Pergunte sobre vagas, candidatos, relatórios e muito mais.
        </p>
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
        </div>
        <span className="flex gap-1 items-center h-5">
          <ThinkingDots dotClassName="bg-chat-cyan" size="md" />
        </span>
      </div>
    </div>
  )
}

function RichContent({ html, className }: { html: string; className?: string }) {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
    />
  )
}

function StreamingBubble({ content }: { content: string }) {
  const cleaned = useMemo(() => cleanAgentResponse(content), [content])
  const html = useMemo(() => parseChatMarkdown(cleaned), [cleaned])

  return (
    <div className="flex gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
        </div>
        <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-[14px] rounded-bl-[4px] px-3.5 py-2.5 max-w-[340px]">
          <RichContent
            html={html}
            className="text-base-ui text-lia-text-secondary leading-relaxed font-['Open_Sans',sans-serif]"
          />
          <span className="inline-block w-1.5 h-3.5 bg-chat-cyan ml-0.5 animate-pulse motion-reduce:animate-none align-middle" />
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ msg, conversationId }: { msg: FloatMessage; conversationId: string | null }) {
  const isUser = msg.sender === "user"

  const renderedHtml = useMemo(() => {
    if (isUser) return escapeHtml(msg.content).replace(/\n/g, "<br/>")
    const cleaned = cleanAgentResponse(msg.content)
    return parseChatMarkdown(cleaned)
  }, [msg.content, isUser])

  if (isUser) {
    return (
      <div className="flex gap-2.5 justify-end">
        <div className="flex flex-col items-end gap-1 max-w-[340px]">
          <div className="bg-lia-bg-tertiary rounded-[14px] rounded-br-[4px] px-3.5 py-2.5">
            <RichContent
              html={renderedHtml}
              className="text-base-ui text-lia-text-secondary leading-relaxed font-['Open_Sans',sans-serif]"
            />
          </div>
          <span className="text-xs text-lia-text-disabled font-['Inter',sans-serif] tabular-nums px-1">
            {msg.timestamp}
          </span>
        </div>
        <div className="w-7 h-7 rounded-full bg-lia-interactive-active flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-3.5 h-3.5 text-lia-text-tertiary" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
          <span className="text-xs text-lia-text-disabled font-['Inter',sans-serif] tabular-nums">{msg.timestamp}</span>
        </div>
        <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-[14px] rounded-bl-[4px] px-3.5 py-2.5 max-w-[340px]">
          <RichContent
            html={renderedHtml}
            className="text-base-ui text-lia-text-secondary leading-relaxed font-['Open_Sans',sans-serif]"
          />
        </div>
        {conversationId && (
          <MessageFeedback
            sessionId={conversationId}
            messageId={msg.id}
            originalResponse={msg.content}
            className="mt-1 px-1"
          />
        )}
      </div>
    </div>
  )
}
