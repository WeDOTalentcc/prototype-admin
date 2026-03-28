import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const { slug } = await params
    const formData = await request.formData()

    const backendForm = new FormData()
    backendForm.append('name', formData.get('name') as string)
    backendForm.append('email', formData.get('email') as string)
    backendForm.append('phone', formData.get('phone') as string)
    backendForm.append('lgpd_consent', formData.get('lgpd_consent') as string)

    const cvFile = formData.get('cv_file') as File
    if (cvFile) {
      backendForm.append('cv_file', cvFile)
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/public-vacancies/p/${slug}/apply`, {
      method: 'POST',
      body: backendForm,
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Erro ao processar candidatura', ...data },
        { status: response.status }
      )
    }

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
