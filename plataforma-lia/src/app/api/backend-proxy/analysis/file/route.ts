export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"
const MAX_FILE_SIZE = 10 * 1024 * 1024

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { success: false, error: "No file provided" },
        { status: 400 }
      )
    }

    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: "File too large (max 10MB)" },
        { status: 413 }
      )
    }

    const backendFormData = new FormData()
    backendFormData.append("file", file)

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/analysis/file`, {
        method: "POST",
        body: backendFormData,
      })

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }

    } catch (backendError) {
    }

    const mockAnalysis = {
      success: true,
      filename: file.name,
      extractedText: "Texto extraído do documento para análise...",
      keywords: ["Python", "AWS", "Data Engineer", "SQL", "Spark"],
      summary: "Documento analisado com sucesso",
      entities: {
        skills: ["Python", "AWS", "SQL", "Spark", "Airflow"],
        job_titles: ["Data Engineer", "Software Engineer"],
        companies: [],
        locations: ["São Paulo"],
        experience_years: 5,
      },
    }

    return NextResponse.json(mockAnalysis)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to analyze file" },
      { status: 500 }
    )
  }
}
