import { CandidateResult } from "@/components/search/search-results-card"

const API_BASE = ""

export interface PearchOptions {
  searchType: "fast"
  highFreshness: boolean
  strictFilters: boolean
  requireEmails: boolean
  showEmails: boolean
  requirePhoneNumbers: boolean
  showPhoneNumbers: boolean
  requirePhonesOrEmails: boolean
}

export interface SearchFilters {
  ppiOptions?: PearchOptions
  general?: {
    minExperience?: number
    maxExperience?: number
    openToWork?: boolean
  }
  location?: {
    countries?: string[]
    states?: string[]
    cities?: string[]
    remote?: boolean
  }
  position?: {
    titles?: string[]
    seniority?: string[]
  }
  company?: {
    names?: string[]
    sizes?: string[]
    industries?: string[]
  }
  skills?: {
    required?: string[]
    preferred?: string[]
  }
  education?: {
    degrees?: string[]
    institutions?: string[]
    fields?: string[]
  }
  languages?: {
    required?: string[]
    proficiencyLevels?: string[]
  }
}

export interface SearchSpec {
  location?: string
  location_city?: string
  location_state?: string
  location_country?: string
  job_title?: string
  seniority?: string
  years_experience?: string
  years_experience_min?: number
  years_experience_max?: number
  skills?: string[]
  required_skills?: string[]
  preferred_skills?: string[]
  industry?: string
  industries?: string[]
  company?: string
  companies?: string[]
  exclude_companies?: string[]
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  work_model?: string
  contract_type?: string
  languages?: string[]
  education_level?: string
  is_open_to_work?: boolean
  has_email?: boolean
  has_phone?: boolean
}

export interface SearchRequest {
  query: string
  thread_id?: string
  search_spec?: SearchSpec
  search_local?: boolean
  search_pearch?: boolean
  pearch_type?: "fast"
  local_limit?: number
  pearch_limit?: number
  show_emails?: boolean
  show_phone_numbers?: boolean
  high_freshness?: boolean
  strict_filters?: boolean
  require_emails?: boolean
  require_phone_numbers?: boolean
  require_phones_or_emails?: boolean
  job_vacancy_id?: number
  exclude_candidate_ids?: string[]
  filters?: SearchFilters
  include_discovered?: boolean
}

export interface SearchResponse {
  query: string
  thread_id?: string
  candidates: CandidateResult[]
  local_count: number
  pearch_count: number
  total_count: number
  credits_used?: number
  credits_remaining?: number
  search_time_seconds?: number
  warning_message?: string
  can_load_more: boolean
}

export interface CreditBreakdown {
  base: number
  insights: number
  emails: number
  phones: number
  freshness: number
}

export interface CreditEstimate {
  query: string
  pearch_type: string
  limit: number
  base_cost: number
  insights_cost: number
  freshness_cost: number
  email_cost: number
  phone_cost: number
  cost_per_candidate: number
  total_estimated: number
  breakdown: CreditBreakdown
  confirmation_message: string
  warnings: string[]
}

export interface CreditEstimateRequest {
  query: string
  pearch_type?: "fast"
  limit?: number
  insights?: boolean
  high_freshness?: boolean
  profile_scoring?: boolean
  strict_filters?: boolean
  require_emails?: boolean
  show_emails?: boolean
  require_phone_numbers?: boolean
  show_phone_numbers?: boolean
  require_phones_or_emails?: boolean
}

export interface CreditBalance {
  available_credits: number
  total_consumed: number
  total_searches: number
  last_updated?: string
}

export async function searchCandidates(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE}/api/backend-proxy/search/candidates`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: request.query,
      thread_id: request.thread_id,
      search_spec: request.search_spec,
      search_local: request.search_local ?? true,
      search_pearch: request.search_pearch ?? false,
      pearch_type: request.pearch_type ?? "fast",
      local_limit: request.local_limit ?? 20,
      pearch_limit: request.pearch_limit ?? 15,
      show_emails: request.show_emails ?? false,
      show_phone_numbers: request.show_phone_numbers ?? false,
      high_freshness: request.high_freshness ?? false,
      strict_filters: request.strict_filters ?? false,
      require_emails: request.require_emails ?? false,
      require_phone_numbers: request.require_phone_numbers ?? false,
      require_phones_or_emails: request.require_phones_or_emails ?? false,
      job_vacancy_id: request.job_vacancy_id,
      exclude_candidate_ids: request.exclude_candidate_ids ?? [],
      include_discovered: request.include_discovered ?? true,
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Search failed: ${error}`)
  }

  return response.json()
}

