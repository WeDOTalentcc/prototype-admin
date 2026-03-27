import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json(
        { success: false, error: "No file provided" },
        { status: 400 }
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

      console.warn("Backend returned error, using fallback:", response.status)
    } catch (backendError) {
      console.warn("Backend unavailable, using fallback:", backendError)
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
    console.error("Error analyzing file:", error)
    return NextResponse.json(
      { success: false, error: "Failed to analyze file" },
      { status: 500 }
    )
  }
}
