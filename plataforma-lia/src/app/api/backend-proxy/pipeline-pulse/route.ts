export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

interface PipelinePulseStage {
  macro_stage: string
  count: number
}

interface PipelinePulsePayload {
  stages: PipelinePulseStage[]
  total: number
  /** PR-M: count of active (status=Ativa) job vacancies for the Vaga pulse badge. */
  active_jobs?: number
}

function isValidPulsePayload(value: unknown): value is PipelinePulsePayload {
  if (!value || typeof value !== "object") return false
  const v = value as Record<string, unknown>
  if (!Array.isArray(v.stages)) return false
  if (typeof v.total !== "number") return false
  return v.stages.every(
    (s) =>
      s !== null &&
      typeof s === "object" &&
      typeof (s as Record<string, unknown>).macro_stage === "string" &&
      typeof (s as Record<string, unknown>).count === "number",
  )
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/pipeline-pulse`, {
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(errorData, { status: response.status })
    }

    const data = await response.json()

    // Task #817 (canonical-fix, defesa em profundidade no produtor):
    // Pydantic já valida no backend, mas se algo no caminho (cache, body
    // truncado, mismatch de versão, futuro middleware) retornar shape
    // divergente, falhar 502 explícito é melhor que vazar `undefined` e
    // travar o consumer com "undefined is not iterable". O contrato da
    // rota é garantir `{stages: PipelinePulseStage[], total: number}` ou
    // erro estruturado — nunca payload corrompido com 200.
    if (!isValidPulsePayload(data)) {
      return NextResponse.json(
        {
          error: "invalid_pulse_payload",
          detail:
            "Backend returned 200 OK but payload does not match PipelinePulseResponse contract",
        },
        { status: 502 },
      )
    }

    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 500 })
  }
}
