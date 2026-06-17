/**
 * Task #1180 — Mapeia o JSON extraído por /company/culture-profile/analyze-direct
 * para o shape exato dos saves (4 blocos), descartando QUALQUER campo de
 * workforce planning (regra explícita do plano).
 *
 * Bloco           | Endpoint canônico
 * ----------------|---------------------------------------------------------
 * culture         | PUT /api/backend-proxy/company/culture-profile/{id}
 * tech_stack      | POST /api/backend-proxy/skills-catalog/company/skills-catalog/sync
 * benefits        | POST /api/backend-proxy/company/benefits/?company_id={id}  (1 chamada por benefício)
 * basic_complementary | PUT /api/backend-proxy/company/profile/{id}
 *
 * "Update existing" controla se o bloco basic_complementary sobrescreve campos
 * já preenchidos no company_profile. Quando false (default), apenas vazios são
 * propostos. Os outros 3 blocos sempre propõem (o card permite desmarcar).
 */

export type ProposalBlockKey =
  | "culture"
  | "tech_stack"
  | "benefits"
  | "basic_complementary"

export interface ProposalField {
  key: string
  label: string
  value: unknown
}

export interface ProposalBlock {
  key: ProposalBlockKey
  label: string
  fields: ProposalField[]
}

export interface ProposedSaves {
  blocks: ProposalBlock[]
  /** Hash determinístico do payload bruto — usado para auditoria. */
  payload_hash: string
}

export interface ExistingBasic {
  industry?: string | null
  employee_count?: number | string | null
  company_size?: string | null
  headquarters_city?: string | null
  headquarters_state?: string | null
  locations?: string[] | null
  founded_year?: number | string | null
  work_model?: string | null
  linkedin_url?: string | null
  logo_url?: string | null
}

const isEmpty = (v: unknown): boolean => {
  if (v === null || v === undefined) return true
  if (typeof v === "string") return v.trim() === ""
  if (Array.isArray(v)) return v.length === 0
  return false
}

const cleanScalar = (v: unknown): unknown => {
  if (typeof v === "string") {
    const t = v.trim()
    return t === "" ? null : t
  }
  return v
}

const cleanList = (v: unknown): string[] => {
  if (!Array.isArray(v)) return []
  return v
    .map((x) => (typeof x === "string" ? x.trim() : String(x ?? "").trim()))
    .filter(Boolean)
}

/**
 * Hash determinístico simples (FNV-1a 32-bit em hex) — não-criptográfico,
 * suficiente para detectar drift do payload entre proposta e save.
 */
export function payloadHash(payload: unknown): string {
  const str = JSON.stringify(payload)
  let h = 0x811c9dc5
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0
  }
  return h.toString(16).padStart(8, "0")
}

export interface MapOptions {
  /** Estado atual do company_profile — usado para filtrar basic_complementary. */
  existingBasic?: ExistingBasic
  /** Se true, basic_complementary inclui mesmo campos já preenchidos. */
  updateExisting?: boolean
}

