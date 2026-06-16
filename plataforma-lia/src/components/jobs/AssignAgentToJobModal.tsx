"use client"

/**
 * Onda 3 F3 → Onda 4 Agent E (2026-05-29) — wrapper thin sobre AssignAgentModal.
 *
 * Refatorado em Onda 4 Agent E (Rule of Three): a logica antes inline aqui
 * (~232 LOC) virou generic em src/components/shared/agents/AssignAgentModal.tsx.
 * Este arquivo mantem a API publica que o JobAgentsTab ja consome —
 * (jobId, jobTitle, open, onClose, onAssigned).
 */
import React from "react"
import { useAttachJobAgent } from "@/hooks/agents/use-job-agents"
import {
  AssignAgentModal,
  type AssignAgentPayload,
} from "@/components/shared/agents/AssignAgentModal"

interface AssignAgentToJobModalProps {
  jobId: string
  jobTitle?: string
  open: boolean
  onClose: () => void
  onAssigned?: () => void
}

export function AssignAgentToJobModal({
  jobId,
  jobTitle,
  open,
  onClose,
  onAssigned,
}: AssignAgentToJobModalProps) {
  const attachAgent = useAttachJobAgent(jobId)

  const handleSubmit = async (payload: AssignAgentPayload) => {
    await attachAgent.mutateAsync({
      agent_id: payload.agent_id,
      trigger_mode: payload.trigger_mode,
      schedule_cron: payload.schedule_cron,
      is_active: payload.is_active,
    })
  }

  return (
    <AssignAgentModal
      open={open}
      onClose={onClose}
      targetType="job"
      targetId={jobId}
      targetLabel={jobTitle}
      onSubmit={handleSubmit}
      onAssigned={onAssigned}
      testIdPrefix="assign-agent-to-job"
    />
  )
}
