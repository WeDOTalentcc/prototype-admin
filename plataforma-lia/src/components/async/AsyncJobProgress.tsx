"use client"

import React, { useEffect, useRef, useState, useCallback } from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Progress } from"@/components/ui/progress"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Loader2, CheckCircle2, XCircle, RefreshCw } from"lucide-react"

// ─── Types ───────────────────────────────────────────────────────────────────

export interface AsyncJobResult {
  job_id: string
  status:"queued" |"processing" |"completed" |"failed"
  result?: Record<string, unknown>
  error?: string
}

interface WsMessage {
  type:"status" |"progress" |"completed" |"failed"
  job_id: string
  status: string
  progress?: number
  message?: string
  result?: Record<string, unknown>
  error?: string
  retrying?: boolean
}

interface AsyncJobProgressProps {
  jobId: string
  wsBaseUrl?: string
  pollIntervalMs?: number
  onComplete: (result: AsyncJobResult) => void
  onError: (error: string) => void
  label?: string
  showCard?: boolean
}

// ─── Component ───────────────────────────────────────────────────────────────

export function AsyncJobProgress({
  jobId,
  wsBaseUrl,
  pollIntervalMs = 3000,
  onComplete,
  onError,
  label ="Processando...",
  showCard = true,
}: AsyncJobProgressProps) {
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState("Aguardando início...")
  const [status, setStatus] = useState<"queued" |"processing" |"completed" |"failed">("queued")
  const [usePolling, setUsePolling] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const completedRef = useRef(false)

  // ── WebSocket ──────────────────────────────────────────────────────────────

  const connectWebSocket = useCallback(() => {
    if (completedRef.current) return

    const base = wsBaseUrl
      || process.env.NEXT_PUBLIC_WS_URL
      || `${window.location.protocol ==="https:" ?"wss:" :"ws:"}//${window.location.host}`
    const url = `${base}/ws/jobs/${jobId}`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setMessage("Conectado — aguardando progresso...")
        setUsePolling(false)
      }

      ws.onmessage = (event) => {
        try {
          const data: WsMessage = JSON.parse(event.data)
          handleUpdate(data)
        } catch {
          // ignore parse errors
        }
      }

      ws.onerror = () => {
        // WebSocket failed — fall back to polling
        setUsePolling(true)
      }

      ws.onclose = () => {
        if (!completedRef.current) {
          setUsePolling(true)
        }
      }
    } catch {
      setUsePolling(true)
    }
  }, [jobId, wsBaseUrl]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Polling fallback ───────────────────────────────────────────────────────

  const pollStatus = useCallback(async () => {
    if (completedRef.current) return

    try {
      const res = await fetch(`/api/backend-proxy/async/jobs/${jobId}/status`)
      if (!res.ok) return

      const data = await res.json()
      handleUpdate({
        type: data.status ==="completed" ?"completed" : data.status ==="failed" ?"failed" :"progress",
        job_id: jobId,
        status: data.status,
        progress: data.progress_percent ?? 0,
        message: data.message,
        result: data.result,
        error: data.error,
      })
    } catch {
      // ignore polling errors
    }

    if (!completedRef.current) {
      pollTimerRef.current = setTimeout(pollStatus, pollIntervalMs)
    }
  }, [jobId, pollIntervalMs]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Message handler ────────────────────────────────────────────────────────

  const handleUpdate = useCallback((data: WsMessage) => {
    if (completedRef.current) return

    if (data.progress !== undefined) setProgress(data.progress)
    if (data.message) setMessage(data.message)

    if (data.type ==="completed") {
      completedRef.current = true
      setProgress(100)
      setStatus("completed")
      setMessage("Concluído!")
      onComplete({ job_id: jobId, status:"completed", result: data.result })
    } else if (data.type ==="failed") {
      completedRef.current = true
      setStatus("failed")
      setMessage(data.error ||"Erro desconhecido")
      onError(data.error ||"Tarefa falhou")
    } else if (data.type ==="progress" || data.type ==="status") {
      setStatus("processing")
    }
  }, [jobId, onComplete, onError])

  // ── Effects ────────────────────────────────────────────────────────────────

  useEffect(() => {
    connectWebSocket()
    return () => {
      wsRef.current?.close()
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
    }
  }, [connectWebSocket])

  useEffect(() => {
    if (usePolling && !completedRef.current) {
      pollStatus()
    }
  }, [usePolling, pollStatus])

  // ── Render ─────────────────────────────────────────────────────────────────

  const content = (
    <div className="space-y-3" role="status" aria-live="polite" aria-label="Carregando...">
      {/* Header */}
      <div className="flex items-center justify-between gap-2" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
          {status ==="processing" || status ==="queued" ? (
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          ) : status ==="completed" ? (
            <CheckCircle2 className="h-4 w-4 text-status-success" />
          ) : (
            <XCircle className="h-4 w-4 text-status-error" />
          )}
          <span className="text-sm font-medium text-lia-text-primary">{label}</span>
        </div>

        <div className="flex items-center gap-2">
          {usePolling && status !=="completed" && status !=="failed" && (
            <Chip density="relaxed" variant="neutral" className="px-1.5 py-0 text-lia-text-secondary">
              <RefreshCw className="h-2.5 w-2.5 mr-1" />
              polling
            </Chip>
          )}
          <Chip
            variant="neutral"
            className={`text-micro px-1.5 py-0 ${
 status ==="completed"
                ?"text-status-success border-status-success/30"
                : status ==="failed"
                ?"text-status-error border-status-error/30"
                :"lia-text-secondary"
            }`}
          >
            {status ==="queued" ?"Na fila" :
             status ==="processing" ?"Processando" :
             status ==="completed" ?"Concluído" :"Falhou"}
          </Chip>
        </div>
      </div>

      {/* Progress bar */}
      <Progress value={progress} className="h-1.5" />

      {/* Message */}
      <p className="text-xs text-lia-text-secondary leading-relaxed">{message}</p>

      {/* Retry on failure */}
      {status ==="failed" && (
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          onClick={() => {
            completedRef.current = false
            setStatus("queued")
            setProgress(0)
            setMessage("Reconectando...")
            connectWebSocket()
          }}
        >
          <RefreshCw className="h-3 w-3 mr-1" />
          Tentar novamente
        </Button>
      )}
    </div>
  )

  if (!showCard) return content

  return (
    <Card className="border border-lia-border-subtle">
      <CardContent className="p-4">{content}</CardContent>
    </Card>
  )
}

export default AsyncJobProgress
