"use client"

import { useState, useCallback } from "react"
import { Linkedin, Loader2, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

type PublishState = "idle" | "publishing" | "success" | "error"

interface LinkedInPublishButtonProps {
  jobId: string
  compact?: boolean
}

export function LinkedInPublishButton({
  jobId,
  compact = false,
}: LinkedInPublishButtonProps) {
  const [publishState, setPublishState] = useState<PublishState>("idle")
  const [errorMsg, setErrorMsg] = useState("")
  const queryClient = useQueryClient()

  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["linkedin-status"],
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/integrations/linkedin/status")
      if (!res.ok) return { connected: false }
      return res.json()
    },
    staleTime: 60_000,
  })

  const publishMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(
        `/api/backend-proxy/integrations/linkedin/publish/${jobId}`,
        { method: "POST" }
      )
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || body.error || `HTTP ${res.status}`)
      }
      return res.json()
    },
    onSuccess: () => {
      setPublishState("success")
      queryClient.invalidateQueries({ queryKey: ["linkedin-status"] })
    },
    onError: (err: Error) => {
      setPublishState("error")
      setErrorMsg(err.message)
    },
  })

  const handlePublish = useCallback(() => {
    setPublishState("publishing")
    setErrorMsg("")
    publishMutation.mutate()
  }, [publishMutation])

  if (statusLoading) return null
  if (!status?.connected) return null

  if (publishState === "success") {
    return (
      <Button variant="outline" size={compact ? "sm" : "default"} disabled>
        <CheckCircle className="h-4 w-4 mr-1.5 text-green-600" />
        Publicado no LinkedIn
      </Button>
    )
  }

  if (publishState === "error") {
    return (
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size={compact ? "sm" : "default"}
          onClick={handlePublish}
        >
          <AlertCircle className="h-4 w-4 mr-1.5 text-red-500" />
          Tentar novamente
        </Button>
        {errorMsg && (
          <span className="text-xs text-red-500 max-w-[200px] truncate">
            {errorMsg}
          </span>
        )}
      </div>
    )
  }

  return (
    <Button
      variant="outline"
      size={compact ? "sm" : "default"}
      onClick={handlePublish}
      disabled={publishState === "publishing"}
    >
      {publishState === "publishing" ? (
        <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
      ) : (
        <Linkedin className="h-4 w-4 mr-1.5" />
      )}
      {compact ? "LinkedIn" : "Publicar no LinkedIn"}
    </Button>
  )
}
