"use client"

import React, { useState } from "react"
import { Check, X, Clock, Loader2, ShieldCheck } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles, buttonStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { usePendingApprovals } from "@/hooks/agents"

interface ApprovalsListProps {
  onReviewed?: () => void
}

export function ApprovalsList({ onReviewed }: ApprovalsListProps) {
  const t = useTranslations('agents.customAgents')
  const tToast = useTranslations('agents.toast')
  const { approvals, isLoading, mutate } = usePendingApprovals()
  const [reviewingId, setReviewingId] = useState<string | null>(null)
  const [notes, setNotes] = useState<Record<string, string>>({})

  const handleReview = async (approvalId: string, action: "approve" | "reject") => {
    setReviewingId(approvalId)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/agent-approvals/${approvalId}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ action, notes: notes[approvalId] || null }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error" }))
        throw new Error(err.detail || tToast('reviewError'))
      }
      toast.success(action === "approve" ? tToast('agentApproved') : tToast('agentRejected'))
      mutate()
      onReviewed?.()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : tToast('reviewError'))
    } finally {
      setReviewingId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-xs text-lia-text-disabled">
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> {t('loadingApprovals')}
      </div>
    )
  }

  if (approvals.length === 0) {
    return (
      <div className={cn(cardStyles.flat, "p-4 text-center")}>
        <ShieldCheck className="w-6 h-6 text-lia-text-disabled mx-auto mb-1.5" />
        <p className="text-xs text-lia-text-secondary">{t('noApprovals')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 mb-2">
        <Clock className="w-3.5 h-3.5 text-amber-500" />
        <h4 className={cn(textStyles.subtitle, "text-xs font-semibold")}>
          {t('pendingApprovals', { count: approvals.length })}
        </h4>
      </div>

      {approvals.map((approval) => {
        const isReviewing = reviewingId === approval.id
        return (
          <div key={approval.id} className={cn(cardStyles.default, "p-3 space-y-2")}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold text-lia-text-primary">
                  {approval.agent_name || t('agentFallback')}
                </p>
                <p className="text-[10px] text-lia-text-disabled">
                  {t('requestedBy', { name: approval.requested_by })}
                </p>
              </div>
              <span className={cn(badgeStyles.warning, "text-[10px]")}>{t('pending')}</span>
            </div>

            <textarea
              value={notes[approval.id] || ""}
              onChange={(e) => setNotes({ ...notes, [approval.id]: e.target.value })}
              placeholder={t('reviewNotes')}
              rows={2}
              className="w-full text-xs border border-lia-border-subtle rounded-md px-2 py-1.5 bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30 resize-none"
              disabled={isReviewing}
            />

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleReview(approval.id, "approve")}
                disabled={isReviewing}
                className="flex-1 inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium bg-emerald-500 text-white hover:bg-emerald-600 transition-colors disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" /> {t('approveBtn')}
              </button>
              <button
                type="button"
                onClick={() => handleReview(approval.id, "reject")}
                disabled={isReviewing}
                className={cn(buttonStyles.outline, "flex-1 text-xs px-3 py-1.5")}
              >
                <X className="w-3.5 h-3.5 mr-1" /> {t('rejectBtn')}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
