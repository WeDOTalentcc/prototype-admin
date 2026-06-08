"use client"

import { useCallback, useState, useEffect } from "react"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import {
  CheckCircle2,
  Clock,
  ExternalLink,
  Settings,
  Zap,
  Loader2,
  AlertCircle,
  Chrome,
  ShieldCheck,
  Key,
  Mic,
  Info,
  Save,
  Send,
} from "lucide-react"
import type { Integration } from "./integration-data"
import { ApiKeyConfigForm } from "./ApiKeyConfigForm"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

const AI_PROVIDER_IDS = ["gemini", "claude", "openai", "deepseek"]

interface ProviderConfigData {
  api_key?: string
  model?: string
  is_active?: boolean
}

interface LLMConfigData {
  company_id: string
  primary_provider: string
  fallback_order: string[]
  providers: Record<string, ProviderConfigData>
  routing: Record<string, string>
  is_active: boolean
  // W2-012-B (2026-05-23): LGPD Art 33 per-tenant region pinning
  region?: string | null
}

interface IntegrationDetailModalProps {
  integration: Integration | null
  open: boolean
  onClose: () => void
  googleStatus?: "idle" | "loading" | "connected" | "error"
  microsoftStatus?: "loading" | "connected" | "not_configured"
  teamsStatus?: "loading" | "configured" | "not_configured"
  onConnectGoogle?: () => void
  errorMsg?: string | null
  llmConfig?: LLMConfigData | null
  onConfigSaved?: () => void
}

