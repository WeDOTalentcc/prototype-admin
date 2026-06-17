export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { bulkExportSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, bulkExportSchema)
    if (!bodyResult.success) return bodyResult.response

    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/bulk/export`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao exportar candidatos', details: errorData },
        { status: response.status }
      )
    }

    const contentType = response.headers.get('content-type')

    if (contentType?.includes('text/csv') || contentType?.includes('application/vnd.openxmlformats')) {
      const blob = await response.blob()
      const headers = new Headers()
      headers.set('Content-Type', contentType)
      headers.set('Content-Disposition', response.headers.get('Content-Disposition') || 'attachment; filename=candidates.csv')
      // Forward fallback header so the FE can show a toast when XLSX falls back to CSV
      const formatFallback = response.headers.get('X-Format-Fallback')
      if (formatFallback) {
        headers.set('X-Format-Fallback', formatFallback)
      }
      return new NextResponse(blob, { headers })
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
