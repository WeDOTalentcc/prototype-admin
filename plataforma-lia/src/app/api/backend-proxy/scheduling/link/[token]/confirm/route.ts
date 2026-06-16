// proxy-auth-exempt: confirmacao via token capability (link enviado ao candidato); candidato nao-autenticado
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams, validateBody } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const tokenParamsSchema = z.object({
  token: z.string().min(1, 'Token is required'),
})

const confirmBodySchema = z.object({
  start: z.string().min(1, 'start is required'),
  end: z.string().min(1, 'end is required'),
}).passthrough()

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  try {
    const { token } = await params
    const paramValidation = validateParams({ token }, tokenParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const bodyValidation = await validateBody(request, confirmBodySchema)
    if (!bodyValidation.success) return bodyValidation.response

    const response = await fetch(
      `${BACKEND_URL}/api/v1/scheduling/link/${token}/confirm`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyValidation.data),
      }
    )

    if (response.status === 404) {
      return NextResponse.json(
        { error: 'Link de agendamento não encontrado' },
        { status: 404 }
      )
    }

    if (response.status === 410) {
      return NextResponse.json(
        { error: 'Este link já foi utilizado ou expirou' },
        { status: 410 }
      )
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao confirmar agendamento', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao confirmar agendamento' },
      { status: 500 }
    )
  }
}
