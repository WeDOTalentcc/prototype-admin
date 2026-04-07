"use client"

import React from "react"

import { useState, useCallback, useRef, useEffect } from "react"
import { FileText, Database, Users } from "lucide-react"
import type { Message, ContextPanelData } from "./chat-core.types"
import { MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, ALLOWED_FILE_TYPES } from "./chat-core.constants"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import { toast } from "sonner"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { cleanAgentResponse } from "@/lib/chat-format"

interface UseChatMessagesOptions {
  initialMessages: Message[]
  setContextData: (data: ContextPanelData | null) => void
  setIsPanelOpen: (open: boolean) => void
}

export function useChatMessages({
  initialMessages,
  setContextData,
  setIsPanelOpen,
}: UseChatMessagesOptions) {
  const { chatMessages: unifiedMessages, addChatMessage, chatStreamingContent } = useLiaChatContext()
  const authUser = useAuthStore((s) => s.user)

  const [messages, setMessages] = useState<Message[]>(() => {
    if (unifiedMessages.length > 0) {
      return unifiedMessages.map((m, idx) => ({
        id: idx + 1,
        sender: m.sender,
        content: m.content,
        timestamp: m.timestamp,
      }))
    }
    return initialMessages
  })
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [showSearch, setShowSearch] = useState(false)
  const [newMessageIndicator, setNewMessageIndicator] = useState(false)
  const [currentMessageIndex, setCurrentMessageIndex] = useState(-1)

  // File attachment state
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [fileValidationError, setFileValidationError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)

  // File analysis context
  const [fileAnalysisContext, setFileAnalysisContext] = useState<FileAnalysisResult | null>(null)

  // DOM refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
// ── Scroll helpers ─────────────────────────────────────────
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  const checkNewMessageIndicator = useCallback(() => {
    if (!messagesContainerRef.current) return
    const container = messagesContainerRef.current
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100
    setNewMessageIndicator(!isAtBottom && messages.length > 0)
  }, [messages.length])

  useEffect(() => {
    scrollToBottom()
    checkNewMessageIndicator()
  }, [messages, chatStreamingContent, checkNewMessageIndicator])

  useEffect(() => {
    setMessages(
      unifiedMessages.map((m, idx) => ({
        id: idx + 1,
        sender: m.sender,
        content: m.content,
        timestamp: m.timestamp,
        metadata: m.metadata,
      }))
    )
  }, [unifiedMessages])

  // ── File attachment handlers ────────────────────────────────
  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const newFiles = Array.from(files)
      const validFiles: File[] = []
      const errors: string[] = []

      newFiles.forEach(file => {
        if (file.size > MAX_FILE_SIZE_BYTES) {
          const sizeMB = (file.size / (1024 * 1024)).toFixed(1)
          errors.push(`"${file.name}" excede ${MAX_FILE_SIZE_MB}MB (${sizeMB}MB)`)
          return
        }
        if (!(file.type in ALLOWED_FILE_TYPES)) {
          const ext = file.name.split('.').pop()?.toUpperCase() || 'desconhecido'
          errors.push(`"${file.name}" tem tipo não suportado (.${ext})`)
          return
        }
        validFiles.push(file)
      })

      if (errors.length > 0) {
        const errorMessage = errors.length === 1
          ? errors[0]
          : `${errors.length} arquivos rejeitados:\n• ${errors.join('\n• ')}`
        setFileValidationError(errorMessage)
        setTimeout(() => setFileValidationError(null), 5000)
      }

      if (validFiles.length > 0) {
        setAttachedFiles(prev => [...prev, ...validFiles])
        const fileNames = validFiles.map(f => f.name).join(", ")
        const message = validFiles.length === 1
          ? `Arquivo "${fileNames}" anexado. O que gostaria que eu fizesse com ele?`
          : `${validFiles.length} arquivos anexados (${fileNames}). O que gostaria que eu fizesse com eles?`

        const liaResponse: Message = {
          id: Date.now(),
          sender: "lia",
          content: message,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
          actions: [
            { label: "Analisar CV", icon: FileText as React.ElementType, variant: "default" },
            { label: "Extrair dados", icon: Database as React.ElementType, variant: "outline" },
            { label: "Comparar perfis", icon: Users as React.ElementType, variant: "outline" },
          ],
        }
        setMessages(prev => [...prev, liaResponse])
      }
    }
    if (e.target) e.target.value = ""
  }, [])

  const handleRemoveFile = useCallback((index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  const handleFilesSelected = useCallback((files: File[]) => {
    setAttachedFiles(prev => [...prev, ...files])
  }, [])

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      setFileAnalysisContext(analysis)
      toast.info("Arquivo analisado", { description: `${file.name} foi processado. A análise será enviada junto com sua próxima mensagem.` })
    } else {
      toast.error("Erro na análise", { description: analysis.error || `Não foi possível analisar ${file.name}` })
    }
  }, [toast])

  // ── Voice recording handlers ────────────────────────────────
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        setAudioBlob(blob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
    } catch {
      const errorMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: "Não consegui acessar o microfone. Por favor, verifique as permissões do navegador e tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text",
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
        recordingTimerRef.current = null
      }
    }
  }, [isRecording])

  const handleRecordingToggle = useCallback(() => {
    if (isRecording) stopRecording()
    else startRecording()
  }, [isRecording, startRecording, stopRecording])

  const handleAudioTranscription = useCallback((text: string) => {
    setInput(prev => prev ? `${prev} ${text}` : text)
    toast.success("Áudio transcrito", { description: "O texto foi adicionado ao campo de mensagem." })
    inputRef.current?.focus()
  }, [toast])

  const handleAudioRecordingStart = useCallback(() => {
    toast.success("Gravando...", { description: "Fale sua mensagem. Clique novamente para parar." })
  }, [toast])

  const handleAudioRecordingEnd = useCallback(() => {
    toast.success("Processando áudio", { description: "Aguarde enquanto transcrevemos sua mensagem." })
  }, [toast])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current)
    }
  }, [])

  // ── Action click handler ───────────────────────────────────
  const handleActionClick = useCallback((message: Message, _action: Record<string, unknown>) => {
    if (message.contextData) {
      setContextData({
        type: message.contextData.type,
        title: message.contextData.title,
        data: message.contextData.data,
      } as ContextPanelData)
      setIsPanelOpen(true)
    }
  }, [setContextData, setIsPanelOpen])

  // ── Text utilities ─────────────────────────────────────────
  const getRelativeTime = useCallback((timestamp: string) => {
    const now = new Date()
    const messageTime = new Date(`2024-02-22T${timestamp}:00`)
    const diffInMinutes = Math.floor((now.getTime() - messageTime.getTime()) / (1000 * 60))
    if (diffInMinutes < 1) return "agora"
    if (diffInMinutes < 60) return `há ${diffInMinutes} min`
    if (diffInMinutes < 1440) return `há ${Math.floor(diffInMinutes / 60)}h`
    return "ontem"
  }, [])

  const formatMessageContent = useCallback((text: string) => {
    let formatted = cleanAgentResponse(text)
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    formatted = formatted.replace(/\n\n/g, '<br/><br/>')
    formatted = formatted.replace(/\n/g, '<br/>')
    formatted = formatted.replace(/•\s/g, '• ')
    return formatted
  }, [])

  const highlightSearchTerm = useCallback((text: string, term: string) => {
    const formatted = formatMessageContent(text)
    if (!term) return formatted
    const regex = new RegExp(`(${term})`, 'gi')
    return formatted.replace(regex, '<mark class="bg-status-warning/10 dark:bg-status-warning/10">$1</mark>')
  }, [formatMessageContent])

  const getQuickSuggestions = useCallback(() => {
    const lastLiaMessage = messages.filter(m => m.sender === "lia").pop()
    if (!lastLiaMessage) return []
    const content = lastLiaMessage.content.toLowerCase()
    if (content.includes("competências") || content.includes("liderança"))
      return ["Concordo", "Preciso de mais detalhes", "Vamos prosseguir"]
    if (content.includes("remuneração") || content.includes("salário"))
      return ["Está dentro do orçamento", "Precisamos ajustar", "Perfeito"]
    if (content.includes("candidato") || content.includes("perfil"))
      return ["Interessante", "Vamos agendar", "Preciso avaliar"]
    return ["Entendi", "Continue", "Preciso de mais informações"]
  }, [messages])

  return {
    // Auth
    authUser,
    // State
    messages, setMessages,
    input, setInput,
    isLoading, setIsLoading,
    searchTerm, setSearchTerm,
    showSearch, setShowSearch,
    newMessageIndicator,
    currentMessageIndex, setCurrentMessageIndex,
    // File
    attachedFiles, setAttachedFiles,
    fileValidationError, setFileValidationError,
    fileInputRef,
    // Voice
    isRecording,
    recordingTime,
    audioBlob, setAudioBlob,
    // File analysis
    fileAnalysisContext, setFileAnalysisContext,
    // Refs
    messagesEndRef,
    messagesContainerRef,
    inputRef,
    // Handlers
    scrollToBottom,
    checkNewMessageIndicator,
    handleFileButtonClick,
    handleFileChange,
    handleRemoveFile,
    handleFilesSelected,
    handleFileAnalyzed,
    handleAudioTranscription,
    handleAudioRecordingStart,
    handleAudioRecordingEnd,
    startRecording,
    stopRecording,
    handleRecordingToggle,
    handleActionClick,
    // Utilities
    getRelativeTime,
    formatMessageContent,
    highlightSearchTerm,
    getQuickSuggestions,
  }
}