export async function searchLocalCandidates(
  query: string,
  limit: number = 20
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    query,
    limit: limit.toString(),
  })

  const response = await fetch(
    `${API_BASE}/api/backend-proxy/search/candidates/local?${params}`
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Local search failed: ${error}`)
  }

  return response.json()
}

export async function estimateCredits(
  request: CreditEstimateRequest
): Promise<CreditEstimate> {
  const response = await fetch(
    `${API_BASE}/api/backend-proxy/search/candidates/estimate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: request.query || "busca",
        pearch_type: request.pearch_type ?? "fast",
        limit: request.limit ?? 15,
        insights: request.insights ?? true,
        high_freshness: request.high_freshness ?? false,
        profile_scoring: request.profile_scoring ?? true,
        strict_filters: request.strict_filters ?? false,
        require_emails: request.require_emails ?? false,
        show_emails: request.show_emails ?? false,
        require_phone_numbers: request.require_phone_numbers ?? false,
        show_phone_numbers: request.show_phone_numbers ?? false,
        require_phones_or_emails: request.require_phones_or_emails ?? false,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Estimate failed: ${error}`)
  }

  return response.json()
}

export async function getCreditBalance(): Promise<CreditBalance> {
  const response = await fetch(`${API_BASE}/api/backend-proxy/credits/balance`)

  if (!response.ok) {
    throw new Error("Failed to fetch credit balance")
  }

  return response.json()
}

export async function refineSearch(
  thread_id: string,
  additional_query: string,
  limit?: number
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    thread_id,
    additional_query,
  })

  if (limit) {
    params.set("limit", limit.toString())
  }

  const response = await fetch(
    `${API_BASE}/api/backend-proxy/search/candidates/refine?${params}`,
    { method: "POST" }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Refine failed: ${error}`)
  }

  return response.json()
}

export function calculateCreditsLocally(options: {
  searchType: "fast"
  limit: number
  highFreshness?: boolean
  requireEmails?: boolean
  showEmails?: boolean
  requirePhoneNumbers?: boolean
  showPhoneNumbers?: boolean
  requirePhonesOrEmails?: boolean
}): CreditEstimate {
  const base = 1
  const insights = 2
  const freshness = options.highFreshness ? 2 : 0
  
  const emailCost = 0
  const phoneCost = 0
  
  const perCandidate = base + insights + freshness
  const total = perCandidate * options.limit
  
  const warnings: string[] = []
  if (options.requireEmails || options.requirePhoneNumbers) {
    warnings.push("Contatos enriquecidos via Apify ($0.01/candidato) quando não disponíveis")
  }
  if (total > 100) {
    warnings.push(`Custo total estimado alto: ${total} créditos`)
  }
  
  return {
    query: "",
    pearch_type: "fast",
    limit: options.limit,
    base_cost: base,
    insights_cost: insights,
    freshness_cost: freshness,
    email_cost: emailCost,
    phone_cost: phoneCost,
    cost_per_candidate: perCandidate,
    total_estimated: total,
    breakdown: {
      base,
      insights,
      emails: emailCost,
      phones: phoneCost,
      freshness
    },
    confirmation_message: `Custo estimado: ${total} créditos (${perCandidate}/candidato x ${options.limit}) + Apify $0.01/candidato para contatos`,
    warnings
  }
}

export interface EnhancePromptSuggestion {
  label: string
  value: string
  category: string
}

export interface EnhancePromptResponse {
  original_query: string
  enhanced_query: string
  explanation: string
  suggestions: EnhancePromptSuggestion[]
  confidence: number
}

export async function enhanceSearchPrompt(
  query: string,
  context?: Record<string, unknown>
): Promise<EnhancePromptResponse> {
  const response = await fetch(`${API_BASE}/api/backend-proxy/search/enhance-prompt`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, context }),
  })

  if (!response.ok) {
    return {
      original_query: query,
      enhanced_query: query,
      explanation: "",
      suggestions: [],
      confidence: 0,
    }
  }

  return response.json()
}

export interface PromoteCandidateResponse {
  success: boolean
  candidate_id?: string
  message: string
  was_merged?: boolean
}

export async function promoteCandidateToBase(
  profileId: string
): Promise<PromoteCandidateResponse> {
  const response = await fetch(
    `${API_BASE}/api/backend-proxy/search/candidates/promote/${profileId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to promote candidate: ${error}`)
  }

  return response.json()
}
