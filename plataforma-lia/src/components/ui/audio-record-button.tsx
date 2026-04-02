"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Mic, Loader2, Square } from "lucide-react"
import { cn } from "@/lib/utils"

interface AudioRecordButtonProps {
  onTranscription: (text: string) => void
  onRecordingStart?: () => void
  onRecordingEnd?: () => void
  disabled?: boolean
  className?: string
  maxDuration?: number
  transcriptionUrl?: string
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

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const isRecordingRef = useRef(false)
  const onRecordingEndRef = useRef(onRecordingEnd)

  useEffect(() => {
    onRecordingEndRef.current = onRecordingEnd
  }, [onRecordingEnd])

  const stopRecordingInternal = useCallback(() => {
    if (!isRecordingRef.current) return
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      isRecordingRef.current = false
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      onRecordingEndRef.current?.()

      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
    }
  }, [])

  const startRecording = useCallback(async () => {
    if (isRecordingRef.current) return
    
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
      isRecordingRef.current = true
      setIsRecording(true)
      setRecordingTime(0)
      onRecordingStart?.()

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= maxDuration - 1) {
            stopRecordingInternal()
            return prev
          }
          return prev + 1
        })
      }, 1000)
    } catch (err) {
      setError("Não foi possível acessar o microfone")
      isRecordingRef.current = false
    }
  }, [maxDuration, onRecordingStart, stopRecordingInternal])

  const stopRecording = useCallback(() => {
    stopRecordingInternal()
  }, [stopRecordingInternal])

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
    } catch (err) {
      setError("Erro ao transcrever áudio")
    } finally {
      setIsTranscribing(false)
    }
  }

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
            : "lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover"
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
