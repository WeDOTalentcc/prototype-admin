"use client"

import { useCallback } from "react"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
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

          {!isComingSoon && !isAiProvider && integration.id !== "google-calendar" && resolvedStatus !== "connected" && (
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
