export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const companyId = request.nextUrl.searchParams.get('company_id') || 'default'
    
    const response = await fetch(`${BACKEND_URL}/api/v1/lia/profile-analysis/save?company_id=${companyId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ error }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to save analysis' }, { status: 500 })
  }
}
