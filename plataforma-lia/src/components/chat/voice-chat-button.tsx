"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Mic, MicOff, Loader2, Volume2, Square, VolumeX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { voiceChat, getVoiceStatus } from "@/services/lia-api"

interface VoiceChatButtonProps {
  sessionId?: string
  onTranscription?: (text: string) => void
  onResponse?: (response: { text: string; audio?: string }) => void
  onError?: (error: string) => void
  className?: string
  disabled?: boolean
}

export function VoiceChatButton({
  sessionId,
  onTranscription,
  onResponse,
  onError,
  className,
  disabled
}: VoiceChatButtonProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [voiceAvailable, setVoiceAvailable] = useState(true)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    getVoiceStatus().then(status => {
      setVoiceAvailable(status.transcription_available && status.synthesis_available)
    })
  }, [])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (audioRef.current) {
        audioRef.current.pause()
      }
    }
  }, [])

  const processAudio = useCallback(async (audioBlob: Blob) => {
    setIsProcessing(true)
    try {
      const result = await voiceChat(audioBlob, sessionId)
      
      if (result.transcription) {
        onTranscription?.(result.transcription)
      }
      
      onResponse?.({ 
        text: result.response_text, 
        audio: result.response_audio_base64 
      })
      
      if (result.response_audio_base64) {
        playAudioResponse(result.response_audio_base64)
      }
    } catch (err) {
      onError?.('Erro ao processar áudio. Tente novamente.')
    } finally {
      setIsProcessing(false)
    }
  }, [onError, onResponse, onTranscription, sessionId])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        stream.getTracks().forEach(track => track.stop())
        streamRef.current = null
        await processAudio(audioBlob)
      }

      mediaRecorder.start(1000)
      setIsRecording(true)
      setRecordingTime(0)
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
    } catch (err) {
      onError?.('Não foi possível acessar o microfone. Verifique as permissões do navegador.')
    }
  }, [onError, processAudio])

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }, [])



  const playAudioResponse = (base64Audio: string) => {
    try {
      const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`)
      audioRef.current = audio
      setIsPlaying(true)
      audio.play()
      audio.onended = () => {
        setIsPlaying(false)
        audioRef.current = null
      }
      audio.onerror = () => {
        setIsPlaying(false)
        audioRef.current = null
      }
    } catch (err) {
    }
  }

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    setIsPlaying(false)
  }, [])

  const handleClick = () => {
    if (isPlaying) {
      stopPlayback()
    } else if (isRecording) {
      stopRecording()
    } else if (!isProcessing) {
      startRecording()
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getButtonContent = () => {
    if (isProcessing) {
      return (
        <>
          <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
          <span className="text-xs ml-1">Processando...</span>
        </>
      )
    }
    if (isPlaying) {
      return (
        <>
          <VolumeX className="h-4 w-4" />
          <span className="text-xs ml-1">Parar</span>
        </>
      )
    }
    if (isRecording) {
      return (
        <>
          <Square className="h-4 w-4 fill-current" />
          <span className="text-xs ml-1">{formatTime(recordingTime)}</span>
        </>
      )
    }
    return <Mic className="h-4 w-4" />
  }

  const getTooltip = () => {
    if (isProcessing) return 'Processando áudio...'
    if (isPlaying) return 'Clique para parar a reprodução'
    if (isRecording) return 'Clique para parar a gravação'
    return 'Clique para gravar por voz'
  }

  if (!voiceAvailable) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled
        className={cn("h-8 w-8 text-lia-text-disabled focus-visible:ring-2 focus-visible:ring-lia-border-default", className)}
        title="Chat por voz não disponível"
        aria-label="Chat por voz não disponível"
      >
        <MicOff className="h-4 w-4" />
      </Button>
    )
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size={isRecording || isProcessing || isPlaying ? "sm" : "icon"}
      onClick={handleClick}
      disabled={disabled || isProcessing}
      title={getTooltip()}
      aria-label={getTooltip()}
      className={cn(
        "transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-lia-border-default",
        isRecording 
          ? "text-status-error hover:text-status-error hover:bg-status-error/10 animate-pulse motion-reduce:animate-none px-3" 
          : isPlaying 
            ? "text-lia-text-secondary hover:text-wedo-cyan-dark hover:bg-lia-bg-tertiary px-3"
            : isProcessing
              ? "text-lia-text-tertiary px-3"
              : "h-8 w-8 text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover",
        className
      )}
    >
      {getButtonContent()}
    </Button>
  )
}
