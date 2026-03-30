"use client"

import React, { useState, useRef } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { LiaVacancyQueriesGuide } from "@/components/ui/lia-vacancy-queries-guide"
import { textStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import {
  Brain,
  Maximize2,
  X,
  Briefcase,
  FileText,
  Target,
  Plus,
  Send,
  Paperclip,
  Search,
  Copy,
  Loader2,
} from "lucide-react"

const ExpandedChatModal = dynamic(
  () => import("@/components/expanded-chat-modal").then((m) => ({ default: m.ExpandedChatModal })),
  { ssr: false },
)

interface LiaInlineMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  isTyping?: boolean
}

interface InlineChatPanelProps {
  showExpandedLIA: boolean
  showInlineChat: boolean
  chatMode: "general" | "job-creation" | null
  inlineChatInitialMessage?: string
  liaInlineMessages: LiaInlineMessage[]
  liaInlineLoading: boolean
  isChatFullscreen: boolean
  liaWidth: number
  isTableCollapsed: boolean
  isResizingLIA: boolean
  userCollapsedLIA: boolean
  selectedJobsForBatch: Set<number>

  liaPromptValue: string
  onSetLiaPromptValue: (value: string | ((prev: string) => string)) => void

  onCloseChat: () => void
  onOpenGeneralChat: (message?: string) => void
  onOpenJobCreationChat: (message?: string) => void
  onReturnToGeneralChat: () => void
  onReturnToLateralPrompt: (messages?: Array<{ id: string; role: "user" | "assistant"; content: string; timestamp: Date }>) => void
  onSendMessage: (content: string) => Promise<void>
  onSetShowExpandedLIA: (show: boolean) => void
  onSetUserCollapsedLIA: (collapsed: boolean) => void
  onSetIsChatFullscreen: (fullscreen: boolean) => void
  onSetIsResizingLIA: (resizing: boolean) => void
  onSetLiaWidth: (width: number) => void
  onSetLiaInlineMessages: (msgs: LiaInlineMessage[]) => void

  liaInlineMessagesEndRef: React.RefObject<HTMLDivElement>

  onAddRecentItem?: (item: {
    id: string
    type: "vaga" | "chat" | "candidato"
    title: string
    subtitle?: string
    meta?: Record<string, string | undefined>
  }) => void
}