export function IntegrationDetailModal({
  integration,
  open,
  onClose,
  googleStatus = "idle",
  microsoftStatus = "not_configured",
  teamsStatus = "not_configured",
  onConnectGoogle,
  errorMsg,
  llmConfig,
  onConfigSaved,
}: IntegrationDetailModalProps) {
  const [teamsWebhookInput, setTeamsWebhookInput] = useState("")
  const [teamsWebhookMasked, setTeamsWebhookMasked] = useState<string | null>(null)
  const [teamsWebhookSource, setTeamsWebhookSource] = useState<"db" | "env" | "none">("none")
  const [teamsSaveLoading, setTeamsSaveLoading] = useState(false)
  const [teamsSaveMsg, setTeamsSaveMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [teamsTestLoading, setTeamsTestLoading] = useState(false)
  const [teamsTestMsg, setTeamsTestMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [teamsConfigLoading, setTeamsConfigLoading] = useState(false)

  useEffect(() => {
    if (!open || integration?.id !== "teams") return
    setTeamsWebhookInput("")
    setTeamsSaveMsg(null)
    setTeamsTestMsg(null)
    setTeamsConfigLoading(true)
    apiFetch("/api/backend-proxy/integrations/teams/outbound-config")
      .then((r) => r.json())
      .then((data) => {
        setTeamsWebhookMasked(data.webhook_url_masked ?? null)
        setTeamsWebhookSource(data.source ?? "none")
      })
      .catch(() => {})
      .finally(() => setTeamsConfigLoading(false))
  }, [open, integration?.id])

  const handleTeamsSave = useCallback(async () => {
    if (!teamsWebhookInput.trim()) return
    setTeamsSaveLoading(true)
    setTeamsSaveMsg(null)
    try {
      const res = await apiFetch("/api/backend-proxy/integrations/teams/outbound-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ webhook_url: teamsWebhookInput.trim() }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setTeamsSaveMsg({ ok: false, text: err.detail || "Erro ao salvar webhook URL" })
        return
      }
      const data = await res.json()
      setTeamsWebhookMasked(data.webhook_url_masked ?? null)
      setTeamsWebhookSource("db")
      setTeamsWebhookInput("")
      setTeamsSaveMsg({ ok: true, text: "URL salva com sucesso" })
      notifyChatOfSettingsUpdate({ actionId: "configure_integration", section: "integrations" })
      onConfigSaved?.()
    } catch {
      setTeamsSaveMsg({ ok: false, text: "Erro de conexão" })
    } finally {
      setTeamsSaveLoading(false)
    }
  }, [teamsWebhookInput, onConfigSaved])

  const handleTeamsTest = useCallback(async () => {
    setTeamsTestLoading(true)
    setTeamsTestMsg(null)
    try {
      // Pass the typed URL (if any) so the test validates the input before saving.
      // If the input is empty, the backend resolves the already-saved per-tenant URL.
      const testBody = teamsWebhookInput.trim()
        ? { webhook_url: teamsWebhookInput.trim() }
        : {}
      const res = await apiFetch("/api/backend-proxy/integrations/teams/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(testBody),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || data.success === false) {
        setTeamsTestMsg({ ok: false, text: data.error || data.detail || "Falha no teste" })
      } else if (data.mode === "development") {
        setTeamsTestMsg({ ok: false, text: "Modo desenvolvimento: nenhuma URL configurada" })
      } else {
        setTeamsTestMsg({ ok: true, text: "Mensagem de teste enviada com sucesso" })
      }
    } catch {
      setTeamsTestMsg({ ok: false, text: "Erro de conexão" })
    } finally {
      setTeamsTestLoading(false)
    }
  }, [teamsWebhookInput])
  // W2-012-B (2026-05-23): salva region per-tenant. LGPD Art 33.
  const handleSaveRegion = useCallback(async (newRegion: string | null) => {
    if (!integration) return { success: false, message: "Integração não selecionada" }
    try {
      const currentConfig = await apiFetch("/api/backend-proxy/llm-config").then(r => r.json())
      const res = await apiFetch("/api/backend-proxy/llm-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_provider: currentConfig.primary_provider || "gemini",
          fallback_order: currentConfig.fallback_order || ["gemini", "claude", "openai"],
          providers: currentConfig.providers || {},
          routing: currentConfig.routing || { chat: "gemini", embedding: "gemini", screening: "gemini", voice: "gemini" },
          region: newRegion,
        }),
      })
      notifyChatOfSettingsUpdate({ actionId: "configure_integration", section: "integrations" })
      if (!res.ok) return { success: false, message: "Erro ao salvar região" }
      onConfigSaved?.()
      return { success: true, message: "Região atualizada" }
    } catch {
      return { success: false, message: "Erro de conexão" }
    }
  }, [integration, onConfigSaved])

  const handleSaveApiKey = useCallback(async (apiKey: string) => {
    if (!integration) return { success: false, message: "Integração não selecionada" }
    try {
      const currentConfig = await apiFetch("/api/backend-proxy/llm-config").then(r => r.json())

      const res = await apiFetch("/api/backend-proxy/llm-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_provider: currentConfig.primary_provider || "gemini",
          fallback_order: currentConfig.fallback_order || ["gemini", "claude", "openai"],
          providers: {
            [integration.id]: { provider: integration.id, api_key: apiKey, is_active: true },
          },
          routing: currentConfig.routing || { chat: "gemini", embedding: "gemini", screening: "gemini", voice: "gemini" },
          region: currentConfig.region ?? null,  // W2-012-B: preserva region existente
        }),
      })

      if (!res.ok) {
        return { success: false, message: "Erro ao salvar configuração" }
      }

      onConfigSaved?.()
      return { success: true, message: `${integration.name} configurado com sucesso` }
    } catch {
      return { success: false, message: "Erro de conexão" }
    }
  }, [integration, onConfigSaved])

  const handleRemoveApiKey = useCallback(async () => {
    if (!integration) return
    const currentConfig = await apiFetch("/api/backend-proxy/llm-config").then(r => r.json())

    await apiFetch("/api/backend-proxy/llm-config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        primary_provider: currentConfig.primary_provider || "gemini",
        fallback_order: currentConfig.fallback_order || ["gemini", "claude", "openai"],
        providers: {
          [integration.id]: { _remove: true },
        },
        routing: currentConfig.routing || {},
      }),
    })

    onConfigSaved?.()
  }, [integration, onConfigSaved])

  // Rules of Hooks: every hook above this line. See CLAUDE.md § Frontend / React rules-of-hooks.
  if (!integration) return null

  const isComingSoon = integration.status === "coming_soon"
  const isAiProvider = AI_PROVIDER_IDS.includes(integration.id)

  const existingProviderConfig = isAiProvider && llmConfig?.providers?.[integration.id]
  const hasExistingKey = !!(existingProviderConfig && (existingProviderConfig as ProviderConfigData).api_key)
  const maskedExistingKey = hasExistingKey
    ? (existingProviderConfig as ProviderConfigData).api_key || ""
    : ""
  const isUsingOwnKey = hasExistingKey && maskedExistingKey.length > 3
  const isPrimaryProvider = llmConfig?.primary_provider === integration.id

  const resolvedStatus = (() => {
    if (isAiProvider && llmConfig) {
      const providerData = llmConfig.providers?.[integration.id]
      if (providerData?.api_key) return "connected"
      return "not_configured"
    }
    if (integration.id === "google-calendar") {
      return googleStatus === "connected" ? "connected" : "not_configured"
    }
    if (integration.id === "microsoft-calendar") {
      return microsoftStatus === "connected" ? "connected" : "not_configured"
    }
    if (integration.id === "teams") {
      return teamsStatus === "configured" ? "connected" : "not_configured"
    }
    return integration.status
  })()

  const isActivePrimary = isAiProvider && llmConfig?.primary_provider === integration.id

  const savedKeyMasked = isAiProvider
    ? llmConfig?.providers?.[integration.id]?.api_key || undefined
    : undefined

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="sm:max-w-2xl max-h-[85vh] flex flex-col"
        data-testid="integration-detail-modal"
      >
        <DialogHeader className="pb-2">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "w-12 h-12 rounded-md flex items-center justify-center flex-shrink-0",
                textStyles.metricSmall,
                integration.iconBg,
                integration.iconColor
              )}
            >
              {integration.iconLetter}
            </div>
            <div className="min-w-0 flex-1">
              <DialogTitle className={textStyles.titleLarge}>
                {integration.name}
              </DialogTitle>
              <DialogDescription className={cn(textStyles.description, "mt-1")}>
                {integration.shortDescription}
              </DialogDescription>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {resolvedStatus === "connected" ? (
                  <Chip variant="success" className="text-[10px] gap-1 px-2 py-0.5">
                    <CheckCircle2 className="w-3 h-3" />
                    Conectado
                  </Chip>
                ) : isComingSoon ? (
                  <Chip variant="neutral" muted className="text-[10px] gap-1 px-2 py-0.5">
                    <Clock className="w-3 h-3" />
                    Em breve
                  </Chip>
                ) : (
                  <Chip variant="neutral" className="text-[10px] gap-1 px-2 py-0.5 text-lia-text-secondary">
                    <Settings className="w-3 h-3" />
                    Não configurado
                  </Chip>
                )}
                {(isActivePrimary || isPrimaryProvider) && (
                  <Chip variant="info" className="text-[10px] gap-1 px-2 py-0.5">
                    <Zap className="w-3 h-3" />
                    Provedor ativo
                  </Chip>
                )}
                {isAiProvider && isUsingOwnKey && (
                  <Chip variant="neutral" muted className="text-[10px] gap-1 px-2 py-0.5">
                    <Key className="w-3 h-3" />
                    Chave própria
                  </Chip>
                )}
                {isAiProvider && !isUsingOwnKey && (
                  <Chip variant="neutral" className="text-[10px] gap-1 px-2 py-0.5 text-lia-text-tertiary">
                    <ShieldCheck className="w-3 h-3" />
                    Cota compartilhada
                  </Chip>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 py-4 space-y-6">
          <div>
            <h4 className={cn(textStyles.label, "mb-2")}>
              Sobre
            </h4>
            <p className={cn(textStyles.description, "leading-relaxed")}>
              {integration.fullDescription}
            </p>
          </div>

          <div>
            <h4 className={cn(textStyles.label, "mb-3")}>
              Recursos &amp; Capacidades
            </h4>
            <div className="flex flex-wrap gap-2">
              {integration.capabilities.map((cap) => (
                <div key={cap.name} className="group relative">
                  <Chip variant="neutral" muted className="text-[10px] px-2.5 py-1 cursor-default">
                    {cap.name}
                  </Chip>
                  <div className="invisible group-hover:visible absolute bottom-full left-0 mb-1 px-2 py-1 bg-lia-bg-inverse dark:bg-lia-bg-primary text-lia-text-inverse dark:text-lia-text-primary text-[10px] rounded-xl whitespace-nowrap z-10 shadow-md">
                    {cap.description}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {isAiProvider && integration.id === "openai" && resolvedStatus !== "connected" && (
            <div className={cn(cardStyles.flat, "flex items-start gap-3 px-4 py-3 border border-status-warning-border-light bg-status-warning-bg")}>
              <Mic className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5" />
              <div>
                <p className={cn(textStyles.label, "text-status-warning")}>
                  Necessário para voz nas triagens
                </p>
                <p className={cn(textStyles.description, "mt-1 text-status-warning/80")}>
                  A transcrição de áudio dos candidatos (Whisper) e a voz da LIA (TTS) dependem da OpenAI. Sem esta chave, as triagens funcionam apenas por texto.
                </p>
              </div>
            </div>
          )}

          {isAiProvider && integration.id === "openai" && resolvedStatus === "connected" && (
            <div className={cn(cardStyles.flat, "flex items-start gap-3 px-4 py-3 border border-status-success/30 bg-status-success-bg")}>
              <Mic className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
              <p className={cn(textStyles.description, "text-status-success")}>
                Transcrição (Whisper) e voz da LIA (TTS) habilitados para triagens.
              </p>
            </div>
          )}

          {isAiProvider && (integration.id === "gemini" || integration.id === "claude") && (
            <div className={cn(cardStyles.flat, "flex items-start gap-3 px-4 py-3")}>
              <Info className="w-4 h-4 text-lia-text-tertiary flex-shrink-0 mt-0.5" />
              <p className={cn(textStyles.description)}>
                Para habilitar voz nas triagens (transcrição e TTS), configure também a integração{" "}
                <strong>OpenAI GPT</strong>.{" "}
                {integration.id === "gemini" ? "Gemini" : "Claude"} é utilizado para chat e análise de candidatos.
              </p>
            </div>
          )}

          {isAiProvider && !isComingSoon && (
            <ApiKeyConfigForm
              providerId={integration.id}
              providerName={integration.name}
              configFieldName={integration.configFields?.[0] || "API_KEY"}
              savedKeyMasked={savedKeyMasked}
              onSave={handleSaveApiKey}
              onRemove={handleRemoveApiKey}
            />
          )}

          {!isAiProvider && integration.configFields && integration.configFields.length > 0 && !isComingSoon && (
            <div>
              <h4 className={cn(textStyles.label, "mb-2")}>
                Configuração Necessária
              </h4>
              <div className="space-y-1.5">
                {integration.configFields.map((field) => (
                  <div
                    key={field}
                    className={cn(cardStyles.flat, "flex items-center gap-2 px-3 py-2")}
                  >
                    <code className="text-[10px] font-mono text-lia-text-secondary dark:text-lia-text-secondary">
                      {field}
                    </code>
                    {resolvedStatus === "connected" ? (
                      <CheckCircle2 className="w-3 h-3 text-status-success ml-auto flex-shrink-0" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-lia-text-tertiary ml-auto flex-shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {integration.id === "teams" && !isComingSoon && (
            <div>
              <h4 className={cn(textStyles.label, "mb-3")}>
                Webhook de Notificações (Outbound)
              </h4>

              {teamsConfigLoading ? (
                <div className="flex items-center gap-2 py-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
                  <span className={cn(textStyles.description, "text-lia-text-tertiary")}>Carregando configuração...</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {teamsWebhookMasked && (
                    <div className={cn(cardStyles.flat, "flex items-center gap-2 px-3 py-2")}>
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className={cn(textStyles.description, "font-mono text-[10px] truncate")}>
                          {teamsWebhookMasked}
                        </p>
                        <p className="text-[10px] text-lia-text-tertiary mt-0.5">
                          {teamsWebhookSource === "db" ? "Configurado por esta tela" : "Via variável de ambiente"}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <p className={textStyles.description}>
                      Cole a URL do Incoming Webhook do canal Teams que deve receber as notificações da LIA.
                    </p>
                    <div className="flex gap-2">
                      <Input
                        type="url"
                        placeholder="https://outlook.office.com/webhook/..."
                        value={teamsWebhookInput}
                        onChange={(e) => setTeamsWebhookInput(e.target.value)}
                        className="rounded-md text-xs h-8 flex-1 font-mono"
                        data-testid="teams-webhook-url-input"
                      />
                      <Button
                        size="sm"
                        className="rounded-md text-xs gap-1.5 h-8 flex-shrink-0"
                        onClick={handleTeamsSave}
                        disabled={teamsSaveLoading || !teamsWebhookInput.trim()}
                        data-testid="teams-webhook-save-button"
                      >
                        {teamsSaveLoading ? (
                          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                        ) : (
                          <Save className="w-3 h-3" />
                        )}
                        Salvar
                      </Button>
                    </div>

                    {teamsSaveMsg && (
                      <div className={cn(
                        "flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px]",
                        teamsSaveMsg.ok
                          ? "bg-status-success-bg border border-status-success/30 text-status-success"
                          : "bg-status-error/10 border border-status-error/30 text-status-error"
                      )}>
                        {teamsSaveMsg.ok
                          ? <CheckCircle2 className="w-3 h-3 flex-shrink-0" />
                          : <AlertCircle className="w-3 h-3 flex-shrink-0" />
                        }
                        {teamsSaveMsg.text}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <p className={cn(textStyles.description, "text-lia-text-tertiary text-[11px]")}>
                      Teste se o webhook está ativo antes de salvar.
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="rounded-md text-xs gap-1.5 h-7"
                      onClick={handleTeamsTest}
                      disabled={teamsTestLoading || (!teamsWebhookMasked && !teamsWebhookInput.trim())}
                      data-testid="teams-webhook-test-button"
                    >
                      {teamsTestLoading ? (
                        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Send className="w-3 h-3" />
                      )}
                      Testar Conexão
                    </Button>
                  </div>

                  {teamsTestMsg && (
                    <div className={cn(
                      "flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px]",
                      teamsTestMsg.ok
                        ? "bg-status-success-bg border border-status-success/30 text-status-success"
                        : "bg-status-error/10 border border-status-error/30 text-status-error"
                    )}>
                      {teamsTestMsg.ok
                        ? <CheckCircle2 className="w-3 h-3 flex-shrink-0" />
                        : <AlertCircle className="w-3 h-3 flex-shrink-0" />
                      }
                      {teamsTestMsg.text}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {integration.id === "google-calendar" && errorMsg && (
            <div className="flex items-center gap-2 p-2 rounded-xl bg-status-error/10 border border-status-error/30 dark:border-status-error/30">
              <AlertCircle className="w-3.5 h-3.5 text-status-error flex-shrink-0" />
              <p className={cn(textStyles.body, "text-status-error dark:text-status-error")}>
                {errorMsg}
              </p>
            </div>
          )}

          {integration.id === "microsoft-calendar" && microsoftStatus !== "connected" && (
            <div>
              <p className={textStyles.description}>
                Configure as variáveis de ambiente Azure (
                <code className="bg-lia-bg-tertiary dark:bg-lia-bg-primary px-1 rounded text-[10px]">AZURE_CLIENT_ID</code>,{" "}
                <code className="bg-lia-bg-tertiary dark:bg-lia-bg-primary px-1 rounded text-[10px]">AZURE_CLIENT_SECRET</code>,{" "}
                <code className="bg-lia-bg-tertiary dark:bg-lia-bg-primary px-1 rounded text-[10px]">AZURE_TENANT_ID</code>
                ) para habilitar esta integração.
              </p>
            </div>
          )}

          {isComingSoon && (
            <div className={cn(cardStyles.flat, "flex items-center gap-3 px-4 py-3")}>
              <Clock className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
              <p className={textStyles.description}>
                Esta integração está no roadmap e será disponibilizada em breve.
                Entre em contato com o suporte para mais informações.
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="pt-2 border-t border-lia-border-subtle">
          {integration.id === "google-calendar" && googleStatus !== "connected" && (
            <Button
              size="sm"
              variant="outline"
              onClick={onConnectGoogle}
              disabled={googleStatus === "loading"}
              className="rounded-md text-xs gap-2"
              data-testid="integration-connect-google-button"
            >
              {googleStatus === "loading" ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                  Conectando...
                </>
              ) : (
                <>
                  <Chrome className="w-3 h-3" />
                  Conectar com Google
                </>
              )}
            </Button>
          )}

          {!isComingSoon && !isAiProvider && integration.id !== "google-calendar" && integration.id !== "teams" && resolvedStatus !== "connected" && (
            integration.category === "ats" ? (
              <Button
                size="sm"
                className="rounded-md text-xs gap-2"
                onClick={() => {
                  onClose()
                  window.location.href = "/integracoes-ats"
                }}
                data-testid="integration-configure-ats-button"
              >
                <ExternalLink className="w-3 h-3" />
                Configurar no Painel ATS
              </Button>
            ) : (
              <div className="flex items-start gap-2 px-3 py-2 text-xs text-lia-text-tertiary border border-lia-border-subtle rounded-md">
                <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <span>
                  Configuracao desta integracao ainda nao disponivel pela UI.
                  Entre em contato com o suporte para habilitar.
                </span>
              </div>
            )
          )}

          <Button
            size="sm"
            variant="outline"
            onClick={onClose}
            className="rounded-md text-xs"
          >
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
