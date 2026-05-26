"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { HubHeader, HubLoadingState } from "./_shared"
import { Webhook as WebhookIcon, Plus, Trash2, Send, Loader2, Copy, CheckCircle2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { textStyles, cardStyles, buttonStyles, badgeStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { useWebhooks } from "@/hooks/agents"
import { type Webhook } from "@/components/pages-agent-studio/custom-agents/webhook-types"
import { useWebhookEventTypes, flattenEventTypes, type FlatWebhookEvent } from "@/hooks/webhooks/use-webhook-event-types"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

export function WebhooksManager() {
  const t = useTranslations("settings.webhooks")
  const { webhooks, isLoading, mutate } = useWebhooks()
  // Sprint 5 catalogos dinamicos: substituiu WEBHOOK_EVENTS hardcoded.
  // includeMaster=true pra trazer eventos curados WeDOTalent + customs.
  const { eventTypes: rawEventTypes } = useWebhookEventTypes({ includeMaster: true })
  const availableEvents: FlatWebhookEvent[] = flattenEventTypes(rawEventTypes).filter((e) => !e.deprecated)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState("")
  const [newUrl, setNewUrl] = useState("")
  const [newEvents, setNewEvents] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [showSecret, setShowSecret] = useState<{ id: string; secret: string } | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)

  const eventLabel = (event: string): string => {
    // Sprint 5: preferir label canonical do catalogo dinamico per-tenant.
    const dyn = availableEvents.find((e) => e.event_type === event)
    if (dyn?.label) return dyn.label
    // Fallback i18n (compat com tradutoes ja existentes em settings.webhooks.eventLabels.*).
    const key = event.replace(/\./g, "_")
    try {
      return t(`eventLabels.${key}` as never)
    } catch {
      return event
    }
  }

  const handleCreate = async () => {
    if (!newName.trim() || !newUrl.trim() || newEvents.length === 0) return
    // P2-W3-INT-5: validacao HTTPS no frontend — feedback imediato antes de hit no backend
    if (!newUrl.trim().startsWith("https://")) {
      toast.error(t("urlMustBeHttps") || "A URL deve comecar com https://")
      return
    }
    setSubmitting(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await apiFetch("/api/backend-proxy/webhooks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ name: newName, url: newUrl, events: newEvents }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: t("createGenericError") }))
        throw new Error(err.detail || t("createGenericErrorMessage"))
      }
      const created: Webhook = await res.json()
      toast.success(t("createdToast", { name: newName }), t("createdToastDesc"))
      if (created.secret) {
        setShowSecret({ id: created.id, secret: created.secret })
      }
      setCreating(false)
      setNewName("")
      setNewUrl("")
      setNewEvents([])
      mutate()
      notifyChatOfSettingsUpdate({
        actionId: "create_webhook",
        section: "webhooks",
        field: newName,
        value: newEvents.length,
      })
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t("createError"))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(t("deleteConfirm", { name }))) return
    try {
      const token = localStorage.getItem("auth_token")
      const res = await apiFetch(`/api/backend-proxy/webhooks/${id}`, {
        method: "DELETE",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok && res.status !== 204) throw new Error(t("createGenericError"))
      toast.success(t("deletedToast"))
      mutate()
      notifyChatOfSettingsUpdate({
        actionId: "delete_webhook",
        section: "webhooks",
        field: name,
      })
    } catch {
      toast.error(t("deleteError"))
    }
  }

  const handleTest = async (id: string) => {
    setTestingId(id)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await apiFetch(`/api/backend-proxy/webhooks/${id}/test`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) throw new Error(t("createGenericError"))
      toast.success(t("testSentToast"), t("testSentDesc"))
      setTimeout(() => mutate(), 3000)
      notifyChatOfSettingsUpdate({
        actionId: "test_webhook",
        section: "webhooks",
        field: id,
      })
    } catch {
      toast.error(t("testError"))
    } finally {
      setTestingId(null)
    }
  }

  const toggleEvent = (event: string) => {
    setNewEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event],
    )
  }

  const copySecret = async (secret: string) => {
    try {
      await navigator.clipboard.writeText(secret)
      toast.success(t("secretCopied"))
    } catch {
      toast.error(t("copyError"))
    }
  }

  return (
    <div className="space-y-4" data-testid="webhooks-manager">
      <HubHeader title={t("title")} description={t("description")}>
        <Button onClick={() => setCreating(true)} className={buttonStyles.primary} data-testid="webhooks-create-button">
          <Plus className="w-4 h-4 mr-1" /> {t("newWebhook")}
        </Button>
      </HubHeader>

      {isLoading && (
        <div className="flex items-center gap-2 py-8 justify-center text-xs text-lia-text-disabled">
          <HubLoadingState variant="inline" message={t("loading")} />
        </div>
      )}

      {!isLoading && webhooks.length === 0 && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <WebhookIcon className="w-10 h-10 text-lia-text-disabled mx-auto mb-2" />
            <p className={textStyles.subtitle}>{t("noneConfigured")}</p>
            <p className="text-xs text-lia-text-disabled mt-1">
              {t("noneHint")}
            </p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2" data-testid="webhooks-list">
        {webhooks.map((wh) => (
          <Card key={wh.id} className={cardStyles.default} data-testid={`webhook-row-${wh.id}`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-lia-text-primary">{wh.name}</span>
                    <Chip variant="neutral" muted className={wh.is_active ? badgeStyles.success : badgeStyles.default}>
                      {wh.is_active ? t("active") : t("paused")}
                    </Chip>
                    {wh.last_status_code && (
                      <Chip variant="neutral" muted
                        className={
                          wh.last_status_code >= 200 && wh.last_status_code < 300
                            ? badgeStyles.success
                            : badgeStyles.error
                        }
                      >
                        {t("lastStatus", { code: wh.last_status_code })}
                      </Chip>
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary truncate font-mono">{wh.url}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {wh.events.map((e) => (
                      <span key={e} className={cn(badgeStyles.default, "text-[10px]")}>
                        {eventLabel(e)}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-lia-text-disabled">
                    <span>{t("deliveries", { count: wh.total_deliveries })}</span>
                    {wh.total_failures > 0 && (
                      <span className="text-status-error">{t("failures", { count: wh.total_failures })}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleTest(wh.id)}
                    disabled={testingId === wh.id}
                    data-testid={`webhook-test-button-${wh.id}`}
                  >
                    {testingId === wh.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(wh.id, wh.name)} data-testid={`webhook-delete-button-${wh.id}`}>
                    <Trash2 className="w-3.5 h-3.5 text-status-error" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create dialog */}
      <Dialog open={creating} onOpenChange={(v) => !v && setCreating(false)}>
        <DialogContent className="sm:max-w-lg" data-testid="webhook-create-modal">
          <DialogHeader>
            <DialogTitle>{t("newWebhook")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t("name")}</label>
              <Input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder={t("namePlaceholder")}
                data-field="name"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t("urlLabel")}</label>
              <Input
                type="text"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder={t("urlPlaceholder")}
                data-field="url"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-2 block">{t("events")}</label>
              <div className="space-y-1.5" data-field="events">
                {availableEvents.length === 0 && (
                  <p className="text-xs text-lia-text-disabled italic">{t("loading")}</p>
                )}
                {availableEvents.map((evt) => (
                  <label key={evt.event_type} className="flex items-center gap-2 text-xs cursor-pointer">
                    <Checkbox
                      checked={newEvents.includes(evt.event_type)}
                      onCheckedChange={() => toggleEvent(evt.event_type)}
                      data-toggle={`events.${evt.event_type}`}
                    />
                    <span className="text-lia-text-primary">{eventLabel(evt.event_type)}</span>
                    <span className="text-lia-text-disabled font-mono text-[10px]">({evt.event_type})</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreating(false)} data-testid="webhook-create-cancel">{t("cancel")}</Button>
            <Button
              onClick={handleCreate}
              disabled={submitting || !newName || !newUrl || newEvents.length === 0}
              className={buttonStyles.primary}
              data-testid="webhook-create-submit"
            >
              {submitting ? t("creating") : t("create")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Show secret dialog (one-time display) */}
      <Dialog open={!!showSecret} onOpenChange={(v) => !v && setShowSecret(null)}>
        <DialogContent className="sm:max-w-lg" data-testid="webhook-secret-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-status-success" />
              {t("createdTitle")}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className={cn(cardStyles.flat, "p-3 border border-status-warning/30")}>
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-status-warning mt-0.5" />
                <div className="text-xs">
                  <p className="font-semibold text-lia-text-primary mb-1">{t("saveSecretWarning")}</p>
                  <p className="text-lia-text-secondary">
                    {t("secretWarningDesc")}
                  </p>
                </div>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">{t("secretLabel")}</label>
              <div className="flex gap-1">
                <Input
                  type="text"
                  readOnly
                  value={showSecret?.secret || ""}
                  className="flex-1 bg-lia-bg-tertiary font-mono"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => showSecret && copySecret(showSecret.secret)}
                  data-testid="webhook-secret-copy"
                >
                  <Copy className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowSecret(null)} className={buttonStyles.primary} data-testid="webhook-secret-dismiss">
              {t("understood")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
