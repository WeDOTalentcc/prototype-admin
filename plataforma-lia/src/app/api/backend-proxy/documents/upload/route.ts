export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_FILE_SIZE = 10 * 1024 * 1024

async function extractTextFromFile(file: File): Promise<string> {
  const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()

  if (ext === ".txt") {
    return await file.text()
  }

  if (ext === ".pdf" || ext === ".docx") {
    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/analysis/file`, {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        return data.extracted_text || data.text || data.content || ""
      }
    } catch {
      // fallback below
    }

    if (ext === ".docx") {
      const buffer = await file.arrayBuffer()
      const text = new TextDecoder("utf-8", { fatal: false }).decode(buffer)
      const paragraphs = text.match(/<w:t[^>]*>([^<]+)<\/w:t>/g) || []
      return paragraphs.map(p => p.replace(/<[^>]+>/g, "")).join(" ")
    }

    return ""
  }

  return ""
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    const documentType = (formData.get("document_type") as string) || "general"

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { success: false, error: "Nenhum arquivo enviado" },
        { status: 400 }
      )
    }

    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: "Arquivo muito grande (máximo 10MB)" },
        { status: 413 }
      )
    }

    const validExtensions = [".pdf", ".docx", ".txt"]
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()
    if (!validExtensions.includes(ext)) {
      return NextResponse.json(
        { success: false, error: "Formato não suportado. Use PDF, DOCX ou TXT." },
        { status: 400 }
      )
    }

    const extractedText = await extractTextFromFile(file)

    if (!extractedText || extractedText.trim().length < 10) {
      return NextResponse.json(
        { success: false, error: "Não foi possível extrair texto suficiente do documento." },
        { status: 422 }
      )
    }

    let fairnessWarnings: string[] = []
    try {
      const checkResponse = await fetch(`${BACKEND_URL}/api/v1/settings/fairness-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: extractedText.substring(0, 5000) }),
      })

      if (checkResponse.ok) {
        const checkData = await checkResponse.json()
        fairnessWarnings = checkData.soft_warnings || checkData.warnings || []
      }
    } catch {
      // non-critical
    }

    return NextResponse.json({
      success: true,
      extracted_text: extractedText,
      document_type: documentType,
      file_name: file.name,
      file_size: file.size,
      text_length: extractedText.length,
      fairness_warnings: fairnessWarnings,
    })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Erro interno ao processar documento" },
      { status: 500 }
    )
  }
}
