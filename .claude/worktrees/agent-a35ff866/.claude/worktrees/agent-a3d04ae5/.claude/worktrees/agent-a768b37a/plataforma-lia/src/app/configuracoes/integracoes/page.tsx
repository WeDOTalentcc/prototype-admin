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
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-50 font-['Open_Sans',sans-serif]">
          Integrações de Calendário
        </h1>
        <p className="text-xs text-gray-500 mt-1 font-['Open_Sans',sans-serif]">
          Conecte seu calendário para agendar entrevistas automaticamente com candidatos.
        </p>
      </div>

      {/* Microsoft Calendar */}
      <Card className="border border-gray-200 dark:border-gray-700 rounded-md shadow-none">
        <CardHeader className="pb-3 pt-4 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold text-gray-900 dark:text-gray-50 font-['Open_Sans',sans-serif]">
                  Microsoft Calendar
                </CardTitle>
                <p className="text-xs text-gray-500 font-['Open_Sans',sans-serif]">
                  Agendamento via Microsoft Graph / Outlook
                </p>
              </div>
            </div>
            {microsoftStatus === "loading" ? (
              <Badge variant="outline" className="text-[10px] gap-1">
                <Loader2 className="w-3 h-3 animate-spin" /> Verificando...
              </Badge>
            ) : microsoftStatus === "connected" ? (
              <Badge variant="outline" className="text-[10px] gap-1 border-green-200 text-green-700 dark:text-green-400 dark:border-green-800">
                <CheckCircle2 className="w-3 h-3" /> Conectado
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px] gap-1 border-gray-200 text-gray-500">
                <XCircle className="w-3 h-3" /> Não configurado
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif]">
            Configure as variáveis <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-[10px]">AZURE_CLIENT_ID</code>,{" "}
            <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-[10px]">AZURE_CLIENT_SECRET</code> e{" "}
            <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded text-[10px]">AZURE_TENANT_ID</code> para habilitar.
          </p>
        </CardContent>
      </Card>

      {/* Google Calendar */}
      <Card className="border border-gray-200 dark:border-gray-700 rounded-md shadow-none">
        <CardHeader className="pb-3 pt-4 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md bg-red-50 dark:bg-red-950/30 flex items-center justify-center">
                <Chrome className="w-5 h-5 text-red-500 dark:text-red-400" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold text-gray-900 dark:text-gray-50 font-['Open_Sans',sans-serif]">
                  Google Calendar
                </CardTitle>
                <p className="text-xs text-gray-500 font-['Open_Sans',sans-serif]">
                  Agendamento com Google Meet automático
                </p>
              </div>
            </div>
            {googleStatus === "connected" ? (
              <Badge variant="outline" className="text-[10px] gap-1 border-green-200 text-green-700 dark:text-green-400 dark:border-green-800">
                <CheckCircle2 className="w-3 h-3" /> Conectado
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px] gap-1 border-gray-200 text-gray-500">
                <XCircle className="w-3 h-3" /> Não conectado
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif]">
            Conecte sua conta Google Workspace para criar eventos com link do Google Meet automaticamente ao agendar entrevistas.
          </p>
          {errorMsg && (
            <div className="flex items-center gap-2 p-2 rounded-md bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
              <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
              <p className="text-[11px] text-red-700 dark:text-red-400 font-['Open_Sans',sans-serif]">{errorMsg}</p>
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
