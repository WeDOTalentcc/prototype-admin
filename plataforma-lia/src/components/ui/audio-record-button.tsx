"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Mic, Loader2, Square } from "lucide-react"
import { cn } from "@/lib/utils"

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  lang: string
  start(): void
  stop(): void
  abort(): void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
}

interface AudioRecordButtonProps {
  onTranscription: (text: string) => void
  onRecordingStart?: () => void
  onRecordingEnd?: () => void
  disabled?: boolean
  className?: string
  maxDuration?: number
  transcriptionUrl?: string
}

type RecordingMethod = "speech-api" | "media-recorder" | null

function getSpeechRecognition(): (new () => SpeechRecognition) | null {
  if (typeof window === "undefined") return null
  return (
    (window as unknown as Record<string, unknown>).SpeechRecognition as (new () => SpeechRecognition) ||
    (window as unknown as Record<string, unknown>).webkitSpeechRecognition as (new () => SpeechRecognition) ||
    null
  )
}

export function AudioRecordButton({
  onTranscription,
  onRecordingStart,
  onRecordingEnd,
  disabled = false,
  className,
  maxDuration = 60,
  transcriptionUrl = "/api/backend-proxy/transcribe/audio",
}: AudioRecordButtonProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const isRecordingRef = useRef(false)
  const onRecordingEndRef = useRef(onRecordingEnd)
  const methodRef = useRef<RecordingMethod>(null)
  const interimTextRef = useRef("")

  useEffect(() => {
    onRecordingEndRef.current = onRecordingEnd
  }, [onRecordingEnd])

  const cleanup = useCallback(() => {
    isRecordingRef.current = false
    setIsRecording(false)

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    if (recognitionRef.current) {
      try { recognitionRef.current.abort() } catch {}
      recognitionRef.current = null
    }

    onRecordingEndRef.current?.()
  }, [])

  const startTimer = useCallback(() => {
    setRecordingTime(0)
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => {
        if (prev >= maxDuration - 1) {
          cleanup()
          return prev
        }
        return prev + 1
      })
    }, 1000)
  }, [maxDuration, cleanup])

  const startWithSpeechAPI = useCallback(() => {
    const SpeechRecognitionClass = getSpeechRecognition()
    if (!SpeechRecognitionClass) return false

    try {
      const recognition = new SpeechRecognitionClass()
      recognition.lang = "pt-BR"
      recognition.continuous = true
      recognition.interimResults = true
      recognition.maxAlternatives = 1

      let finalTranscript = ""
      interimTextRef.current = ""

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interim = ""
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + " "
          } else {
            interim += transcript
          }
        }
        interimTextRef.current = interim
      }

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        if (event.error === "not-allowed" || event.error === "service-not-available") {
          cleanup()
          startWithMediaRecorder()
          return
        }
        if (event.error !== "aborted" && event.error !== "no-speech") {
          setError("Erro no reconhecimento de voz")
          cleanup()
        }
      }

      recognition.onend = () => {
        if (isRecordingRef.current && methodRef.current === "speech-api") {
          const text = finalTranscript.trim()
          if (text) {
            onTranscription(text)
          } else if (interimTextRef.current.trim()) {
            onTranscription(interimTextRef.current.trim())
          }
          cleanup()
        }
      }

      recognition.start()
      recognitionRef.current = recognition
      methodRef.current = "speech-api"
      isRecordingRef.current = true
      setIsRecording(true)
      setError(null)
      onRecordingStart?.()
      startTimer()
      return true
    } catch {
      return false
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cleanup, onRecordingStart, startTimer, onTranscription])

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsTranscribing(true)
    try {
      const formData = new FormData()
      formData.append("audio", audioBlob, "recording.webm")

      const response = await fetch(transcriptionUrl, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.status}`)
      }

      const data = await response.json()
      if (data.text) {
        onTranscription(data.text)
      } else if (data.error) {
        setError(data.error)
      }
    } catch {
      setError("Erro ao transcrever áudio")
    } finally {
      setIsTranscribing(false)
    }
  }

  const startWithMediaRecorder = useCallback(async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "audio/mp4",
      })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType,
        })
        await transcribeAudio(audioBlob)
      }

      mediaRecorder.start(1000)
      methodRef.current = "media-recorder"
      isRecordingRef.current = true
      setIsRecording(true)
      onRecordingStart?.()
      startTimer()
    } catch {
      setError("Não foi possível acessar o microfone. Verifique as permissões do navegador.")
      isRecordingRef.current = false
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [maxDuration, onRecordingStart, startTimer])

  const startRecording = useCallback(() => {
    if (isRecordingRef.current) return
    setError(null)

    const speechStarted = startWithSpeechAPI()
    if (!speechStarted) {
      startWithMediaRecorder()
    }
  }, [startWithSpeechAPI, startWithMediaRecorder])

  const stopRecording = useCallback(() => {
    if (!isRecordingRef.current) return

    if (methodRef.current === "speech-api" && recognitionRef.current) {
      recognitionRef.current.stop()
    } else if (methodRef.current === "media-recorder" && mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop()
      cleanup()
    } else {
      cleanup()
    }
  }, [cleanup])

  const handleClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const tooltipText = isTranscribing
    ? "Transcrevendo..."
    : isRecording
    ? "Parar gravação"
    : "Gravar por voz"

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={handleClick}
        disabled={disabled || isTranscribing}
        title={tooltipText}
        className={cn(
 "h-8 w-8 transition-colors",
          isRecording
            ? "text-status-error hover:text-status-error hover:bg-status-error/10 animate-pulse motion-reduce:animate-none"
            : "text-lia-border-strong hover:text-lia-text-primary hover:bg-lia-interactive-hover"
        )}
      >
        {isTranscribing ? (
          <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
        ) : isRecording ? (
          <Square className="h-4 w-4 fill-current" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>

      {isRecording && (
        <div className="flex items-center gap-2 text-xs text-status-error">
          <span className="w-2 h-2 rounded-full bg-status-error animate-pulse motion-reduce:animate-none" />
          <span>{formatTime(recordingTime)}</span>
        </div>
      )}

      {error && (
        <span className="text-xs text-status-error">{error}</span>
      )}
    </div>
  )
}
