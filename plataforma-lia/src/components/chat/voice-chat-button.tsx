"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Mic, MicOff, Loader2, Volume2, Square, VolumeX, Radio } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { voiceChat, getVoiceStatus, createVoiceStreamConnection } from "@/services/lia-api"
import type { VoiceStreamMessage } from "@/services/lia-api/types"

interface VoiceChatButtonProps {
  sessionId?: string
  onTranscription?: (text: string) => void
  onResponse?: (response: { text: string; audio?: string }) => void
  onError?: (error: string) => void
  className?: string
  disabled?: boolean
  streamingEnabled?: boolean
  wsSessionId?: string
  wsToken?: string
  onStreamingInit?: () => void
  onStreamingEnd?: () => void
}

type VoiceMode = 'idle' | 'connecting' | 'streaming' | 'recording' | 'processing' | 'playing'

export function VoiceChatButton({
  sessionId,
  onTranscription,
  onResponse,
  onError,
  className,
  disabled,
  streamingEnabled = false,
  wsSessionId,
  wsToken,
  onStreamingInit,
  onStreamingEnd,
}: VoiceChatButtonProps) {
  const [mode, setMode] = useState<VoiceMode>('idle')
  const [recordingTime, setRecordingTime] = useState(0)
  const [voiceAvailable, setVoiceAvailable] = useState(true)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const wsConnectionRef = useRef<ReturnType<typeof createVoiceStreamConnection> | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const audioQueueRef = useRef<ArrayBuffer[]>([])
  const isPlayingQueueRef = useRef(false)
  const autoStartedSessionRef = useRef<string | null>(null)

  useEffect(() => {
    getVoiceStatus().then(status => {
      setVoiceAvailable(status.transcription_available && status.synthesis_available)
    })
  }, [])

  useEffect(() => {
    return () => {
      cleanupAll()
    }
  }, [])

  const cleanupAll = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    if (wsConnectionRef.current) {
      wsConnectionRef.current.close()
      wsConnectionRef.current = null
    }
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    audioQueueRef.current = []
    isPlayingQueueRef.current = false
  }, [])

  const playAudioQueue = useCallback(async () => {
    if (isPlayingQueueRef.current || audioQueueRef.current.length === 0) return
    isPlayingQueueRef.current = true

    try {
      const ctx = audioContextRef.current || new AudioContext({ sampleRate: 24000 })
      audioContextRef.current = ctx

      while (audioQueueRef.current.length > 0) {
        const chunk = audioQueueRef.current.shift()
        if (!chunk) continue

        try {
          const pcmData = new Int16Array(chunk)
          const floatData = new Float32Array(pcmData.length)
          for (let i = 0; i < pcmData.length; i++) {
            floatData[i] = pcmData[i] / 32768.0
          }

          const audioBuffer = ctx.createBuffer(1, floatData.length, 24000)
          audioBuffer.getChannelData(0).set(floatData)

          const source = ctx.createBufferSource()
          source.buffer = audioBuffer
          source.connect(ctx.destination)

          await new Promise<void>((resolve) => {
            source.onended = () => resolve()
            source.start()
          })
        } catch {
          continue
        }
      }
    } finally {
      isPlayingQueueRef.current = false
    }
  }, [])

  const stopStreaming = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (wsConnectionRef.current) {
      wsConnectionRef.current.close()
      wsConnectionRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }
    autoStartedSessionRef.current = null
    setMode('idle')
    setRecordingTime(0)
    onStreamingEnd?.()
  }, [onStreamingEnd])

  const handleStreamEvent = useCallback((event: VoiceStreamMessage) => {
    switch (event.type) {
      case 'transcript':
        if (event.role === 'candidate' && event.text) {
          onTranscription?.(event.text)
        } else if (event.role === 'lia' && event.text) {
          onResponse?.({ text: event.text })
        }
        break

      case 'audio':
        if (event.data) {
          const binaryStr = atob(event.data)
          const bytes = new Uint8Array(binaryStr.length)
          for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i)
          }
          audioQueueRef.current.push(bytes.buffer)
          playAudioQueue()
        }
        break

      case 'status':
        if (event.status === 'connected' || event.status === 'in_progress') {
          setMode('streaming')
        } else if (event.status === 'ended' || event.status === 'timeout') {
          stopStreaming()
        }
        break

      case 'error':
        onError?.(event.message || 'Erro na conexão de voz')
        stopStreaming()
        break

      case 'turn_complete':
      case 'metrics':
        break
    }
  }, [onTranscription, onResponse, onError, playAudioQueue, stopStreaming])

  const processAudio = useCallback(async (audioBlob: Blob) => {
    setMode('processing')
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
        playLegacyAudioResponse(result.response_audio_base64)
      } else {
        setMode('idle')
      }
    } catch {
      onError?.('Erro ao processar áudio. Tente novamente.')
      setMode('idle')
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
      setMode('recording')
      setRecordingTime(0)
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
    } catch {
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
      setMode('idle')
    }
  }, [])

  const startStreaming = useCallback(async () => {
    if (!wsSessionId || !wsToken) {
      startRecording()
      return
    }

    setMode('connecting')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })
      streamRef.current = stream

      const connection = createVoiceStreamConnection(
        wsSessionId,
        wsToken,
        handleStreamEvent,
        () => {
          stopStreaming()
        },
        (error) => {
          onError?.(error)
          stopStreaming()
        },
      )
      wsConnectionRef.current = connection

      const audioContext = new AudioContext({ sampleRate: 16000 })
      audioContextRef.current = audioContext
      const source = audioContext.createMediaStreamSource(stream)
      sourceRef.current = source
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor

      processor.onaudioprocess = (e) => {
        if (!wsConnectionRef.current?.isConnected()) return
        const inputData = e.inputBuffer.getChannelData(0)
        const pcmData = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]))
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }
        wsConnectionRef.current.sendAudio(pcmData.buffer)
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      setMode('streaming')
      setRecordingTime(0)
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
    } catch {
      onError?.('Não foi possível acessar o microfone. Verifique as permissões do navegador.')
      setMode('idle')
    }
  }, [wsSessionId, wsToken, handleStreamEvent, onError, cleanupAll, startRecording])

  useEffect(() => {
    if (
      streamingEnabled &&
      wsSessionId &&
      wsToken &&
      mode === 'idle' &&
      autoStartedSessionRef.current !== wsSessionId
    ) {
      autoStartedSessionRef.current = wsSessionId
      startStreaming()
    }
  }, [streamingEnabled, wsSessionId, wsToken, mode, startStreaming])

  const playLegacyAudioResponse = (base64Audio: string) => {
    try {
      const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`)
      audioRef.current = audio
      setMode('playing')
      audio.play()
      audio.onended = () => {
        setMode('idle')
        audioRef.current = null
      }
      audio.onerror = () => {
        setMode('idle')
        audioRef.current = null
      }
    } catch {
      setMode('idle')
    }
  }

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    audioQueueRef.current = []
    isPlayingQueueRef.current = false
    setMode('idle')
  }, [])

  const handleClick = () => {
    switch (mode) {
      case 'playing':
        stopPlayback()
        break
      case 'streaming':
        stopStreaming()
        break
      case 'recording':
        stopRecording()
        break
      case 'idle':
        if (streamingEnabled && wsSessionId && wsToken) {
          startStreaming()
        } else if (onStreamingInit && !streamingEnabled) {
          onStreamingInit()
        } else {
          startRecording()
        }
        break
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getButtonContent = () => {
    if (mode === 'connecting') {
      return (
        <>
          <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
          <span className="text-xs ml-1">Conectando...</span>
        </>
      )
    }
    if (mode === 'processing') {
      return (
        <>
          <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
          <span className="text-xs ml-1">Processando...</span>
        </>
      )
    }
    if (mode === 'playing') {
      return (
        <>
          <VolumeX className="h-4 w-4" />
          <span className="text-xs ml-1">Parar</span>
        </>
      )
    }
    if (mode === 'streaming') {
      return (
        <>
          <Radio className="h-4 w-4 animate-pulse motion-reduce:animate-none" />
          <span className="text-xs ml-1">{formatTime(recordingTime)}</span>
        </>
      )
    }
    if (mode === 'recording') {
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
    if (mode === 'connecting') return 'Conectando ao serviço de voz...'
    if (mode === 'processing') return 'Processando áudio...'
    if (mode === 'playing') return 'Clique para parar a reprodução'
    if (mode === 'streaming') return 'Clique para encerrar a conversa por voz'
    if (mode === 'recording') return 'Clique para parar a gravação'
    return streamingEnabled ? 'Clique para iniciar conversa por voz em tempo real' : 'Clique para gravar por voz'
  }

  if (!voiceAvailable) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled
        className={cn("h-8 w-8 text-lia-text-muted focus-visible:ring-2 focus-visible:ring-lia-border-default", className)}
        title="Chat por voz não disponível"
        aria-label="Chat por voz não disponível"
      >
        <MicOff className="h-4 w-4" />
      </Button>
    )
  }

  const isExpanded = mode !== 'idle'
  const isDisabledState = disabled || mode === 'processing' || mode === 'connecting'

  return (
    <Button
      type="button"
      variant="ghost"
      size={isExpanded ? "sm" : "icon"}
      onClick={handleClick}
      disabled={isDisabledState}
      title={getTooltip()}
      aria-label={getTooltip()}
      className={cn(
        "transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-lia-border-default",
        mode === 'streaming'
          ? "text-wedo-cyan-text hover:text-wedo-cyan-dark hover:bg-wedo-cyan/10 animate-pulse motion-reduce:animate-none px-3"
          : mode === 'recording'
            ? "text-status-error hover:text-status-error hover:bg-status-error/10 animate-pulse motion-reduce:animate-none px-3"
            : mode === 'playing'
              ? "text-lia-text-secondary hover:text-wedo-cyan-dark hover:bg-lia-bg-tertiary px-3"
              : mode === 'processing' || mode === 'connecting'
                ? "text-lia-text-tertiary px-3"
                : "h-8 w-8 text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover",
        className
      )}
    >
      {getButtonContent()}
    </Button>
  )
}
