export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from "@/lib/api/validate"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { z } from "zod"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

// WT-2022 Wave 2 audit (2026-05-21): list mantida apenas como FALLBACK de UI
// quando backend nao tem config persisted ainda. NAO eh canonical — vide
// audit_alertas_departamentos.md ghost-setting finding G1.
//
// REMOVIDO: fallback "admin_company" cross-tenant (REGRA 6 CLAUDE.md).
// Agora exigimos JWT via getAuthHeaders + backend usa get_verified_company_id.
const DEFAULT_TECHNICAL_ALERTS = [
  { id: "ta-1", name: "Falha de Entrega de Email", description: "Alerta quando taxa de falha de entrega ultrapassa o limite", severity: "high", enabled: true, channels: ["email", "slack"], threshold: 5, thresholdUnit: "% de falhas" },
  { id: "ta-2", name: "Webhook Timeout", description: "Alerta quando webhooks não respondem dentro do tempo limite", severity: "medium", enabled: true, channels: ["slack"], threshold: 30, thresholdUnit: "segundos" },
  { id: "ta-3", name: "Quota de API Excedida", description: "Alerta quando empresa atinge 80% da quota de API", severity: "medium", enabled: true, channels: ["email"], threshold: 80, thresholdUnit: "% da quota" },
  { id: "ta-4", name: "Erro de Integração ATS", description: "Alerta para falhas na sincronização com sistemas ATS", severity: "critical", enabled: true, channels: ["email", "slack", "webhook"], threshold: 3, thresholdUnit: "falhas consecutivas" },
  { id: "ta-5", name: "Bounce Rate Alto", description: "Alerta quando taxa de bounce de emails é elevada", severity: "high", enabled: false, channels: ["email"], threshold: 10, thresholdUnit: "% de bounces" }
]

export async function GET(request: NextRequest) {
  try {
    // WT-2022 Wave 2: tenant via JWT, NUNCA via header X-Company-ID literal.
    // Backend FastAPI usa get_verified_company_id que valida JWT canonical.
    const headers = getAuthHeaders(request)
    const backendUrl = `${BACKEND_URL}/api/v1/alerts/config`

    const response = await fetch(backendUrl, { method: "GET", headers })

    if (!response.ok) {
      return NextResponse.json(
        {
          success: true,
          technicalAlerts: DEFAULT_TECHNICAL_ALERTS,
          briefing_frequency: "daily"
        },
        { status: 200 }
      )
    }

    const data = await response.json()
    const technicalAlerts = data.alerts?.filter((a: { id: string }) => a.id?.startsWith("ta-")) || []

    return NextResponse.json({
      success: true,
      technicalAlerts: technicalAlerts.length > 0 ? technicalAlerts : DEFAULT_TECHNICAL_ALERTS,
      alerts: data.alerts || [],
      briefing_frequency: data.briefing_frequency || "daily"
    })
  } catch (_error) {
    return NextResponse.json(
      {
        success: true,
        technicalAlerts: DEFAULT_TECHNICAL_ALERTS,
        briefing_frequency: "daily"
      },
      { status: 200 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest) {
  try {
    // WT-2022 Wave 2: tenant via JWT, NUNCA via header X-Company-ID literal.
    const headers = getAuthHeaders(request)
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/alerts/config`

    const response = await fetch(backendUrl, {
      method: "PUT",
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: "Erro ao salvar configuração de alertas", details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ success: true, ...data })
  } catch (_error) {
    return NextResponse.json(
      { error: "Erro ao conectar com o backend" },
      { status: 500 }
    )
  }
}
