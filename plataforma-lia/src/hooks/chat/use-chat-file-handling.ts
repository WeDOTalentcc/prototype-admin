"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { Message } from "@/types/chat"
import { FileAnalysisResult } from "@/components/ui/file-upload-button"
import { toast } from "sonner"
// ──────────────────────────────────────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────────────────────────────────────

import { MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES } from '@/constants/upload'
const ALLOWED_FILE_TYPES = {
  "application/pdf": "PDF",
  "application/msword": "DOC",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
    "DOCX",
  "text/plain": "TXT",
  "text/csv": "CSV",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
  "application/vnd.ms-excel": "XLS",
  "image/png": "PNG",
  "image/jpeg": "JPG",
  "image/jpg": "JPG",
} as const

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

export interface ChatFileHandlingState {
  attachedFiles: File[]
  fileValidationError: string | null
  fileAnalysisContext: FileAnalysisResult | null
  isRecording: boolean
  recordingTime: number
  audioBlob: Blob | null
}

export interface ChatFileHandlingActions {
  setAttachedFiles: React.Dispatch<React.SetStateAction<File[]>>
  setFileValidationError: React.Dispatch<React.SetStateAction<string | null>>
  setFileAnalysisContext: React.Dispatch<React.SetStateAction<FileAnalysisResult | null>>
  setIsRecording: React.Dispatch<React.SetStateAction<boolean>>
  setRecordingTime: React.Dispatch<React.SetStateAction<number>>
  setAudioBlob: React.Dispatch<React.SetStateAction<Blob | null>>
  handleFileButtonClick: () => void
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleRemoveFile: (index: number) => void
  handleFilesSelected: (files: File[]) => void
  handleFileAnalyzed: (file: File, analysis: FileAnalysisResult) => void
  handleAudioTranscription: (text: string) => void
  handleAudioRecordingStart: () => void
  handleAudioRecordingEnd: () => void
  startRecording: () => Promise<void>
  stopRecording: () => void
  handleRecordingToggle: () => void
  fileInputRef: React.RefObject<HTMLInputElement | null>
  MAX_FILE_SIZE_MB: number
  MAX_FILE_SIZE_BYTES: number
  ALLOWED_FILE_TYPES: typeof ALLOWED_FILE_TYPES
}

export interface UseChatFileHandlingReturn {
  state: ChatFileHandlingState
  actions: ChatFileHandlingActions
}

// ──────────────────────────────────────────────────────────────────────────────
// Hook
// ──────────────────────────────────────────────────────────────────────────────

interface UseChatFileHandlingParams {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setInput: React.Dispatch<React.SetStateAction<string>>
  inputRef: React.RefObject<HTMLTextAreaElement | null>
}

export function useChatFileHandling({
  setMessages,
  setInput,
  inputRef,
}: UseChatFileHandlingParams): UseChatFileHandlingReturn {
const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [fileValidationError, setFileValidationError] = useState<string | null>(null)
  const [fileAnalysisContext, setFileAnalysisContext] = useState<FileAnalysisResult | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup recording timer on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [])

  // ── file attachment handlers ─────────────────────────────────────────────────

  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        const newFiles = Array.from(files)
        const validFiles: File[] = []
        const errors: string[] = []

        newFiles.forEach((file) => {
          if (file.size > MAX_FILE_SIZE_BYTES) {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(1)
            errors.push(`"${file.name}" excede ${MAX_FILE_SIZE_MB}MB (${sizeMB}MB)`)
            return
          }

          if (!(file.type in ALLOWED_FILE_TYPES)) {
            const ext = file.name.split(".").pop()?.toUpperCase() || "desconhecido"
            errors.push(`"${file.name}" tem tipo não suportado (.${ext})`)
            return
          }

          validFiles.push(file)
        })

        if (errors.length > 0) {
          const errorMessage =
            errors.length === 1
              ? errors[0]
              : `${errors.length} arquivos rejeitados:\n• ${errors.join("\n• ")}`
          setFileValidationError(errorMessage)
          setTimeout(() => setFileValidationError(null), 5000)
        }

        if (validFiles.length > 0) {
          setAttachedFiles((prev) => [...prev, ...validFiles])

          const fileNames = validFiles.map((f) => f.name).join(", ")
          const messageText =
            validFiles.length === 1
              ? `Arquivo "${fileNames}" anexado. O que gostaria que eu fizesse com ele?`
              : `${validFiles.length} arquivos anexados (${fileNames}). O que gostaria que eu fizesse com eles?`

          const liaResponse: Message = {
            id: Date.now(),
            sender: "lia",
            content: messageText,
            timestamp: new Date().toLocaleTimeString("pt-BR", {
              hour: "2-digit",
              minute: "2-digit",
            }),
            type: "text",
            actions: [
              { label: "Analisar CV", variant: "default" },
              { label: "Extrair dados", variant: "outline" },
              { label: "Comparar perfis", variant: "outline" },
            ],
          }
          setMessages((prev) => [...prev, liaResponse])
        }
      }
      if (e.target) {
        e.target.value = ""
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  const handleRemoveFile = useCallback((index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleFilesSelected = useCallback((files: File[]) => {
    setAttachedFiles((prev) => [...prev, ...files])
  }, [])

  const handleFileAnalyzed = useCallback(
    (file: File, analysis: FileAnalysisResult) => {
      if (analysis.success) {
        setFileAnalysisContext(analysis)
        toast.info("Arquivo analisado", { description: `${file.name} foi processado. A análise será enviada junto com sua próxima mensagem.` })
      } else {
        toast.error("Erro na análise", { description: analysis.error || `Não foi possível analisar ${file.name}` })
      }
    },
     
    []
  )

  // ── audio / recording handlers ───────────────────────────────────────────────

  const handleAudioTranscription = useCallback(
    (text: string) => {
      setInput((prev) => (prev ? `${prev} ${text}` : text))
      toast.success("Áudio transcrito", { description: "O texto foi adicionado ao campo de mensagem." })
      inputRef.current?.focus()
    },
    [setInput, inputRef]
  )

  const handleAudioRecordingStart = useCallback(() => {
    toast.success("Gravando...", { description: "Fale sua mensagem. Clique novamente para parar." })
   
  }, [])

  const handleAudioRecordingEnd = useCallback(() => {
    toast.success("Processando áudio", { description: "Aguarde enquanto transcrevemos sua mensagem." })
   
  }, [])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        setAudioBlob(blob)
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      recordingTimerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
    } catch {
      const errorMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content:
          "Não consegui acessar o microfone. Por favor, verifique as permissões do navegador e tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        type: "text",
      }
      setMessages((prev) => [...prev, errorMessage])
    }
  }, [setMessages])

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
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopRecording])

  return {
    state: {
      attachedFiles,
      fileValidationError,
      fileAnalysisContext,
      isRecording,
      recordingTime,
      audioBlob,
    },
    actions: {
      setAttachedFiles,
      setFileValidationError,
      setFileAnalysisContext,
      setIsRecording,
      setRecordingTime,
      setAudioBlob,
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
      fileInputRef,
      MAX_FILE_SIZE_MB,
      MAX_FILE_SIZE_BYTES,
      ALLOWED_FILE_TYPES,
    },
  }
}
