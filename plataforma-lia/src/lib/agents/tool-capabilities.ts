/**
 * Tool → capacidade (plain-language PT) — mapeamento canonical para Agent Studio.
 *
 * CONTEXTO (Paulo, crítica do recrutador 2026-05-30):
 *   A galeria e o modal de template expunham nomes técnicos crus de tools
 *   (`search_candidates`, `get_evaluation_criteria`, ...) — jargão de engenharia
 *   sem sentido para um recrutador. Este mapa traduz cada tool numa frase de
 *   capacidade em PT plain-language e agrupa em 2-3 bullets de alto nível.
 *
 * SINGLE SOURCE OF TRUTH: qualquer surface do Studio que precise descrever o
 * "que o agente faz" para o cliente final lê daqui, nunca renderiza o ID cru.
 *
 * As frases são PT-only (dado canonical de produto, alinhado ao locale primário
 * PT-BR). O componente que consome ainda envolve cabeçalhos/labels em
 * useTranslations: só os verbos de capacidade vêm deste mapa.
 *
 * Tools canonical: espelham TOOL_KEYS em
 * `src/components/pages-agent-studio/custom-agents/types.ts`.
 */

/** Frase curta de capacidade por tool (verbo + objeto, plain-language PT). */
export const TOOL_CAPABILITY_PT: Record<string, string> = {
  search_candidates: "Busca candidatos",
  get_candidate_details: "Analisa perfis de candidatos",
  get_evaluation_criteria: "Consulta critérios de avaliação",
  get_company_culture: "Considera a cultura da empresa",
  get_pipeline_summary: "Acompanha o funil de candidatos",
  search_talent_pool: "Garimpa o banco de talentos",
  list_jobs: "Consulta vagas abertas",
  get_job_details: "Lê os detalhes da vaga",
  get_analytics_summary: "Resume indicadores e relatórios",
  summarize_context: "Resume o contexto da conversa",
  clarify_request: "Faz perguntas para entender melhor",
  move_candidate: "Move candidatos no funil",
  send_email: "Envia e-mails aos candidatos",
  update_candidate_field: "Atualiza informações do candidato",
  schedule_interview: "Agenda entrevistas",
  create_note: "Registra anotações e avaliações",
}

/**
 * Grupos conceituais de alto nível. Cada tool pertence a um grupo; o resumo
 * escolhe um rótulo narrativo por grupo presente (dedup conceitual), em vez de
 * listar muitos verbos soltos. Ordem dos grupos = ordem de exibição dos bullets.
 */
type CapabilityGroup =
  | "find"
  | "analyze"
  | "act"
  | "communicate"
  | "report"

const TOOL_GROUP: Record<string, CapabilityGroup> = {
  search_candidates: "find",
  search_talent_pool: "find",
  list_jobs: "find",
  get_job_details: "find",
  get_candidate_details: "analyze",
  get_evaluation_criteria: "analyze",
  get_company_culture: "analyze",
  summarize_context: "analyze",
  clarify_request: "analyze",
  get_pipeline_summary: "report",
  get_analytics_summary: "report",
  move_candidate: "act",
  update_candidate_field: "act",
  schedule_interview: "act",
  create_note: "act",
  send_email: "communicate",
}

/** Rótulo narrativo de alto nível por grupo (bullet do "O que este agente faz"). */
const GROUP_SUMMARY_PT: Record<CapabilityGroup, string> = {
  find: "Encontra os candidatos certos para a vaga",
  analyze: "Analisa perfis com base nos seus critérios",
  act: "Organiza o funil e mantém os dados em dia",
  communicate: "Conversa com os candidatos por e-mail",
  report: "Acompanha resultados e indicadores",
}

/**
 * Resume uma lista de tools em 2-3 bullets de alto nível, em PT plain-language.
 *
 * Dedup conceitual: várias tools do mesmo grupo viram um único bullet. Mantém a
 * ordem canonical dos grupos. Limita a `limit` (default 3) para não sobrecarregar.
 */
export function summarizeCapabilities(
  tools: readonly string[],
  limit = 3,
): string[] {
  if (!tools || tools.length === 0) return []

  const order: CapabilityGroup[] = ["find", "analyze", "act", "communicate", "report"]
  const present = new Set<CapabilityGroup>()

  for (const tool of tools) {
    const group = TOOL_GROUP[tool]
    if (group) present.add(group)
  }

  const bullets = order
    .filter((g) => present.has(g))
    .map((g) => GROUP_SUMMARY_PT[g])

  // Fallback: se nenhuma tool mapeou para grupo (tools desconhecidas), usa as
  // frases individuais conhecidas; senão devolve vazio (consumer decide o copy).
  if (bullets.length === 0) {
    const fallback = tools
      .map((tool) => TOOL_CAPABILITY_PT[tool])
      .filter((value): value is string => Boolean(value))
    return fallback.slice(0, limit)
  }

  return bullets.slice(0, limit)
}

/**
 * Lista plana de capacidades individuais conhecidas (verbo + objeto), para
 * surfaces que querem detalhe ao invés de resumo. Filtra tools desconhecidas.
 */
export function listCapabilities(tools: readonly string[]): string[] {
  if (!tools) return []
  return tools
    .map((tool) => TOOL_CAPABILITY_PT[tool])
    .filter((value): value is string => Boolean(value))
}
