"use client"

import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import {
  CheckCircle2,
  Loader2,
  AlertCircle,
  Eye,
  EyeOff,
  Key,
  Trash2,
} from "lucide-react"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

interface ApiKeyConfigFormProps {
  providerId: string
  providerName: string
  configFieldName: string
  savedKeyMasked?: string
  onSave: (apiKey: string) => Promise<{ success: boolean; message: string }>
  onRemove?: () => Promise<void>
}

export function ApiKeyConfigForm({
  providerId,
  providerName,
  configFieldName,
  savedKeyMasked,
  onSave,
  onRemove,
}: ApiKeyConfigFormProps) {
  const [apiKey, setApiKey] = useState("")
  const [showKey, setShowKey] = useState(false)
  const [status, setStatus] = useState<"idle" | "testing" | "saving" | "success" | "error">("idle")
  const [message, setMessage] = useState("")
  const hasSavedKey = !!savedKeyMasked

  useEffect(() => {
    setApiKey("")
    setStatus("idle")
    setMessage("")
  }, [providerId])

  const handleSave = useCallback(async () => {
    if (!apiKey.trim()) return

    setStatus("testing")
    setMessage("Validando chave...")

    try {
      const testRes = await apiFetch("/api/backend-proxy/llm-config/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: providerId, api_key: apiKey.trim() }),
      })

      const testData = await testRes.json()

      if (!testData.success) {
        setStatus("error")
        setMessage(testData.message || "Chave inválida")
        return
      }

      notifyChatOfSettingsUpdate({
        actionId: "test_api_key",
        section: "integrations",
        field: providerId,
      })
      setStatus("saving")
      setMessage("Salvando configuração...")

      const result = await onSave(apiKey.trim())

      if (result.success) {
        setStatus("success")
        setMessage(result.message || `${providerName} configurado com sucesso`)
        setApiKey("")
      } else {
        setStatus("error")
        setMessage(result.message || "Erro ao salvar")
      }
    } catch (err) {
      setStatus("error")
      setMessage("Erro de conexão ao validar chave")
    }
  }, [apiKey, providerId, providerName, onSave])

  const handleRemove = useCallback(async () => {
    if (!onRemove) return
    setStatus("saving")
    setMessage("Removendo chave...")
    try {
      await onRemove()
      setStatus("idle")
      setMessage("")
    } catch {
      setStatus("error")
      setMessage("Erro ao remover chave")
    }
  }, [onRemove])

  const isProcessing = status === "testing" || status === "saving"

  return (
    <div className="space-y-3" data-testid={`api-key-config-form-${providerId}`}>
      <h4 className={cn(textStyles.label, "mb-2 flex items-center gap-1.5")}>
        <Key className="w-3.5 h-3.5" />
        Chave de API
      </h4>

      {hasSavedKey && status !== "success" && (
        <div className={cn(cardStyles.flat, "flex items-center gap-2 px-3 py-2")}>
          <CheckCircle2 className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
          <span className={cn(textStyles.body, "flex-1")}>
            Chave configurada: <code className="text-[10px] font-mono text-lia-text-secondary">{savedKeyMasked}</code>
          </span>
          {onRemove && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleRemove}
              disabled={isProcessing}
              data-testid={`api-key-remove-${providerId}`}
              aria-label="Remover chave API"
            >
              <Trash2 className="w-3 h-3 text-lia-text-tertiary hover:text-status-error" />
            </Button>
          )}
        </div>
      )}

      {status === "success" && (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-status-success/10 border border-status-success/30">
          <CheckCircle2 className="w-3.5 h-3.5 text-status-success flex-shrink-0" />
          <p className={cn(textStyles.body, "text-status-success")}>{message}</p>
        </div>
      )}

      <div className="space-y-2">
        <div className="relative">
          <Input
            type={showKey ? "text" : "password"}
            placeholder={hasSavedKey ? "Nova chave (substituir atual)" : `Cole sua ${configFieldName}`}
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value)
              if (status === "error" || status === "success") {
                setStatus("idle")
                setMessage("")
              }
            }}
            disabled={isProcessing}
            className="pr-10 text-xs font-mono bg-lia-bg-primary dark:bg-lia-bg-tertiary border-lia-border-subtle"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-lia-text-tertiary hover:text-lia-text-secondary transition-colors"
          >
            {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </button>
        </div>

        {status === "error" && (
          <div className="flex items-center gap-2 p-2 rounded-xl bg-status-error/10 border border-status-error/30">
            <AlertCircle className="w-3 h-3 text-status-error flex-shrink-0" />
            <p className={cn(textStyles.body, "text-status-error text-[11px]")}>{message}</p>
          </div>
        )}

        <Button
          size="sm"
          onClick={handleSave}
          disabled={!apiKey.trim() || isProcessing}
          className="w-full rounded-md text-xs gap-2"
          data-testid={`api-key-save-${providerId}`}
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
              {status === "testing" ? "Validando..." : "Salvando..."}
            </>
          ) : (
            <>
              <Key className="w-3 h-3" />
              {hasSavedKey ? "Atualizar Chave" : "Salvar Chave"}
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
