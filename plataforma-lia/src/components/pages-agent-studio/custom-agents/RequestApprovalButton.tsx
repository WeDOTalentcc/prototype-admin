"use client"

import React, { useState } from "react"
import { ShieldCheck, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { buttonStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import type { CustomAgent } from "./types"

interface RequestApprovalButtonProps {
  agent: CustomAgent
  onRequested?: () => void
}

export function RequestApprovalButton({ agent, onRequested }: RequestApprovalButtonProps) {
  const [isRequesting, setIsRequesting] = useState(false)

  const handleRequest = async () => {
    setIsRequesting(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/request-approval`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro" }))
        throw new Error(err.detail || "Erro ao solicitar aprovacao")
      }
      toast.success("Aprovacao solicitada", "O administrador sera notificado.")
      onRequested?.()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao solicitar aprovacao")
    } finally {
      setIsRequesting(false)
    }
  }

  if (agent.status !== "draft") return null

  return (
    <button
      type="button"
      onClick={handleRequest}
      disabled={isRequesting}
      className={cn(buttonStyles.primary, "text-xs px-3 py-1.5 inline-flex items-center gap-1.5")}
    >
      {isRequesting ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : (
        <ShieldCheck className="w-3.5 h-3.5" />
      )}
      Solicitar aprovacao
    </button>
  )
}
