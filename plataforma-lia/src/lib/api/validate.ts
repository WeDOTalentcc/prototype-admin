import { ZodSchema } from 'zod'
import { NextRequest, NextResponse } from 'next/server'

export type ValidationResult<T> =
  | { success: true; data: T }
  | { success: false; response: NextResponse }

export function validateQuery<T>(
  request: NextRequest,
  schema: ZodSchema<T>
): ValidationResult<T> {
  const { searchParams } = new URL(request.url)
  const raw = Object.fromEntries(searchParams.entries())
  const result = schema.safeParse(raw)
  if (!result.success) {
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Invalid query parameters', details: result.error.flatten() },
        { status: 400 }
      ),
    }
  }
  return { success: true, data: result.data }
}

export async function validateFormData<T>(
  request: NextRequest,
  schema: ZodSchema<T>
): Promise<ValidationResult<T>> {
  let formData: FormData
  try {
    formData = await request.formData()
  } catch {
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Invalid form data' },
        { status: 400 }
      ),
    }
  }
  const raw = Object.fromEntries(formData.entries())
  const result = schema.safeParse(raw)
  if (!result.success) {
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Validation error', details: result.error.flatten() },
        { status: 400 }
      ),
    }
  }
  return { success: true, data: result.data }
}

export async function validateBody<T>(
  request: NextRequest,
  schema: ZodSchema<T>
): Promise<ValidationResult<T>> {
  let raw: unknown
  try {
    raw = await request.json()
  } catch {
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Invalid JSON body' },
        { status: 400 }
      ),
    }
  }

  const result = schema.safeParse(raw)
  if (!result.success) {
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Validation error', details: result.error.flatten() },
        { status: 400 }
      ),
    }
  }

  return { success: true, data: result.data }
}

export function validateParams<T>(
  params: unknown,
  schema: ZodSchema<T>
): ValidationResult<T> {
  const result = schema.safeParse(params)
  if (!result.success) {
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Invalid route parameters', details: result.error.flatten() },
        { status: 400 }
      ),
    }
  }
  return { success: true, data: result.data }
}
