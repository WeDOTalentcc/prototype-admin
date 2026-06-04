/**
 * activity-labels (2026-06-04): localiza no FE os labels dos cards de atividade
 * (passos de fase + nomes de ferramentas) conforme o locale ativo da plataforma.
 *
 * Arquitetura: o backend emite CHAVES semânticas (phase keys + tool names cruas);
 * o FE localiza aqui. Assim os cards respeitam o toggle PT/EN de forma reativa e
 * independente de qual página/estado do chat (resolve full-page EN sem plumbing
 * de locale no request).
 */

type LangMap = Record<string, Record<string, string>>

const PHASE_LABELS: LangMap = {
  pt: {
    understanding: "Entendendo sua solicitação",
    composing: "Preparando a resposta",
  },
  en: {
    understanding: "Understanding your request",
    composing: "Composing the response",
  },
}

const TOOL_LABELS: LangMap = {
  pt: {
    search_candidates: "Buscando candidatos",
    rank_candidates: "Ranqueando candidatos",
    get_candidate_stats: "Analisando estatísticas de candidatos",
    list_candidates: "Listando candidatos",
    list_candidates_by_stage: "Listando candidatos por etapa",
    list_jobs: "Listando vagas",
    search_jobs: "Buscando vagas",
    get_job_details: "Consultando detalhes da vaga",
    get_job_benchmark: "Consultando benchmark da vaga",
    get_job_quality_metrics: "Analisando qualidade da vaga",
    get_job_suggestions: "Gerando sugestões para a vaga",
    get_job_velocity: "Analisando velocidade da vaga",
  },
  en: {
    search_candidates: "Searching candidates",
    rank_candidates: "Ranking candidates",
    get_candidate_stats: "Analyzing candidate stats",
    list_candidates: "Listing candidates",
    list_candidates_by_stage: "Listing candidates by stage",
    list_jobs: "Listing jobs",
    search_jobs: "Searching jobs",
    get_job_details: "Fetching job details",
    get_job_benchmark: "Fetching job benchmark",
    get_job_quality_metrics: "Analyzing job quality",
    get_job_suggestions: "Generating job suggestions",
    get_job_velocity: "Analyzing job velocity",
  },
}

function langOf(locale: string): "pt" | "en" {
  return locale?.toLowerCase().startsWith("en") ? "en" : "pt"
}

function humanize(name: string): string {
  return name.replace(/[_-]+/g, " ").trim()
}

/** Localized label for a reasoning phase key (falls back to the raw value, e.g.
 *  if the backend ever emits free text instead of a known key). */
export function phaseLabel(key: string, locale: string): string {
  return PHASE_LABELS[langOf(locale)]?.[key] ?? key
}

/** Localized label for a tool name (falls back to a humanized name). */
export function toolLabel(name: string, locale: string): string {
  return TOOL_LABELS[langOf(locale)]?.[name] ?? humanize(name)
}
