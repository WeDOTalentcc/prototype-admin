"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle2, XCircle, Calendar, Chrome, AlertCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface IntegrationStatus {
  provider: "google" | "microsoft"
  connected: boolean
  label: string
  description: string
  icon: React.ReactNode
}

export default function IntegracoesPage() {
  const [googleStatus, setGoogleStatus] = useState<"idle" | "loading" | "connected" | "error">("idle")
  const [microsoftStatus, setMicrosoftStatus] = useState<"loading" | "connected" | "not_configured">("loading")
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Check Microsoft Graph status on mount
  useEffect(() => {
    fetch("/api/backend-proxy/calendar/health")
      .then((r) => r.json())
      .then((data) => {
        setMicrosoftStatus(data.graph_configured ? "connected" : "not_configured")
      })
      .catch(() => setMicrosoftStatus("not_configured"))
  }, [])

  const handleConnectGoogle = async () => {
    setGoogleStatus("loading")
    setErrorMsg(null)
    try {
      const companyId = "current" // will be resolved server-side from auth
      const res = await fetch(`/api/backend-proxy/calendar/google/auth-url?company_id=${companyId}`)
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Erro ao obter URL de autorização")
      }
      const { auth_url } = await res.json()
      // Open OAuth consent screen
      window.location.href = auth_url
    } catch (err) {
      setGoogleStatus("error")
      setErrorMsg(err instanceof Error ? err.message : "Erro ao conectar com Google")
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold lia-text-900 dark:lia-text-50 font-['Open_Sans',sans-serif]">
          Integrações de Calendário
        </h1>
        <p className="text-xs lia-text-500 mt-1 font-['Open_Sans',sans-serif]">
          Conecte seu calendário para agendar entrevistas automaticamente com candidatos.
        </p>
      </div>

      {/* Microsoft Calendar */}
      <Card className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md shadow-none">
        <CardHeader className="pb-3 pt-4 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-wedo-cyan-dark dark:text-wedo-cyan-dark" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold lia-text-900 dark:lia-text-50 font-['Open_Sans',sans-serif]">
                  Microsoft Calendar
                </CardTitle>
                <p className="text-xs lia-text-500 font-['Open_Sans',sans-serif]">
                  Agendamento via Microsoft Graph / Outlook
                </p>
              </div>
            </div>
            {microsoftStatus === "loading" ? (
              <Badge variant="outline" className="text-micro gap-1">
                <Loader2 className="w-3 h-3 animate-spin" /> Verificando...
              </Badge>
            ) : microsoftStatus === "connected" ? (
              <Badge variant="outline" className="text-micro gap-1 border-status-success/30 text-status-success dark:text-status-success dark:border-status-success/30">
                <CheckCircle2 className="w-3 h-3" /> Conectado
              </Badge>
            ) : (
              <Badge variant="outline" className="text-micro gap-1 border-lia-border-subtle lia-text-500">
                <XCircle className="w-3 h-3" /> Não configurado
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <p className="text-xs lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif]">
            Configure as variáveis <code className="bg-gray-100 dark:bg-lia-bg-secondary px-1 rounded-md text-micro">AZURE_CLIENT_ID</code>,{" "}
            <code className="bg-gray-100 dark:bg-lia-bg-secondary px-1 rounded-md text-micro">AZURE_CLIENT_SECRET</code> e{" "}
            <code className="bg-gray-100 dark:bg-lia-bg-secondary px-1 rounded-md text-micro">AZURE_TENANT_ID</code> para habilitar.
          </p>
        </CardContent>
      </Card>

      {/* Google Calendar */}
      <Card className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md shadow-none">
        <CardHeader className="pb-3 pt-4 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md bg-status-error/10 flex items-center justify-center">
                <Chrome className="w-5 h-5 text-status-error dark:text-status-error" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold lia-text-900 dark:lia-text-50 font-['Open_Sans',sans-serif]">
                  Google Calendar
                </CardTitle>
                <p className="text-xs lia-text-500 font-['Open_Sans',sans-serif]">
                  Agendamento com Google Meet automático
                </p>
              </div>
            </div>
            {googleStatus === "connected" ? (
              <Badge variant="outline" className="text-micro gap-1 border-status-success/30 text-status-success dark:text-status-success dark:border-status-success/30">
                <CheckCircle2 className="w-3 h-3" /> Conectado
              </Badge>
            ) : (
              <Badge variant="outline" className="text-micro gap-1 border-lia-border-subtle lia-text-500">
                <XCircle className="w-3 h-3" /> Não conectado
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          <p className="text-xs lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif]">
            Conecte sua conta Google Workspace para criar eventos com link do Google Meet automaticamente ao agendar entrevistas.
          </p>
          {errorMsg && (
            <div className="flex items-center gap-2 p-2 rounded-md bg-status-error/10 border border-status-error/30 dark:border-status-error/30">
              <AlertCircle className="w-3.5 h-3.5 text-status-error flex-shrink-0" />
              <p className="text-xs text-status-error dark:text-status-error font-['Open_Sans',sans-serif]">{errorMsg}</p>
            </div>
          )}
          {googleStatus !== "connected" && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleConnectGoogle}
              disabled={googleStatus === "loading"}
              className="rounded-md text-xs gap-2 font-['Open_Sans',sans-serif]"
            >
              {googleStatus === "loading" ? (
                <><Loader2 className="w-3 h-3 animate-spin" /> Conectando...</>
              ) : (
                <><Chrome className="w-3 h-3" /> Conectar com Google</>
              )}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
