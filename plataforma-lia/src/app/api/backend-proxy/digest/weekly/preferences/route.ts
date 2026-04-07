export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'
import { validateBody } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const digestPreferencesSchema = z.object({
  weekly_report_enabled: z.boolean().optional(),
  email: z.string().email().optional(),
  frequency: z.string().optional(),
}).passthrough()

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/digest/weekly/preferences`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { weekly_report_enabled: true },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { weekly_report_enabled: true },
      { status: 200 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const bodyValidation = await validateBody(request, digestPreferencesSchema)
    if (!bodyValidation.success) return bodyValidation.response

    const response = await fetch(
      `${BACKEND_URL}/api/v1/digest/weekly/preferences`,
      {
        method: 'PUT',
        headers: {
          ...getAuthHeaders(request),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bodyValidation.data),
      }
    )

    if (!response.ok) {
      const errText = await response.text()
      return NextResponse.json(
        { error: errText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao atualizar preferência do resumo semanal' },
      { status: 500 }
    )
  }
}
