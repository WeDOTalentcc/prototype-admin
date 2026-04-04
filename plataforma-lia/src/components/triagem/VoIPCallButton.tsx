"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Phone, PhoneOff, Mic, MicOff, Loader2, Volume2, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Device as TwilioDevice, Call as TwilioCall } from "@twilio/voice-sdk"

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

let TwilioDeviceClass: typeof TwilioDevice | null = null
let TwilioCallClass: typeof TwilioCall | null = null

async function loadTwilioSDK(): Promise<{ Device: typeof TwilioDevice; Call: typeof TwilioCall }> {
  if (TwilioDeviceClass && TwilioCallClass) {
    return { Device: TwilioDeviceClass, Call: TwilioCallClass }
  }
  const mod = await import("@twilio/voice-sdk")
  TwilioDeviceClass = mod.Device
  TwilioCallClass = mod.Call
  return { Device: mod.Device, Call: mod.Call }
}

export function VoIPCallButton({
  token,
  disabled = false,
  className,
  onCallStarted,
  onCallEnded,
  onError,
}: VoIPCallButtonProps) {
  const [voipState, setVoIPState] = useState<VoIPState>("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [callDuration, setCallDuration] = useState(0)
  const deviceRef = useRef<TwilioDevice | null>(null)
  const callRef = useRef<TwilioCall | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const voipTokenRef = useRef<string | null>(null)
  const voipSessionIdRef = useRef<string | null>(null)
  const voipAvailableRef = useRef<boolean | null>(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      clearTimer()
      if (callRef.current) {
        try {
          callRef.current.disconnect()
        } catch {}
      }
      if (deviceRef.current) {
        try {
          deviceRef.current.destroy()
        } catch {}
      }
    }
  }, [clearTimer])

  const fetchVoIPToken = useCallback(async (): Promise<string | null> => {
    if (voipTokenRef.current) return voipTokenRef.current
    try {
      const res = await fetch(`/api/backend-proxy/triagem/${token}/voip-start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const msg = data.detail || "Não foi possível iniciar sessão VoIP"
        setErrorMessage(msg)
        onError?.(msg)
        return null
      }
      const data = await res.json()
      if (!data.voip_available || !data.token) {
        voipAvailableRef.current = false
        setVoIPState("unavailable")
        return null
      }
      voipAvailableRef.current = true
      voipTokenRef.current = data.token
      voipSessionIdRef.current = data.session_id
      return data.token
    } catch {
      const msg = "Erro de rede ao obter token VoIP"
      setErrorMessage(msg)
      onError?.(msg)
      return null
    }
  }, [token, onError])

  const startCall = useCallback(async () => {
    if (disabled || voipState !== "idle") return

    setVoIPState("connecting")
    setErrorMessage(null)
    setCallDuration(0)

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      const msg = "Microfone não disponível. Verifique as permissões do navegador."
      setErrorMessage(msg)
      setVoIPState("error")
      onError?.(msg)
      return
    }

    const accessToken = await fetchVoIPToken()
    if (!accessToken) {
      setVoIPState(voipAvailableRef.current === false ? "unavailable" : "error")
      return
    }

    let DeviceClass: typeof TwilioDevice
    let CallClass: typeof TwilioCall
    try {
      const sdk = await loadTwilioSDK()
      DeviceClass = sdk.Device
      CallClass = sdk.Call
    } catch {
      const msg = "Não foi possível carregar o sistema de chamada VoIP."
      setErrorMessage(msg)
      setVoIPState("error")
      onError?.(msg)
      return
    }

    try {
      const device = new DeviceClass(accessToken, {
        codecPreferences: [CallClass.Codec.Opus, CallClass.Codec.PCMU],
        logLevel: "error",
      })
      deviceRef.current = device

      device.on("error", (err: { message?: string }) => {
        const errMsg = err?.message || "Erro na chamada VoIP"
        setErrorMessage(errMsg)
        setVoIPState("error")
        clearTimer()
        onError?.(errMsg)
      })

      const voipSessionId = voipSessionIdRef.current || ""
      const call = await device.connect({
        params: {
          session_id: voipSessionId,
          identity: `candidate_${voipSessionId.slice(0, 8)}`,
        },
      })
      callRef.current = call

      call.on("accept", () => {
        setVoIPState("connected")
        onCallStarted?.()
        timerRef.current = setInterval(() => {
          setCallDuration((prev) => prev + 1)
        }, 1000)
      })

      call.on("disconnect", () => {
        setVoIPState("ended")
        clearTimer()
        onCallEnded?.()
        deviceRef.current?.destroy()
        deviceRef.current = null
        callRef.current = null
      })

      call.on("cancel", () => {
        setVoIPState("idle")
        clearTimer()
        deviceRef.current?.destroy()
        deviceRef.current = null
        callRef.current = null
      })

      call.on("error", (err: { message?: string }) => {
        const errMsg = err?.message || "Erro na chamada"
        setErrorMessage(errMsg)
        setVoIPState("error")
        clearTimer()
        onError?.(errMsg)
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao iniciar chamada VoIP"
      setErrorMessage(msg)
      setVoIPState("error")
      onError?.(msg)
    }
  }, [disabled, voipState, fetchVoIPToken, clearTimer, onCallStarted, onCallEnded, onError])

  const endCall = useCallback(() => {
    if (callRef.current) {
      try {
        callRef.current.disconnect()
      } catch {}
    }
    clearTimer()
    setVoIPState("ended")
    onCallEnded?.()
  }, [clearTimer, onCallEnded])

  const toggleMute = useCallback(() => {
    if (!callRef.current) return
    const isMuted = callRef.current.isMuted()
    callRef.current.mute(!isMuted)
    setVoIPState(isMuted ? "connected" : "muted")
  }, [])

  const reset = useCallback(() => {
    clearTimer()
    if (deviceRef.current) {
      try {
        deviceRef.current.destroy()
      } catch {}
      deviceRef.current = null
    }
    callRef.current = null
    voipTokenRef.current = null
    voipSessionIdRef.current = null
    setVoIPState("idle")
    setErrorMessage(null)
    setCallDuration(0)
  }, [clearTimer])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0")
    const s = (seconds % 60).toString().padStart(2, "0")
    return `${m}:${s}`
  }

  if (voipState === "unavailable") {
    return (
      <button
        type="button"
        disabled
        title="Chamada VoIP não disponível neste momento"
        aria-label="Chamada VoIP indisponível"
        className={cn(
          "h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-lia-border-subtle text-lia-text-disabled text-sm font-medium opacity-50 cursor-not-allowed font-['Open_Sans',sans-serif]",
          className
        )}
      >
        <WifiOff className="w-4 h-4" />
        VoIP indisponível
      </button>
    )
  }

  if (voipState === "error") {
    return (
      <div className="flex flex-col gap-1.5">
        <button
          type="button"
          onClick={reset}
          title="Tentar novamente"
          aria-label="Tentar chamada VoIP novamente"
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
        title="Iniciar nova chamada VoIP"
        aria-label="Iniciar nova chamada VoIP"
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
          aria-label="Encerrar chamada VoIP"
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
        aria-label="Conectando chamada VoIP..."
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
      title="Iniciar chamada de voz pelo navegador (VoIP)"
      aria-label="Iniciar chamada de voz VoIP"
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
