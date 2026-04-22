export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'
import { z } from 'zod'

export async function GET(request: NextRequest) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { searchParams } = new URL(request.url)
    const clientId = searchParams.get('client_id')

    if (!clientId) {
      return NextResponse.json(
        { error: 'client_id é obrigatório' },
        { status: 400 }
      )
    }

    const backendUrl = `${BACKEND_URL}/api/v1/billing/clients/${clientId}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar dados de faturamento', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const { action, client_id, ...rest } = body

    if (!client_id) {
      return NextResponse.json(
        { error: 'client_id é obrigatório' },
        { status: 400 }
      )
    }

    let backendUrl = `${BACKEND_URL}/api/v1/billing/clients/${client_id}`

    if (action === 'cancel_subscription') {
      backendUrl = `${BACKEND_URL}/api/v1/billing/clients/${client_id}/cancel`
    } else if (action === 'change_plan') {
      backendUrl = `${BACKEND_URL}/api/v1/billing/clients/${client_id}/plan`
    } else if (action === 'download_invoice') {
      backendUrl = `${BACKEND_URL}/api/v1/billing/invoices/${rest.invoice_id}/download`
    }

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: auth.headers,
      body: JSON.stringify(rest),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar ação', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
