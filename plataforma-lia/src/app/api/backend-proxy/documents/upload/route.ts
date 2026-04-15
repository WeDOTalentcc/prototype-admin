export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_FILE_SIZE = 10 * 1024 * 1024

const VALID_DOCUMENT_TYPES = ["handbook", "org_chart", "compensation", "tech_doc", "general"]

const SENSITIVE_TERMS: Record<string, string> = {
  "idade máxima": "Restrição por idade",
  "idade mínima": "Restrição por idade",
  "somente homens": "Discriminação de gênero",
  "somente mulheres": "Discriminação de gênero",
  "apenas homens": "Discriminação de gênero",
  "apenas mulheres": "Discriminação de gênero",
  "sexo masculino": "Referência a gênero",
  "sexo feminino": "Referência a gênero",
  "estado civil": "Dado pessoal sensível",
  "religião": "Dado pessoal sensível",
  "raça": "Dado pessoal sensível",
  "etnia": "Dado pessoal sensível",
  "cor da pele": "Dado pessoal sensível",
  "orientação sexual": "Dado pessoal sensível",
  "deficiência": "Termo sensível — verificar contexto",
  "portador de necessidades": "Termo desatualizado",
  "boa aparência": "Critério discriminatório",
  "aparência física": "Critério discriminatório",
  "young professionals only": "Age restriction",
  "male only": "Gender discrimination",
  "female only": "Gender discrimination",
  "no disabilities": "Disability discrimination",
  "marital status": "Sensitive personal data",
}

function runFairnessCheck(text: string): string[] {
  const lower = text.toLowerCase()
  const found: string[] = []
  const seen = new Set<string>()

  for (const [term, warning] of Object.entries(SENSITIVE_TERMS)) {
    if (lower.includes(term) && !seen.has(warning)) {
      seen.add(warning)
      found.push(warning)
    }
  }

  return found
}

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

    if (!VALID_DOCUMENT_TYPES.includes(documentType)) {
      return NextResponse.json(
        { success: false, error: "Tipo de documento inválido" },
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

    const fairnessWarnings = runFairnessCheck(extractedText.substring(0, 10000))

    return NextResponse.json({
      success: true,
      extracted_text: extractedText,
      document_type: documentType,
      file_name: file.name,
      file_size: file.size,
      text_length: extractedText.length,
      fairness_warnings: fairnessWarnings,
    })
  } catch {
    return NextResponse.json(
      { success: false, error: "Erro interno ao processar documento" },
      { status: 500 }
    )
  }
}
