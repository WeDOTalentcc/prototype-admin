"use client"

/**
 * Onda 3 F5 → Onda 4 Agent E (2026-05-29) — wrapper thin sobre AssignAgentModal.
 *
 * Refatorado em Onda 4 Agent E (Rule of Three): a logica antes inline aqui
 * (~258 LOC) virou generic em src/components/shared/agents/AssignAgentModal.tsx.
 * Mantida API publica: (stageId, stageName, open, onClose, onAssigned).
 *
 * Backend canonical: POST /custom-agents/{agent_id}/deployments com
 * target_type='pipeline_stage'. Invalida queryKey ['agent-deployments'] em
 * sucesso.
 */
import React from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  AssignAgentModal,
  type AssignAgentPayload,
} from "@/components/shared/agents/AssignAgentModal"
import type { TriggerMode } from "@/types/agents/job-agent"

interface StageAgentTriggerModalProps {
  stageId: string
  stageName?: string
  open: boolean
  onClose: () => void
  onAssigned?: () => void
}

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("auth_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function postCreateDeployment(payload: {
  agent_id: string
  target_id: string
  trigger_mode: TriggerMode
  is_active: boolean
}): Promise<unknown> {
  // Backend canonical: POST /custom-agents/{agent_id}/deployments
  const res = await fetch(
    `/api/backend-proxy/custom-agents/${encodeURIComponent(payload.agent_id)}/deployments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        target_type: "pipeline_stage",
        target_id: payload.target_id,
        trigger_mode: payload.trigger_mode,
        is_active: payload.is_active,
      }),
    },
  )
  if (!res.ok) {
    let detail = ""
    try {
      const data = await res.json()
      detail = data?.detail || data?.message || ""
    } catch {
      /* ignore */
    }
    throw new Error(detail || `Failed to create deployment: ${res.status}`)
  }
  return res.json()
}

export function StageAgentTriggerModal({
  stageId,
  stageName,
  open,
  onClose,
  onAssigned,
}: StageAgentTriggerModalProps) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (payload: AssignAgentPayload) =>
      postCreateDeployment({
        agent_id: payload.agent_id,
        target_id: stageId,
        trigger_mode: payload.trigger_mode,
        is_active: payload.is_active,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agent-deployments"] })
    },
  })

  const handleSubmit = async (payload: AssignAgentPayload) => {
    await mutation.mutateAsync(payload)
  }

  return (
    <AssignAgentModal
      open={open}
      onClose={onClose}
      targetType="pipeline_stage"
      targetId={stageId}
      targetLabel={stageName}
      onSubmit={handleSubmit}
      onAssigned={onAssigned}
      testIdPrefix="stage-agent-trigger"
    />
  )
}
