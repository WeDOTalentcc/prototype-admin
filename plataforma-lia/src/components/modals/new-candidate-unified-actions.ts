import { duplicateDetectionService, type DuplicateCheckResult } from '@/services/duplicate-detection-service'
import { toast } from "sonner"
import type { ParsedCV, ParsedCVResponse, InputTab, ManualData } from "./new-candidate-unified-types"

export async function processCV(file: File, setUploadProgress: (n: number) => void): Promise<ParsedCV> {
  setUploadProgress(10)
  const formData = new FormData()
  formData.append("file", file)
  setUploadProgress(30)

  const response = await fetch("/api/backend-proxy/cv/upload", {
    method: "POST",
    body: formData,
  })

  setUploadProgress(70)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || errorData.detail || "Erro ao processar CV")
  }

  const data: ParsedCVResponse = await response.json()
  setUploadProgress(100)

  if (data.success && data.parsed_cv) {
    return data.parsed_cv
  }
  throw new Error(data.message || "Erro ao processar CV")
}

export async function parseText(cvText: string, setUploadProgress: (n: number) => void): Promise<ParsedCV> {
  if (cvText.trim().length < 50) {
    throw new Error("O texto do CV deve ter pelo menos 50 caracteres.")
  }

  setUploadProgress(20)

  const response = await fetch("/api/backend-proxy/cv/parse-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: cvText, source: "manual_paste" }),
  })

  setUploadProgress(70)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || errorData.detail || "Erro ao processar texto")
  }

  const data: ParsedCVResponse = await response.json()
  setUploadProgress(100)

  if (data.success && data.parsed_cv) {
    return data.parsed_cv
  }
  throw new Error(data.message || "Erro ao processar texto")
}

export async function createCandidateAPI(candidateData: Record<string, unknown>): Promise<string> {
  const response = await fetch("/api/backend-proxy/candidates/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(candidateData),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || errorData.detail || "Erro ao criar candidato")
  }

  const result = await response.json()
  return result.id
}

export function buildCandidateDataFromParsed(parsed: ParsedCV, shouldEnrich: boolean): Record<string, unknown> {
  const languagesDict: Record<string, string> = {}
  if (parsed.languages && Array.isArray(parsed.languages)) {
    parsed.languages.forEach((lang: string) => {
      languagesDict[lang] = "intermediate"
    })
  }

  return {
    name: parsed.full_name,
    email: parsed.email || null,
    phone: parsed.phone || null,
    current_title: parsed.current_title || parsed.experiences?.[0]?.title || null,
    current_company: parsed.experiences?.[0]?.company || null,
    location_city: parsed.location || null,
    linkedin_url: parsed.linkedin || null,
    github_url: parsed.github || null,
    portfolio_url: parsed.portfolio || null,
    technical_skills: parsed.skills || [],
    languages: languagesDict,
    certifications: parsed.certifications || [],
    seniority_level: parsed.seniority_level || null,
    notes: parsed.summary || null,
    source: "manual",
    auto_enrich: shouldEnrich && !!parsed.linkedin
  }
}

export async function checkDuplicateByParsedCV(parsed: ParsedCV): Promise<DuplicateCheckResult> {
  return duplicateDetectionService.checkByParsedCV({
    full_name: parsed.full_name,
    email: parsed.email,
    phone: parsed.phone,
    linkedin: parsed.linkedin
  })
}

export async function checkDuplicateByLinkedin(url: string): Promise<DuplicateCheckResult> {
  return duplicateDetectionService.checkDuplicate({
    linkedinUrl: url.trim()
  })
}

export async function checkDuplicateByManual(data: ManualData): Promise<DuplicateCheckResult> {
  return duplicateDetectionService.checkDuplicate({
    name: data.name.trim(),
    email: data.email.trim() || undefined,
    phone: data.phone.trim() || undefined,
    linkedinUrl: data.linkedinUrl.trim() || undefined
  })
}

export function buildLinkedinCandidateData(linkedinUrl: string): Record<string, unknown> {
  return {
    name: "Importação LinkedIn",
    linkedin_url: linkedinUrl.trim(),
    source: "linkedin",
    auto_enrich: true
  }
}

export function buildManualCandidateData(manualData: ManualData): { data: Record<string, unknown>; hasLinkedin: boolean } {
  const hasLinkedin = !!(manualData.linkedinUrl.trim() && manualData.linkedinUrl.includes('linkedin.com/in/'))
  return {
    data: {
      name: manualData.name.trim(),
      email: manualData.email.trim() || null,
      phone: manualData.phone.trim() || null,
      linkedin_url: manualData.linkedinUrl.trim() || null,
      source: "manual",
      auto_enrich: hasLinkedin
    },
    hasLinkedin
  }
}

export function showSuccessToast(shouldEnrich: boolean) {
  if (shouldEnrich) {
    toast.success("Candidato cadastrado com sucesso!", { description: "A IA irá buscar os dados do LinkedIn em segundo plano. Abrindo perfil..." })
  } else {
    toast.success("Candidato cadastrado com sucesso!", { description: "Abrindo perfil completo..." })
  }
}
