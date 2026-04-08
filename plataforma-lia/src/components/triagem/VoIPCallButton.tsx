"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Phone, PhoneOff, Mic, MicOff, Loader2, Volume2, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"

type VoIPState =
  | "idle"
  | "connecting"
  | "connected"
  | "muted"
  | "ended"
  | "error"
  | "unavailable"

interface VoIPCallButtonProps {
  token: string
  disabled?: boolean
  className?: string
  onCallStarted?: () => void
  onCallEnded?: () => void
  onError?: (message: string) => void
}

const AUDIO_SAMPLE_RATE = 16000
const AUDIO_BUFFER_SIZE = 4096

export function VoIPCallButton({
  token,
  disabled = false,
  className,
  onCallStarted,
  onCallEnded,
  onError,
}: VoIPCallButtonProps) {
  const [voipState, _setVoIPState] = useState<VoIPState>("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [callDuration, setCallDuration] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const playbackQueueRef = useRef<ArrayBuffer[]>([])
  const isPlayingRef = useRef(false)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const sessionIdRef = useRef<string | null>(null)
  const isMutedRef = useRef(false)
  const voipStateRef = useRef<VoIPState>("idle")

  const setVoIPState = useCallback((state: VoIPState) => {
    voipStateRef.current = state
    _setVoIPState(state)
  }, [])

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const stopAudio = useCallback(() => {
    if (processorRef.current) {
      try {
        processorRef.current.disconnect()
      } catch {}
      processorRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop())
      mediaStreamRef.current = null
    }
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close()
      } catch {}
      audioContextRef.current = null
    }
    playbackQueueRef.current = []
    isPlayingRef.current = false
  }, [])

  useEffect(() => {
    return () => {
      clearTimer()
      stopAudio()
      if (wsRef.current) {
        try {
          wsRef.current.close()
        } catch {}
      }
    }
  }, [clearTimer, stopAudio])

  const playAudioChunk = useCallback(async (audioData: ArrayBuffer) => {
    const ctx = audioContextRef.current
    if (!ctx || ctx.state === "closed") return

    playbackQueueRef.current.push(audioData)
    if (isPlayingRef.current) return

    isPlayingRef.current = true
    while (playbackQueueRef.current.length > 0) {
      const chunk = playbackQueueRef.current.shift()
      if (!chunk) break

      try {
        const pcmData = new Int16Array(chunk)
        const floatData = new Float32Array(pcmData.length)
        for (let i = 0; i < pcmData.length; i++) {
          floatData[i] = pcmData[i] / 32768.0
        }

        const audioBuffer = ctx.createBuffer(1, floatData.length, AUDIO_SAMPLE_RATE)
        audioBuffer.getChannelData(0).set(floatData)

        const source = ctx.createBufferSource()
        source.buffer = audioBuffer
        source.connect(ctx.destination)

        await new Promise<void>((resolve) => {
          source.onended = () => resolve()
          source.start()
        })
      } catch {
        break
      }
    }
    isPlayingRef.current = false
  }, [])

  const startCall = useCallback(async () => {
    if (disabled || voipState !== "idle") return

    setVoIPState("connecting")
    setErrorMessage(null)
    setCallDuration(0)

    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: AUDIO_SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })
      mediaStreamRef.current = stream
    } catch {
      const msg = "Microfone não disponível. Verifique as permissões do navegador."
      setErrorMessage(msg)
      setVoIPState("error")
      onError?.(msg)
      return
    }

    let sessionRes: {
      session_id: string
      gemini_available: boolean
      success: boolean
      voice_provider?: string
      ws_token?: string
      message?: string
    }
    try {
      const res = await fetch(`/api/backend-proxy/triagem/${token}/voip-start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const msg = data.detail || "Não foi possível iniciar sessão de voz"
        setErrorMessage(msg)
        setVoIPState("error")
        onError?.(msg)
        stopAudio()
        return
      }
      sessionRes = await res.json()

      if (!sessionRes.success) {
        const fallbackMsg = sessionRes.message || "Chamada de voz não disponível. Use o chat de texto."
        setErrorMessage(fallbackMsg)
        setVoIPState("unavailable")
        stopAudio()
        return
      }

      if (!sessionRes.gemini_available) {
        const fallbackMsg = sessionRes.message || "Chamada de voz não disponível. Use o chat de texto."
        setErrorMessage(fallbackMsg)
        setVoIPState("unavailable")
        stopAudio()
        return
      }
      sessionIdRef.current = sessionRes.session_id
    } catch {
      const msg = "Erro de rede ao iniciar sessão de voz"
      setErrorMessage(msg)
      setVoIPState("error")
      onError?.(msg)
      stopAudio()
      return
    }

    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
      const wsToken = sessionRes.ws_token ? `&ws_token=${encodeURIComponent(sessionRes.ws_token)}` : ""
      const wsUrl = `${protocol}//${window.location.host}/api/v1/gemini-voice/live-stream?session_id=${sessionRes.session_id}${wsToken}`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setVoIPState("connected")
        onCallStarted?.()
        timerRef.current = setInterval(() => {
          setCallDuration((prev) => prev + 1)
        }, 1000)

        const ctx = new AudioContext({ sampleRate: AUDIO_SAMPLE_RATE })
        audioContextRef.current = ctx

        const source = ctx.createMediaStreamSource(stream)
        const processor = ctx.createScriptProcessor(AUDIO_BUFFER_SIZE, 1, 1)
        processorRef.current = processor

        processor.onaudioprocess = (e) => {
          if (isMutedRef.current) return
          if (ws.readyState !== WebSocket.OPEN) return

          const inputData = e.inputBuffer.getChannelData(0)
          const pcmData = new Int16Array(inputData.length)
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]))
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff
          }

          ws.send(pcmData.buffer)
        }

        source.connect(processor)
        processor.connect(ctx.destination)
      }

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === "audio" && data.data) {
            const binaryStr = atob(data.data)
            const bytes = new Uint8Array(binaryStr.length)
            for (let i = 0; i < binaryStr.length; i++) {
              bytes[i] = binaryStr.charCodeAt(i)
            }
            await playAudioChunk(bytes.buffer)
          }

          if (data.type === "status") {
            if (data.status === "ended" || data.status === "timeout") {
              setVoIPState("ended")
              clearTimer()
              onCallEnded?.()
              stopAudio()
            }
          }

          if (data.type === "error") {
            const msg = data.message || "Erro na sessão de voz"
            setErrorMessage(msg)
            setVoIPState("error")
            clearTimer()
            onError?.(msg)
            stopAudio()
          }
        } catch {}
      }

      ws.onerror = () => {
        const msg = "Erro na conexão de voz"
        setErrorMessage(msg)
        setVoIPState("error")
        clearTimer()
        onError?.(msg)
        stopAudio()
      }

      ws.onclose = () => {
        const currentState = voipStateRef.current
        if (currentState === "connected" || currentState === "muted") {
          setVoIPState("ended")
          clearTimer()
          onCallEnded?.()
          stopAudio()
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao iniciar sessão de voz"
      setErrorMessage(msg)
      setVoIPState("error")
      onError?.(msg)
      stopAudio()
    }
  }, [disabled, voipState, token, clearTimer, stopAudio, playAudioChunk, onCallStarted, onCallEnded, onError, setVoIPState])

  const endCall = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: "end" }))
      } catch {}
      try {
        wsRef.current.close()
      } catch {}
    }
    clearTimer()
    stopAudio()
    setVoIPState("ended")
    onCallEnded?.()
  }, [clearTimer, stopAudio, onCallEnded, setVoIPState])

  const toggleMute = useCallback(() => {
    isMutedRef.current = !isMutedRef.current
    setVoIPState(isMutedRef.current ? "muted" : "connected")
  }, [setVoIPState])

  const reset = useCallback(() => {
    clearTimer()
    stopAudio()
    if (wsRef.current) {
      try {
        wsRef.current.close()
      } catch {}
      wsRef.current = null
    }
    sessionIdRef.current = null
    isMutedRef.current = false
    setVoIPState("idle")
    setErrorMessage(null)
    setCallDuration(0)
  }, [clearTimer, stopAudio, setVoIPState])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0")
    const s = (seconds % 60).toString().padStart(2, "0")
    return `${m}:${s}`
  }

  if (voipState === "unavailable") {
    return (
      <div className="flex flex-col gap-1.5">
        <button
          type="button"
          disabled
          title="Chamada por voz não disponível neste momento"
          aria-label="Chamada por voz indisponível"
          className={cn(
            "h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-lia-border-subtle text-lia-text-disabled text-sm font-medium opacity-50 cursor-not-allowed font-['Open_Sans',sans-serif]",
            className
          )}
        >
          <WifiOff className="w-4 h-4" />
          Voz indisponível
        </button>
        {errorMessage && (
          <p className="text-xs text-lia-text-secondary text-center leading-snug font-['Open_Sans',sans-serif] px-1">
            {errorMessage}
          </p>
        )}
      </div>
    )
  }

  if (voipState === "error") {
    return (
      <div className="flex flex-col gap-1.5">
        <button
          type="button"
          onClick={reset}
          title="Tentar novamente"
          aria-label="Tentar chamada de voz novamente"
          className={cn(
            "h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-status-error/40 text-status-error text-sm font-medium hover:bg-status-error/10 transition-colors font-['Open_Sans',sans-serif]",
            className
          )}
        >
          <Phone className="w-4 h-4" />
          Tentar novamente
        </button>
        {errorMessage && (
          <p className="text-xs text-status-error text-center leading-snug font-['Open_Sans',sans-serif] px-1">
            {errorMessage}
          </p>
        )}
      </div>
    )
  }

  if (voipState === "ended") {
    return (
      <button
        type="button"
        onClick={reset}
        title="Iniciar nova chamada de voz"
        aria-label="Iniciar nova chamada de voz"
        className={cn(
          "h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-lia-border-subtle text-lia-text-secondary text-sm font-medium hover:bg-lia-bg-tertiary transition-colors font-['Open_Sans',sans-serif]",
          className
        )}
      >
        <Phone className="w-4 h-4" />
        Nova chamada
      </button>
    )
  }

  if (voipState === "connected" || voipState === "muted") {
    return (
      <div className="flex gap-2">
        <button
          type="button"
          onClick={toggleMute}
          title={voipState === "muted" ? "Ativar microfone" : "Silenciar microfone"}
          aria-label={voipState === "muted" ? "Ativar microfone" : "Silenciar microfone"}
          className={cn(
            "h-11 flex items-center justify-center gap-2 px-3 rounded-lg border text-sm font-medium transition-colors font-['Open_Sans',sans-serif]",
            voipState === "muted"
              ? "border-status-warning/40 text-status-warning bg-status-warning/10 hover:bg-status-warning/20"
              : "border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-tertiary"
          )}
        >
          {voipState === "muted" ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          <span className="text-xs font-['Inter',sans-serif]">{formatTime(callDuration)}</span>
        </button>

        <button
          type="button"
          onClick={endCall}
          title="Encerrar chamada"
          aria-label="Encerrar chamada de voz"
          className="h-11 flex items-center justify-center gap-2 px-4 rounded-lg bg-status-error text-white text-sm font-medium hover:bg-status-error/90 transition-colors font-['Open_Sans',sans-serif]"
        >
          <PhoneOff className="w-4 h-4" />
          Encerrar
        </button>
      </div>
    )
  }

  if (voipState === "connecting") {
    return (
      <button
        type="button"
        disabled
        aria-label="Conectando chamada de voz..."
        className={cn(
          "h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-lia-border-subtle text-lia-text-secondary text-sm font-medium opacity-70 cursor-not-allowed font-['Open_Sans',sans-serif]",
          className
        )}
      >
        <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
        Conectando...
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={startCall}
      disabled={disabled}
      title="Iniciar chamada de voz pelo navegador"
      aria-label="Iniciar chamada de voz"
      className={cn(
        "h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-lia-border-subtle text-lia-text-primary text-sm font-medium hover:bg-lia-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none font-['Open_Sans',sans-serif]",
        className
      )}
    >
      <Volume2 className="w-4 h-4" />
      Ligar pelo navegador
    </button>
  )
}
