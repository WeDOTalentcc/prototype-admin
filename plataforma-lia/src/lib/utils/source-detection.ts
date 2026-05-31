"use client"

export interface SourceDetails {
  label: string
  subtext: string
  credits?: string
  isLocal: boolean
  isGlobal: boolean
  variant: string
}

const GLOBAL_SOURCE_VARIANTS = new Set([
  'pearch', 'pearch_ai', 'pearch_fast', 'pearch_pro',
  'global', 'external', 'pearch-ai', 'pearch-fast', 'pearch-pro',
  'sourcing', 'external_search', 'ai_search', 'aisearch',
  'apify_search', 'apify'
])

const LOCAL_SOURCE_VARIANTS = new Set([
  'local', 'internal', 'manual', 'import', 'csv', 'ats',
  'linkedin_import', 'gupy', 'pandape', 'uploaded', 'database',
  'referral', 'indication', 'website', 'career_page', 'form',
  'api', 'webhook', 'email', 'excel', 'json_import'
])

const LOCAL_SOURCE_LABELS: Record<string, { label: string; subtext: string }> = {
  'local': { label: 'Base Local', subtext: 'Candidato cadastrado no banco de dados' },
  'internal': { label: 'Interno', subtext: 'Cadastrado internamente' },
  'manual': { label: 'Cadastro Manual', subtext: 'Adicionado manualmente pelo recrutador' },
  'import': { label: 'Importado', subtext: 'Importado de arquivo ou integração' },
  'csv': { label: 'Importação CSV', subtext: 'Importado via arquivo CSV' },
  'excel': { label: 'Importação Excel', subtext: 'Importado via arquivo Excel' },
  'ats': { label: 'ATS', subtext: 'Sincronizado do sistema ATS' },
  'linkedin_import': { label: 'LinkedIn', subtext: 'Importado do LinkedIn' },
  'gupy': { label: 'Gupy', subtext: 'Sincronizado da plataforma Gupy' },
  'pandape': { label: 'Pandapé', subtext: 'Sincronizado do Pandapé' },
  'referral': { label: 'Indicação', subtext: 'Indicado por colaborador' },
  'indication': { label: 'Indicação', subtext: 'Indicado por colaborador' },
  'website': { label: 'Website', subtext: 'Candidatura pelo site' },
  'career_page': { label: 'Página de Carreiras', subtext: 'Candidatura via página de vagas' },
  'form': { label: 'Formulário', subtext: 'Candidatura via formulário' },
  'api': { label: 'API', subtext: 'Importado via API' },
  'webhook': { label: 'Webhook', subtext: 'Recebido via webhook' },
  'email': { label: 'Email', subtext: 'Recebido via email' },
  'json_import': { label: 'Importação JSON', subtext: 'Importado via arquivo JSON' },
}

const GLOBAL_SOURCE_LABELS: Record<string, { label: string; subtext: string; credits: string }> = {
  'pearch': { label: 'Base Global', subtext: 'Busca inteligente global', credits: '1 cred + $0.01 Apify/cand' },
  'pearch_ai': { label: 'Base Global', subtext: 'Busca com insights', credits: '1 cred + $0.01 Apify/cand' },
  'pearch_pro': { label: 'Base Global', subtext: 'Busca avançada', credits: '1 cred + $0.01 Apify/cand' },
  'pearch_fast': { label: 'Base Global', subtext: 'Busca rápida', credits: '1 cred + $0.01 Apify/cand' },
  'pearch-ai': { label: 'Base Global', subtext: 'Busca com insights', credits: '1 cred + $0.01 Apify/cand' },
  'pearch-pro': { label: 'Base Global', subtext: 'Busca avançada', credits: '1 cred + $0.01 Apify/cand' },
  'pearch-fast': { label: 'Base Global', subtext: 'Busca rápida', credits: '1 cred + $0.01 Apify/cand' },
  'global': { label: 'Base Global', subtext: 'Candidato de busca externa', credits: '1 cred + $0.01 Apify/cand' },
  'external': { label: 'Fonte Externa', subtext: 'Sourcing externo', credits: '1 cred + $0.01 Apify/cand' },
  'external_search': { label: 'Busca Externa', subtext: 'Candidato de busca externa', credits: '1 cred + $0.01 Apify/cand' },
  'ai_search': { label: 'Busca IA', subtext: 'Encontrado via inteligência artificial', credits: '1 cred + $0.01 Apify/cand' },
  'aisearch': { label: 'Busca IA', subtext: 'Encontrado via inteligência artificial', credits: '1 cred + $0.01 Apify/cand' },
  'sourcing': { label: 'Sourcing', subtext: 'Sourcing externo', credits: '1 cred + $0.01 Apify/cand' },
  'apify_search': { label: 'Base Global', subtext: 'Busca LinkedIn (Apify)', credits: '$0.01 Apify/cand' },
  'apify': { label: 'Base Global', subtext: 'Enriquecimento Apify', credits: '$0.01 Apify/cand' },
}

export function normalizeSourceField(source: string | undefined | null): string {
  if (!source) return ''
  return source.toLowerCase().trim().replace(/\s+/g, '_').replace(/-/g, '_')
}

export function isGlobalSource(source: string | undefined | null, hasPearchId?: boolean): boolean {
  const normalized = normalizeSourceField(source)
  
  if (GLOBAL_SOURCE_VARIANTS.has(normalized)) return true
  
  if (hasPearchId && !LOCAL_SOURCE_VARIANTS.has(normalized) && !normalized) {
    return true
  }
  
  return false
}

export function isLocalSource(source: string | undefined | null, hasPearchId?: boolean): boolean {
  return !isGlobalSource(source, hasPearchId)
}

export function getSourceDetails(source: string | undefined | null, hasPearchId?: boolean): SourceDetails {
  const normalized = normalizeSourceField(source)
  const isGlobal = isGlobalSource(source, hasPearchId)
  
  if (isGlobal) {
    const globalDetails = GLOBAL_SOURCE_LABELS[normalized] || {
      label: 'Base Global',
      subtext: 'Busca inteligente global',
      credits: '1 cred + $0.01 Apify/cand'
    }
    return {
      ...globalDetails,
      isLocal: false,
      isGlobal: true,
      variant: normalized || 'pearch'
    }
  }
  
  const localDetails = LOCAL_SOURCE_LABELS[normalized] || {
    label: 'Base Local',
    subtext: 'Candidato da base interna'
  }
  return {
    ...localDetails,
    isLocal: true,
    isGlobal: false,
    variant: normalized || 'local'
  }
}

export function getSourceCreditsEstimate(source: string | undefined | null): number {
  const normalized = normalizeSourceField(source)
  
  if (LOCAL_SOURCE_VARIANTS.has(normalized) || !GLOBAL_SOURCE_VARIANTS.has(normalized)) {
    return 0
  }
  
  if (normalized.includes('fast')) return 3
  if (normalized.includes('pro')) return 7
  return 7
}
