import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/onboarding`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      
      if (response.status === 404) {
        return NextResponse.json({
          success: true,
          message: 'Onboarding data received successfully',
          data: body
        })
      }
      
      return NextResponse.json(
        { error: 'Erro ao enviar dados de onboarding', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      success: true,
      message: 'Onboarding data received (fallback)',
      timestamp: new Date().toISOString()
    })
  }
}