export function mapExtractedToProposedSaves(
  extracted: Record<string, unknown>,
  opts: MapOptions = {},
): ProposedSaves {
  const blocks: ProposalBlock[] = []

  // ── Bloco 1: Cultura / EVP ────────────────────────────────────────
  const cultureFields: ProposalField[] = []
  const pushCulture = (key: string, label: string, raw: unknown, asList = false) => {
    const v = asList ? cleanList(raw) : cleanScalar(raw)
    if (!isEmpty(v)) cultureFields.push({ key, label, value: v })
  }
  pushCulture("mission", "Missão", extracted.mission)
  pushCulture("vision", "Visão", extracted.vision)
  pushCulture("values", "Valores", extracted.values, true)
  pushCulture("evp_bullets", "EVP (bullets)", extracted.evp_bullets, true)
  pushCulture("culture_description", "Descrição da cultura", extracted.culture_description)
  pushCulture("leadership_style", "Estilo de liderança", extracted.leadership_style)
  pushCulture("team_dynamics", "Dinâmica de time", extracted.team_dynamics)
  pushCulture("growth_opportunities", "Oportunidades de crescimento", extracted.growth_opportunities)
  pushCulture("dei_initiatives", "DEI", extracted.dei_initiatives)
  pushCulture("sustainability", "Sustentabilidade", extracted.sustainability)
  pushCulture("social_impact", "Impacto social", extracted.social_impact)
  const bf = extracted.big_five as Record<string, unknown> | undefined
  if (bf && typeof bf === "object") {
    cultureFields.push({ key: "big_five", label: "Big Five (perfil organizacional)", value: bf })
  }
  if (cultureFields.length > 0) {
    blocks.push({ key: "culture", label: "Cultura & EVP", fields: cultureFields })
  }

  // ── Bloco 2: Tech Stack ───────────────────────────────────────────
  const tech = cleanList(extracted.tech_stack)
  const engCulture = cleanScalar(extracted.engineering_culture)
  const techFields: ProposalField[] = []
  if (tech.length > 0) techFields.push({ key: "tech_stack", label: "Stack tecnológico", value: tech })
  if (!isEmpty(engCulture)) techFields.push({ key: "engineering_culture", label: "Cultura de engenharia", value: engCulture })
  if (techFields.length > 0) {
    blocks.push({ key: "tech_stack", label: "Tech Stack", fields: techFields })
  }

  // ── Bloco 3: Benefícios ───────────────────────────────────────────
  // O LLM hoje não devolve benefícios estruturados em /analyze-direct.
  // Mantemos o bloco para futura extensão (sem fields ⇒ não renderizado).
  const benefitsRaw = extracted.benefits
  if (Array.isArray(benefitsRaw) && benefitsRaw.length > 0) {
    const items = benefitsRaw
      .map((b) => {
        // Backend `BenefitBase` (lia-agent-system/app/schemas/company.py)
        // requer `name` + `category` (Pydantic non-default). Garante ambos
        // com default seguro `"other"` para evitar 422 no save.
        if (typeof b === "string") return { name: b.trim(), category: "other" }
        if (b && typeof b === "object") {
          const obj = { ...(b as Record<string, unknown>) }
          if (!obj.category || typeof obj.category !== "string") obj.category = "other"
          return obj
        }
        return null
      })
      .filter((b): b is Record<string, unknown> => b !== null && Boolean(b.name))
    if (items.length > 0) {
      blocks.push({
        key: "benefits",
        label: "Benefícios",
        fields: items.map((b, i) => ({
          key: `benefit_${i}`,
          label: String(b.name ?? `Benefício ${i + 1}`),
          value: b,
        })),
      })
    }
  }

  // ── Bloco 4: Dados Básicos complementares ─────────────────────────
  // NUNCA inclui nome/cnpj/website/linkedin (já tratados no modal) e NUNCA
  // workforce_plan / headcount_target / departments (regra anti-workforce).
  const existing = opts.existingBasic || {}
  const updateExisting = opts.updateExisting ?? false
  const basicFields: ProposalField[] = []
  const pushBasic = (
    key: string,
    label: string,
    raw: unknown,
    existingVal: unknown,
    asList = false,
  ) => {
    const v = asList ? cleanList(raw) : cleanScalar(raw)
    if (isEmpty(v)) return
    if (!updateExisting && !isEmpty(existingVal)) return
    basicFields.push({ key, label, value: v })
  }
  pushBasic("industry", "Setor", extracted.industry, existing.industry)
  pushBasic("employee_count", "Nº de funcionários", extracted.employee_count, existing.employee_count)
  pushBasic("company_size", "Porte", extracted.company_size, existing.company_size)
  // headquarters chega como "Cidade, UF" — split feito pelo backend PUT,
  // aqui mantemos a string única e propomos uma vez se vazio.
  pushBasic(
    "headquarters",
    "Sede",
    extracted.headquarters,
    existing.headquarters_city,
  )
  pushBasic("locations", "Localidades", extracted.locations, existing.locations, true)
  pushBasic("founded_year", "Fundação", extracted.founded_year, existing.founded_year)
  pushBasic("work_model", "Modelo de trabalho", extracted.work_model, existing.work_model)
  pushBasic("linkedin_url", "LinkedIn", extracted.linkedin_url, existing.linkedin_url)
  pushBasic("logo_url", "Logo URL", extracted.logo_url, existing.logo_url)
  if (basicFields.length > 0) {
    blocks.push({ key: "basic_complementary", label: "Dados Básicos complementares", fields: basicFields })
  }

  // GUARDA EXPLÍCITA — qualquer chave que cheire a workforce é descartada.
  // Defesa em profundidade caso o LLM passe a extrair esses campos no futuro.
  const WORKFORCE_KEY_RX = /workforce|headcount|hiring_plan|department_plan/i
  for (const blk of blocks) {
    blk.fields = blk.fields.filter((f) => !WORKFORCE_KEY_RX.test(f.key))
  }

  return {
    blocks,
    payload_hash: payloadHash(blocks),
  }
}
