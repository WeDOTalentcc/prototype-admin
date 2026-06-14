"use client"

/**
 * UpgradeRequestModal — substitui mailto: como CTA "Falar com Account Manager"
 * no modelo pay-first sales-led canonical WeDOTalent.
 *
 * Audit harness 2026-05-23: antes, toast quota → mailto:sucesso@... abria o
 * client de email do user, sem captura estruturada. Agora form modal in-app
 * envia POST /upgrade-requests com payload canonical, backend dispara
 * Hubspot Deal (se token configurado) + notificação pra equipe AM.
 *
 * Pré-requisitos backend:
 *   - POST /api/v1/upgrade-requests (criado canonical 2026-05-23)
 *   - HUBSPOT_ACCESS_TOKEN no Replit Secrets (opcional — fallback funciona sem)
 */
import React, { useState } from "react"
import { Loader2, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { toast } from "@/lib/toast"

export interface UpgradeRequestContext {
  /** Recurso que disparou (custom_agents, sourcing_agents, etc) */
  resource: string
  /** Label PT-BR pra UI (ex: "agentes customizados") */
  resourceLabel?: string
  /** Uso atual quando solicitou */
  current: number
  /** Limit do plano (-1 = unlimited) */
  limit: number
  /** Plano atual */
  currentPlan: string
}

export interface UpgradeRequestModalProps {
  isOpen: boolean
  onClose: () => void
  context: UpgradeRequestContext | null
}

const PLAN_OPTIONS = ["starter", "pro", "business", "enterprise"] as const

export function UpgradeRequestModal({ isOpen, onClose, context }: UpgradeRequestModalProps) {
  const t = useTranslations("agents.studio.upgradeRequest")
  const [requestedPlan, setRequestedPlan] = useState<string>("")
  const [notes, setNotes] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!context) return
    setIsSubmitting(true)
    try {
      const res = await fetch("/api/backend-proxy/upgrade-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resource: context.resource,
          current: context.current,
          limit: context.limit,
          current_plan: context.currentPlan,
          requested_plan: requestedPlan || null,
          notes: notes.trim() || null,
        }),
      })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = (await res.json()) as { expected_response_hours: number }
      toast.success(
        t("successTitle"),
        t("successDesc", { hours: data.expected_response_hours }),
      )
      setRequestedPlan("")
      setNotes("")
      onClose()
    } catch (e) {
      toast.error(
        t("errorTitle"),
        t("errorDesc"),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!context) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md" data-testid="upgrade-request-modal">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-graphite" aria-hidden="true" />
            <DialogTitle>{t("title")}</DialogTitle>
          </div>
          <DialogDescription>
            {t("description", {
              resource: context.resourceLabel || context.resource,
              current: context.current,
              limit: context.limit,
              plan: context.currentPlan,
            })}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <div>
            <label
              htmlFor="upgrade-requested-plan"
              className="block text-xs font-medium text-lia-text-primary mb-1"
            >
              {t("requestedPlanLabel")}
            </label>
            <select
              id="upgrade-requested-plan"
              value={requestedPlan}
              onChange={(e) => setRequestedPlan(e.target.value)}
              className="w-full rounded-md border border-lia-border-subtle bg-lia-bg-primary px-2 py-1.5 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
              disabled={isSubmitting}
            >
              <option value="">{t("requestedPlanPlaceholder")}</option>
              {PLAN_OPTIONS.map((plan) => (
                <option key={plan} value={plan} disabled={plan === context.currentPlan}>
                  {t(`plans.${plan}`)}
                  {plan === context.currentPlan ? ` (${t("currentSuffix")})` : ""}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-lia-text-muted mt-0.5">
              {t("requestedPlanHelp")}
            </p>
          </div>

          <div>
            <label
              htmlFor="upgrade-notes"
              className="block text-xs font-medium text-lia-text-primary mb-1"
            >
              {t("notesLabel")}
            </label>
            <textarea
              id="upgrade-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              maxLength={2000}
              placeholder={t("notesPlaceholder")}
              className="w-full rounded-md border border-lia-border-subtle bg-lia-bg-primary px-2 py-1.5 text-sm text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30 resize-none"
              disabled={isSubmitting}
            />
          </div>

          <p className="text-[10px] text-lia-text-secondary bg-lia-bg-secondary rounded-md px-2 py-1.5">
            {t("disclosure")}
          </p>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            {t("cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="gap-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
            data-testid="upgrade-request-submit"
          >
            {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />}
            {t("submit")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
