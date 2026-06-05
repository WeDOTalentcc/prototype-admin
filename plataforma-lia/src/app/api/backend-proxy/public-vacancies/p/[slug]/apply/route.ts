// proxy-auth-exempt: aplicacao publica de candidato via slug; candidato nao-autenticado; consent LGPD no body
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  slug: z.string().min(1, 'slug is required'),
})

const applyFieldsSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email is required'),
  phone: z.string().min(1, 'Phone is required'),
  lgpd_consent: z.string().min(1, 'LGPD consent is required'),
})

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const { slug } = await params
    const paramValidation = validateParams({ slug }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const formData = await request.formData()

    const fields = {
      name: formData.get('name') as string,
      email: formData.get('email') as string,
      phone: formData.get('phone') as string,
      lgpd_consent: formData.get('lgpd_consent') as string,
    }

    const fieldValidation = applyFieldsSchema.safeParse(fields)
    if (!fieldValidation.success) {
      return NextResponse.json(
        { error: 'Validation error', details: fieldValidation.error.flatten() },
        { status: 400 }
      )
    }

    const backendForm = new FormData()
    backendForm.append('name', fields.name)
    backendForm.append('email', fields.email)
    backendForm.append('phone', fields.phone)
    backendForm.append('lgpd_consent', fields.lgpd_consent)

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
