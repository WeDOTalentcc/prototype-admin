"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { startVoiceStreamSession } from "@/services/lia-api/voice-api"

interface VoiceStreamState {
  streamingEnabled: boolean
  wsSessionId: string | undefined
  wsToken: string | undefined
  voiceProvider: string | undefined
  voiceStrategy: string | undefined
  isInitializing: boolean
  error: string | undefined
}

export function useVoiceStream(companyId: string | undefined) {
  const [state, setState] = useState<VoiceStreamState>({
    streamingEnabled: false,
    wsSessionId: undefined,
    wsToken: undefined,
    voiceProvider: undefined,
    voiceStrategy: undefined,
    isInitializing: false,
    error: undefined,
  })

  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const initStreamSession = useCallback(async (
    candidateName?: string,
    jobTitle?: string,
  ) => {
    if (!companyId) return

    setState(prev => ({ ...prev, isInitializing: true, error: undefined }))

    const result = await startVoiceStreamSession(
      "",
      candidateName || "",
      jobTitle || "",
      companyId,
    )

    if (!mountedRef.current) return

    if (result.success && result.session_id) {
      setState({
        streamingEnabled: true,
        wsSessionId: result.session_id,
        wsToken: result.ws_token || undefined,
        voiceProvider: result.voice_provider,
        voiceStrategy: result.voice_strategy,
        isInitializing: false,
        error: undefined,
      })
    } else {
      setState({
        streamingEnabled: false,
        wsSessionId: undefined,
        wsToken: undefined,
        voiceProvider: result.voice_provider || undefined,
        voiceStrategy: undefined,
        isInitializing: false,
        error: result.error || undefined,
      })
    }
  }, [companyId])

  const resetSession = useCallback(() => {
    setState({
      streamingEnabled: false,
      wsSessionId: undefined,
      wsToken: undefined,
      voiceProvider: undefined,
      voiceStrategy: undefined,
      isInitializing: false,
      error: undefined,
    })
  }, [])

  return {
    ...state,
    initStreamSession,
    resetSession,
  }
}
