export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  try {
    const { token } = await params
    let body: Record<string, unknown> = {}
    const parseResult = _bodySchema.safeParse(await request.json().catch(() => ({}))); body = parseResult.success ? parseResult.data : {}
    
    const backendUrl = `${BACKEND_URL}/api/public/shared/${token}/request-otp`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao solicitar OTP', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
