"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
/**
 * LinkedInConnectModal — modal for configuring LinkedIn integration credentials.
 *
 * Allows the recruiter to paste their LinkedIn access_token and org ID manually
 * (no OAuth dance). Credentials are stored encrypted server-side.
 *
 * Rules of Hooks discipline: all hooks declared before any conditional returns.
 */

import React, { useCallback, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { CheckCircle, XCircle, Loader2, ExternalLink } from "lucide-react"
import { cn } from "@/lib/utils"

// ── Types ────────────────────────────────────────────────────────────────────

interface LinkedInStatus {
  connected: boolean
  status: "connected" | "not_configured"
  org_id: string | null
  posting_type: "job_posting" | "social_only" | null
}

interface LinkedInConnectModalProps {
  isOpen: boolean
  onClose: () => void
  onConnected?: () => void
}

// ── Component ────────────────────────────────────────────────────────────────

export function LinkedInConnectModal({
  isOpen,
  onClose,
  onConnected,
}: LinkedInConnectModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('linkedin-connect', isOpen)

  // ── All hooks before any conditional return (Rules of Hooks) ──────────────
  const [status, setStatus] = useState<LinkedInStatus | null>(null)
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [statusError, setStatusError] = useState<string | null>(null)

  const [accessToken, setAccessToken] = useState("")
  const [orgId, setOrgId] = useState("")
  const [postingType, setPostingType] = useState<"job_posting" | "social_only">(
    "job_posting",
  )

  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
  } | null>(null)

  const [disconnecting, setDisconnecting] = useState(false)

  // ── Fetch status ──────────────────────────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    setLoadingStatus(true)
    setStatusError(null)
    try {
      const res = await fetch("/api/backend-proxy/integrations/linkedin/status")
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: LinkedInStatus = await res.json()
      setStatus(data)
      if (data.connected) {
        setOrgId(data.org_id || "")
        setPostingType(data.posting_type || "job_posting")
      }
    } catch (e) {
      setStatusError(e instanceof Error ? e.message : "Erro ao carregar status")
    } finally {
      setLoadingStatus(false)
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      fetchStatus()
      // Reset transient UI state when modal opens
      setSaveSuccess(false)
      setSaveError(null)
      setTestResult(null)
      setAccessToken("")
    }
  }, [isOpen, fetchStatus])

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    // Allow empty token when already connected (update only org_id/posting_type)
    if (!accessToken.trim() && !status?.connected) {
      setSaveError("Cole o access_token do LinkedIn antes de salvar.")
      return
    }
    if (!orgId.trim() || !/^\d+$/.test(orgId.trim())) {
      setSaveError("Organization ID deve ser numérico (ex: 12345678).")
      return
    }
    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)
    try {
      const res = await fetch("/api/backend-proxy/integrations/linkedin/connect", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          access_token: accessToken.trim(),
          org_id: orgId.trim(),
          posting_type: postingType,
        }),
      })
      const data = await res.json()
      if (!res.ok || !data.success) {
        setSaveError(data.detail || data.error || `Erro ${res.status}`)
      } else {
        setSaveSuccess(true)
        setAccessToken("") // clear sensitive field
        setStatus({ connected: true, status: "connected", org_id: orgId.trim(), posting_type: postingType })
        onConnected?.()
      }
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Erro ao salvar credenciais")
    } finally {
      setSaving(false)
    }
  }, [accessToken, orgId, postingType, onConnected])

  const handleTestPost = useCallback(async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await fetch("/api/backend-proxy/integrations/linkedin/test-post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: null }),
      })
      const data = await res.json()
      setTestResult({
        success: data.success,
        message: data.message || (data.success ? "Post de teste enviado!" : "Falha no teste."),
      })
    } catch (e) {
      setTestResult({
        success: false,
        message: e instanceof Error ? e.message : "Erro ao testar conexão",
      })
    } finally {
      setTesting(false)
    }
  }, [])

  const handleDisconnect = useCallback(async () => {
    if (!window.confirm("Desconectar o LinkedIn? As credenciais serão removidas.")) return
    setDisconnecting(true)
    try {
      const res = await fetch("/api/backend-proxy/integrations/linkedin/disconnect", {
        method: "DELETE",
      })
      if (res.ok) {
        setStatus({ connected: false, status: "not_configured", org_id: null, posting_type: null })
        setOrgId("")
        setAccessToken("")
        setSaveSuccess(false)
        onConnected?.()
      }
    } catch (_e) {
      // ignore
    } finally {
      setDisconnecting(false)
    }
  }, [onConnected])

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-lg font-semibold">LinkedIn Jobs</span>
            {status?.connected && (
              <span className="inline-flex items-center gap-1 text-xs text-status-success bg-status-success/10 px-2 py-0.5 rounded-full">
                <CheckCircle className="h-3 w-3" />
                Conectado
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            Configure suas credenciais do LinkedIn para publicar vagas automaticamente.
            {!status?.connected && (
              <span className="block mt-1 text-xs">
                Vá ao LinkedIn Developer Portal &gt; seu app &gt; Auth &gt; OAuth 2.0 Tools &gt; gere um token com scope <code className="bg-lia-bg-tertiary px-1 rounded">w_organization_social</code>.
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        {loadingStatus ? (
          <HubLoadingState />
        ) : statusError ? (
          <HubErrorState onRetry={fetchStatus} />
        ) : (
          <div className="space-y-5 pt-2">
            {/* Connection status banner */}
            {status?.connected && (
              <div className="flex items-start gap-3 p-3 bg-status-success/10 border border-status-success/20 rounded-lg text-sm">
                <CheckCircle className="h-4 w-4 text-status-success mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-status-success">Conectado</p>
                  <p className="text-lia-text-secondary">
                    Org ID: <span className="font-mono">{status.org_id}</span> ·{" "}
                    {status.posting_type === "job_posting" ? "Job Posting + Social" : "Apenas social"}
                  </p>
                </div>
              </div>
            )}

            {/* Access Token field */}
            <div className="space-y-1.5">
              <Label htmlFor="li-access-token">
                Access Token{" "}
                <span className="text-lia-text-tertiary text-xs font-normal">
                  (LinkedIn Developer App)
                </span>
              </Label>
              <Textarea
                id="li-access-token"
                placeholder={status?.connected ? "Token salvo — cole aqui só para substituir" : "AQVJ..."}
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                rows={3}
                className="font-mono text-xs resize-none"
                aria-describedby="li-access-token-hint"
              />
              <p id="li-access-token-hint" className="text-xs text-lia-text-tertiary">
                {status?.connected
                  ? "\u2705 Token salvo no servidor (criptografado). Deixe em branco para manter ou cole um novo para substituir."
                  : "Cole o access_token gerado no LinkedIn Developer Portal (menu OAuth 2.0 Tools > Generate token com scope w_organization_social)."}
              </p>
            </div>

            {/* Organization ID */}
            <div className="space-y-1.5">
              <Label htmlFor="li-org-id">LinkedIn Organization ID</Label>
              <Input
                id="li-org-id"
                placeholder="12345678"
                value={orgId}
                onChange={(e) => setOrgId(e.target.value.replace(/\D/g, ""))}
                type="text"
                inputMode="numeric"
                className="font-mono"
              />
              <p className="text-xs text-lia-text-tertiary">
                ID numérico da organização (só números, ex: 7708382). Não confundir com o Client ID do app (alfanumérico).{" "}
                <a
                  href="https://www.linkedin.com/company/admin/overview/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 text-lia-text-secondary hover:underline"
                >
                  Encontrar na LinkedIn Admin <ExternalLink className="h-3 w-3" />
                </a>
              </p>
            </div>

            {/* Posting type */}
            <div className="space-y-2">
              <Label>Tipo de publicação</Label>
              <RadioGroup
                value={postingType}
                onValueChange={(v) => setPostingType(v as "job_posting" | "social_only")}
                className="space-y-1"
              >
                <div className="flex items-start gap-2">
                  <RadioGroupItem value="job_posting" id="pt-job" className="mt-0.5" />
                  <Label htmlFor="pt-job" className="cursor-pointer font-normal">
                    <span className="font-medium">Job Posting (API oficial)</span>
                    <br />
                    <span className="text-xs text-lia-text-tertiary">
                      Cria uma vaga estruturada no LinkedIn Jobs + post no feed
                    </span>
                  </Label>
                </div>
                <div className="flex items-start gap-2">
                  <RadioGroupItem value="social_only" id="pt-social" className="mt-0.5" />
                  <Label htmlFor="pt-social" className="cursor-pointer font-normal">
                    <span className="font-medium">Social post apenas</span>
                    <br />
                    <span className="text-xs text-lia-text-tertiary">
                      Apenas post no feed da empresa com link para o portal
                    </span>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Error / Success feedback */}
            {saveError && (
              <div className="flex items-start gap-2 text-sm text-status-error">
                <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{saveError}</span>
              </div>
            )}
            {saveSuccess && (
              <div className="flex items-start gap-2 text-sm text-status-success">
                <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>Credenciais salvas com sucesso!</span>
              </div>
            )}

            {/* Test result */}
            {testResult && (
              <div
                className={cn(
                  "flex items-start gap-2 text-sm p-2.5 rounded-lg border",
                  testResult.success
                    ? "text-status-success bg-status-success/10 border-status-success/20"
                    : "text-status-error bg-status-error/10 border-status-error/20",
                )}
              >
                {testResult.success ? (
                  <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
              <div className="flex gap-2">
                <Button onClick={handleSave} disabled={saving} size="sm">
                  {saving && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />}
                  {status?.connected ? "Atualizar credenciais" : "Salvar credenciais"}
                </Button>
                {status?.connected && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleTestPost}
                    disabled={testing}
                  >
                    {testing && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />}
                    Testar conexão
                  </Button>
                )}
              </div>
              <div className="flex gap-2">
                {status?.connected && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDisconnect}
                    disabled={disconnecting}
                    className="text-status-error hover:text-status-error hover:bg-status-error/10"
                  >
                    {disconnecting && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />}
                    Desconectar
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={onClose}>
                  Fechar
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