export function InlineChatPanel({
  showExpandedLIA,
  showInlineChat,
  chatMode,
  inlineChatInitialMessage,
  liaInlineMessages,
  liaInlineLoading,
  isChatFullscreen,
  liaWidth,
  isTableCollapsed,
  isResizingLIA,
  userCollapsedLIA,
  selectedJobsForBatch,
  liaPromptValue,
  onSetLiaPromptValue,
  onCloseChat,
  onOpenGeneralChat,
  onOpenJobCreationChat,
  onReturnToGeneralChat,
  onReturnToLateralPrompt,
  onSendMessage,
  onSetShowExpandedLIA,
  onSetUserCollapsedLIA,
  onSetIsChatFullscreen,
  onSetIsResizingLIA,
  onSetLiaWidth,
  onSetLiaInlineMessages,
  liaInlineMessagesEndRef,
  onAddRecentItem,
}: InlineChatPanelProps) {
  if (!showExpandedLIA && !showInlineChat) return null

  // Internal state — only used within this panel
  const [activeSearchTab, setActiveSearchTab] = useState<"ia-natural" | "job-description" | "templates">("ia-natural")
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [isUploadingJD, setIsUploadingJD] = useState(false)
  const [jdUploadError, setJdUploadError] = useState<string | null>(null)
  const jdFileInputRef = useRef<HTMLInputElement>(null)

  const handleJDFileUpload = async (file: File) => {
    setIsUploadingJD(true)
    setJdUploadError(null)
    try {
      const formData = new FormData()
      formData.append("file", file)
      const titleParam = file.name.replace(/\.[^/.]+$/, "")
      const res = await fetch(
        `/api/backend-proxy/jd-import/upload?title=${encodeURIComponent(titleParam)}`,
        { method: "POST", body: formData },
      )
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({})) as { error?: string }
        setJdUploadError(errorData.error || "Falha ao processar arquivo")
        return
      }
      const data = await res.json()
      const text = data.description || data.responsibilities_text || ""
      if (text) setJobDescriptionText(text)
    } catch {
      setJdUploadError("Erro de conexão ao processar arquivo")
    } finally {
      setIsUploadingJD(false)
    }
  }

  return (
    <div
      className={`transition-colors duration-300 relative group h-full ${
        isTableCollapsed || (chatMode === "job-creation" && isChatFullscreen) ? "flex-1" : "flex-shrink-0"
      }`}
      style={{width:
          isTableCollapsed || (chatMode === "job-creation" && isChatFullscreen)
            ? "auto"
            : chatMode === "job-creation"
              ? "60%"
              : `${liaWidth}px`,
        maxWidth:
          isTableCollapsed || (chatMode === "job-creation" && isChatFullscreen)
            ? "none"
            : chatMode === "job-creation"
              ? "900px"
              : `${liaWidth}px`,
        transition: "all 0.3s ease-in-out"}}
    >
      {/* MODO CRIAÇÃO DE VAGA - Super Chat com Critérios */}
      {chatMode === "job-creation" && showInlineChat ? (
        <div className="h-full flex flex-col">
          <ExpandedChatModal
            isOpen={true}
            onClose={onCloseChat}
            initialMessage={inlineChatInitialMessage}
            initialMessages={liaInlineMessages}
            contextTitle="Criação de Vaga"
            inline={true}
            mode="job-creation"
            onJobCreated={() => {
              onReturnToGeneralChat()
            }}
            onReturnToLateral={onReturnToLateralPrompt}
            onFullscreenChange={onSetIsChatFullscreen}
            onMessagesUpdate={(msgs) => onSetLiaInlineMessages(msgs)}
          />
        </div>
      ) : showInlineChat && chatMode === "general" ? (
        /* MODO CHAT GERAL EXPANDIDO - Substitui o super chat quando volta da criação */
        <div className="h-full flex flex-col">
          <ExpandedChatModal
            isOpen={true}
            onClose={onCloseChat}
            initialMessage={inlineChatInitialMessage}
            initialMessages={liaInlineMessages}
            contextTitle="Chat LIA"
            inline={true}
            mode="general"
            onReturnToLateral={onReturnToLateralPrompt}
            onMessagesUpdate={(msgs) => onSetLiaInlineMessages(msgs)}
          />
        </div>
      ) : (
        /* MODO GERAL - Prompt Expandido Original */
        <Card
          className="h-full flex flex-col overflow-hidden border border-lia-border-default bg-gray-50 dark:bg-lia-bg-secondary"
          style={{maxHeight: "calc(100vh - 180px)"}}
        >
          {/* Mensagem de Apresentação da LIA */}
          <div className="flex-shrink-0 px-4 py-3 bg-gray-50 dark:bg-lia-bg-secondary">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div
                  className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 bg-gray-50 dark:bg-lia-bg-secondary"
                >
                  <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-semibold leading-tight truncate text-gray-950 dark:text-gray-50">
                    Olá! Sou a Lia.
                  </h3>
                  <p className="text-xs leading-tight truncate mt-0.5 text-gray-500">
                    Como posso te ajudar hoje?
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onOpenGeneralChat("")}
                  title="Expandir chat"
                  className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                >
                  <Maximize2 className="w-4 h-4 text-gray-500" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    onSetShowExpandedLIA(false)
                    onSetUserCollapsedLIA(true)
                  }}
                  title="Fechar"
                  className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </Button>
              </div>
            </div>
          </div>

          {/* Indicador de vagas selecionadas - mensagem compacta */}
          {selectedJobsForBatch.size > 0 && (
            <div className="flex-shrink-0 px-4 py-2">
              <div className="px-3 py-2 bg-gray-100 rounded-md border border-lia-border-subtle flex items-center gap-2">
                <Briefcase className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                <span className="text-xs text-gray-600 font-medium">
                  {selectedJobsForBatch.size} vaga{selectedJobsForBatch.size > 1 ? "s" : ""} selecionada
                  {selectedJobsForBatch.size > 1 ? "s" : ""}
                </span>
              </div>
            </div>
          )}

          {/* Área de Mensagens do Chat Inline - Só aparece quando há mensagens */}
          {liaInlineMessages.length > 0 ? (
            <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
              {liaInlineMessages.map((message) => (
                <div
                  key={message.id}
                  className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}
                >
                  {message.role === "user" ? (
                    <div className="flex items-start gap-2 max-w-[90%]">
                      <img
                        src="https://randomuser.me/api/portraits/men/32.jpg"
                        alt="Você"
                        className="w-6 h-6 rounded-full object-cover flex-shrink-0"
                      />
                      <div className="px-2.5 py-2 rounded-md bg-gray-100 dark:bg-lia-bg-elevated">
                        <p className="text-xs text-gray-800 leading-relaxed">{message.content}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-[90%] group">
                      <div className="flex items-start gap-2">
                        <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0">
                          <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                        </div>
                        <div className="pt-0.5 flex-1">
                          <div className="flex items-center gap-1 mb-0.5">
                            <span
                              className="text-micro font-medium text-gray-800"
                            >
                              LIA
                            </span>
                          </div>
                          <div className="text-xs text-gray-800 space-y-1 leading-relaxed">
                            {message.content.split("\n").map((line, i) => {
                              if (line.startsWith("•")) {
                                return (
                                  <p key={i} className="pl-2">
                                    {line}
                                  </p>
                                )
                              }
                              if (line.match(/^\d+\./)) {
                                return (
                                  <p key={i} className="pl-2">
                                    {line}
                                  </p>
                                )
                              }
                              if (line.includes("**")) {
                                const parts = line.split(/\*\*(.*?)\*\*/g)
                                return (
                                  <p key={i}>
                                    {parts.map((part, j) =>
                                      j % 2 === 1 ? <strong key={j}>{part}</strong> : part,
                                    )}
                                  </p>
                                )
                              }
                              return line ? <p key={i}>{line}</p> : null
                            })}
                          </div>
                          {(message as any).action_executed && (message as any).action_result && (
                            <ActionResultCard
                              actionType={(message as any).action_type || "pause_job"}
                              result={(message as any).action_result}
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {liaInlineLoading && (
                <div className="flex justify-start">
                  <div className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                    <div className="w-5 h-5 rounded-md bg-lia-bg-primary flex items-center justify-center">
                      <Loader2 className="w-3 h-3 animate-spin text-gray-600 dark:text-lia-text-tertiary" />
                    </div>
                    <span className="text-micro text-gray-500">Pensando...</span>
                  </div>
                </div>
              )}

              <div ref={liaInlineMessagesEndRef} />
            </div>
          ) : (
            /* Espaço flexível vazio quando não há mensagens - empurra conteúdo para baixo */
            <div className="flex-1" />
          )}

          {/* Input Area - Fixo na parte inferior */}
          <div className="flex-shrink-0 px-4 pb-4 pt-2">
            {/* Campo de Input */}
            <div className="flex items-center gap-2 p-2 rounded-md border bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle">
              <input
                type="text"
                placeholder="Envie mensagem para a LIA..."
                value={liaPromptValue}
                onChange={(e) => onSetLiaPromptValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && liaPromptValue.trim() && !liaInlineLoading) {
                    onSendMessage(liaPromptValue.trim())
                    onSetLiaPromptValue("")
                  }
                }}
                disabled={liaInlineLoading}
                className="flex-1 text-xs bg-transparent focus:outline-none text-gray-950 dark:text-gray-50 disabled:opacity-50"
              />
              <AudioRecordButton
                onTranscription={(text) => onSetLiaPromptValue((prev) => (prev ? `${prev} ${text}` : text))}
                className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-gray-100 transition-colors"
              />
              <button
                type="button"
                onClick={() => {
                  if (liaPromptValue.trim() && !liaInlineLoading) {
                    onSendMessage(liaPromptValue.trim())
                    onSetLiaPromptValue("")
                  }
                }}
                disabled={!liaPromptValue.trim() || liaInlineLoading}
                className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors disabled:opacity-50 bg-gray-900"
              >
                <Send className="w-3.5 h-3.5 text-white" />
              </button>
            </div>

            {/* Sistema de Abas - Pill Style (movido para baixo do input) */}
            <div className="flex items-center gap-1.5 mt-2">
              <button
                onClick={() => setActiveSearchTab("ia-natural")}
                className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition-[width,height] ${
                  activeSearchTab === "ia-natural"
                    ? "text-white bg-gray-900"
                    : "text-gray-700 hover:dark:text-lia-text-secondary dark:bg-lia-bg-secondary dark:hover:bg-gray-700"
                }`}
              >
                <div className="flex items-center gap-1">
                  <Brain className="w-2.5 h-2.5 text-wedo-cyan" />
                  <span>IA Natural</span>
                </div>
              </button>
              <button
                onClick={() => setActiveSearchTab("job-description")}
                className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition-[width,height] ${
                  activeSearchTab === "job-description"
                    ? "text-white bg-gray-900"
                    : "text-gray-700 hover:dark:text-lia-text-secondary dark:bg-lia-bg-secondary dark:hover:bg-gray-700"
                }`}
              >
                <div className="flex items-center gap-1">
                  <FileText className="w-2.5 h-2.5" />
                  <span>Descrição do Cargo</span>
                </div>
              </button>
              <button
                onClick={() => setActiveSearchTab("templates")}
                className={`flex-shrink-0 px-2.5 py-1 rounded-full text-xs font-medium transition-[width,height] ${
                  activeSearchTab === "templates"
                    ? "text-white bg-gray-900"
                    : "text-gray-700 hover:dark:text-lia-text-secondary dark:bg-lia-bg-secondary dark:hover:bg-gray-700"
                }`}
              >
                <div className="flex items-center gap-1">
                  <Target className="w-2.5 h-2.5" />
                  <span>Templates</span>
                </div>
              </button>
            </div>

            {/* Tags de Ações Rápidas - Abaixo das abas (só visíveis em IA Natural) */}
            {activeSearchTab === "ia-natural" && (
              <div className="flex items-center gap-1.5 mt-1.5">
                <span className="text-micro font-medium text-gray-500">Sugestões:</span>
                <button
                  onClick={() => {
                    onSetShowExpandedLIA(false)
                    onOpenJobCreationChat()
                  }}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-gray-700 bg-gray-100 rounded-full hover:bg-gray-200 transition-[width,height]"
                >
                  <Plus className="w-2.5 h-2.5 text-gray-500" />
                  Criar vaga
                </button>
                <LiaVacancyQueriesGuide
                  onSelectQuery={(query) => {
                    onSendMessage(query)
                  }}
                  className="!px-2 !py-0.5 !text-micro !bg-gray-100 !border-0 hover:!bg-gray-200"
                />
              </div>
            )}
          </div>

          {/* Conteúdo das outras abas */}
          {(activeSearchTab === "job-description" || activeSearchTab === "templates") && (
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50 dark:bg-lia-bg-secondary">
              {/* ABA 2: JOB DESCRIPTION */}
              {activeSearchTab === "job-description" && (
                <div className="space-y-3">
                  {/* Descrição */}
                  <div className="p-2.5 rounded-md" style={{backgroundColor: "var(--gray-50)"}}>
                    <p className="text-xs">
                      Cole ou anexe uma descrição de vaga e eu vou criar a vaga automaticamente para você,
                      configurando todos os detalhes.
                    </p>
                  </div>

                  {/* Textarea */}
                  <div className="relative">
                    <textarea
                      placeholder="Cole aqui o job description completo (requisitos, responsabilidades, benefícios...)..."
                      value={jobDescriptionText}
                      onChange={(e) => setJobDescriptionText(e.target.value)}
                      className="w-full h-28 p-3 pb-10 text-xs rounded-md border focus:outline-none focus:ring-1 focus:ring-gray-900/20 transition-colors resize-none text-gray-950 dark:text-gray-50 border border-lia-border-subtle"
                      style={{backgroundColor: "var(--gray-50)"}}
                    />
                    {/* Botões de Anexo */}
                    <div className="absolute bottom-2 right-2 flex items-center gap-1">
                      <input
                        ref={jdFileInputRef}
                        type="file"
                        accept=".txt,.md,.pdf,.docx"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) handleJDFileUpload(file)
                          e.target.value = ""
                        }}
                      />
                      <button
                        type="button"
                        className="p-1.5 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50"
                        title="Anexar documento (.txt, .md, .pdf, .docx — máx 5MB)"
                        disabled={isUploadingJD}
                        onClick={() => jdFileInputRef.current?.click()}
                      >
                        {isUploadingJD ? (
                          <svg className="w-3.5 h-3.5 text-gray-500 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8v8z"
                            />
                          </svg>
                        ) : (
                          <Paperclip className="w-3.5 h-3.5 text-gray-500" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Erro de upload */}
                  {jdUploadError && (
                    <p className="text-micro text-status-error px-1">{jdUploadError}</p>
                  )}

                  {/* Aviso LGPD */}
                  <p className="text-micro text-gray-400 px-1">
                    O arquivo pode conter dados pessoais. Revise o conteúdo antes de importar. (LGPD)
                  </p>

                  {/* Botão Criar Vaga */}
                  <Button
                    className="w-full h-9 !text-xs font-medium rounded-md"
                    style={{backgroundColor: jobDescriptionText.trim() ? "var(--gray-800)" : "var(--gray-50)",
                      color: jobDescriptionText.trim() ? "var(--white)" : "var(--gray-400)"}}
                    onClick={() => {
                      if (jobDescriptionText.trim()) {
                        onSetShowExpandedLIA(false)
                        onOpenJobCreationChat(jobDescriptionText)
                      }
                    }}
                    disabled={!jobDescriptionText.trim()}
                  >
                    <Brain className="w-3.5 h-3.5 mr-1.5 text-wedo-cyan" />
                    Criar Vaga a Partir da Descrição
                  </Button>
                </div>
              )}

              {/* ABA 3: TEMPLATES DE VAGAS */}
              {activeSearchTab === "templates" && (
                <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-20rem)]">
                  {/* Seção 1: Criar a partir de Template */}
                  <div>
                    <h4 className="text-xs font-medium mb-0.5 text-gray-800">
                      Criar Vaga a Partir de Template
                    </h4>
                    <p className={`${textStyles.caption} mb-2`}>
                      Selecione um modelo pronto e eu inicio a criação da vaga para você
                    </p>

                    {/* Grid de Templates Compacto */}
                    <div className="grid grid-cols-2 gap-1.5">
                      {[
                        { icon: "🚀", title: "Backend Sênior Node.js", tags: ["Backend", "Node.js"] },
                        { icon: "📊", title: "Product Manager", tags: ["Product", "Agile"] },
                        { icon: "🎨", title: "UX/UI Designer", tags: ["Design", "Figma"] },
                        { icon: "☁️", title: "DevOps Engineer", tags: ["Cloud", "CI/CD"] },
                      ].map((template) => (
                        <div
                          key={template.title}
                          className="cursor-pointer transition-colors rounded-md p-2 hover:border border-lia-border-subtle"
                          style={{backgroundColor: "var(--gray-50)"}}
                          onClick={() => {
                            onSetLiaPromptValue(`Criar vaga ${template.title}`)
                            setActiveSearchTab("ia-natural")
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--gray-400)")}
                          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--gray-50)")}
                        >
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm">{template.icon}</span>
                            <div className="flex-1 min-w-0">
                              <h5 className="text-xs font-medium truncate text-gray-800">{template.title}</h5>
                              <div className="flex gap-1 mt-0.5">
                                {template.tags.map((tag) => (
                                  <span
                                    key={tag}
                                    className="text-micro px-1 py-0.5 rounded-full text-gray-400"
                                    style={{backgroundColor: "var(--gray-50)"}}
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Seção 2: Criar a partir de Vaga Existente */}
                  <div className="pt-2">
                    <h4 className="text-xs font-medium mb-0.5 text-gray-800">
                      Criar a Partir de Vaga Existente
                    </h4>
                    <p className={`${textStyles.caption} mb-2`}>Copie uma vaga já criada e faça ajustes</p>

                    {/* Campo de Busca de Vagas */}
                    <div className="relative">
                      <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Buscar vaga por título ou ID..."
                        className="w-full pl-8 pr-3 py-2 text-xs rounded-md focus:outline-none transition-colors text-gray-800 border border-lia-border-subtle"
                        style={{backgroundColor: "var(--gray-50)"}}
                        onFocus={(e) => (e.target.style.borderColor = "var(--gray-400)")}
                        onBlur={(e) => (e.target.style.borderColor = "var(--gray-50)")}
                      />
                    </div>

                    {/* Lista de Vagas Recentes */}
                    <div className="mt-2 space-y-1.5">
                      {[
                        { id: "V0001", title: "Product Manager - Fintech" },
                        { id: "V0004", title: "Tech Lead Mobile" },
                        { id: "V0005", title: "DevOps Engineer Sênior" },
                      ].map((job) => (
                        <div
                          key={job.id}
                          className="flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors border border-lia-border-subtle"
                          style={{backgroundColor: "var(--gray-50)"}}
                          onClick={() => {
                            onSetLiaPromptValue(`Duplicar vaga ${job.id} - ${job.title}`)
                            setActiveSearchTab("ia-natural")
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--gray-400)")}
                          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--gray-50)")}
                        >
                          <span
                            className="text-micro px-1.5 py-0.5 rounded-full"
                            style={{backgroundColor: "var(--gray-50)"}}
                          >
                            {job.id}
                          </span>
                          <span className="text-xs truncate flex-1 text-gray-800">{job.title}</span>
                          <Copy className="w-3.5 h-3.5 text-gray-400" />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Seção 3: Criar Novo Template */}
                  <div className="pt-2">
                    <h4 className="text-xs font-medium mb-0.5 text-gray-800">Salvar Template</h4>
                    <p className={`${textStyles.caption} mb-2`}>
                      Transforme uma vaga existente em template reutilizável
                    </p>

                    <Button
                      variant="outline"
                      className="w-full h-9 !text-xs font-medium rounded-md text-gray-800 border border-lia-border-subtle"
                      onClick={() => {
                      }}
                    >
                      <Plus className="w-3.5 h-3.5 mr-1.5 text-gray-600" />
                      Criar Template a Partir de Vaga
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Resize Handle - só mostra no modo geral */}
      {chatMode !== "job-creation" && (
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-ew-resize hover:bg-status-warning transition-colors group-hover:opacity-100 opacity-0 bg-status-warning/30"
          onMouseDown={(e) => {
            e.preventDefault()
            onSetIsResizingLIA(true)
            const startX = e.clientX
            const startWidth = liaWidth

            const handleMouseMove = (e: MouseEvent) => {
              const deltaX = e.clientX - startX
              const newWidth = Math.max(400, Math.min(800, startWidth + deltaX))
              onSetLiaWidth(newWidth)
            }

            const handleMouseUp = () => {
              onSetIsResizingLIA(false)
              document.removeEventListener("mousemove", handleMouseMove)
              document.removeEventListener("mouseup", handleMouseUp)
            }

            document.addEventListener("mousemove", handleMouseMove)
            document.addEventListener("mouseup", handleMouseUp)
          }}
        />
      )}
    </div>
  )
}
