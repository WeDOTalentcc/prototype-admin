/**
 * Curated agent conversation examples (Fase 3 Sprint 2 — "mostrar o agente em ação").
 *
 * Princípio ElevenLabs adaptado ao recrutador: comprehension by demonstration.
 * Em vez de descrever o que o agente faz, mostramos 2-4 turnos de uma conversa
 * real (Candidato ↔ Agente) que evidencia o VALOR — análise, justificativa,
 * recomendação. Resolve a dor #1 do recrutador ("não entendi o que faz").
 *
 * i18n strategy (decisão Sprint 2): os diálogos são DADOS curados, não chrome de
 * UI. Mantê-los como keyed-by-locale aqui (em vez de pulverizar ~120 keys em
 * messages/*.json) é a opção canonical: prosa longa não é label. O componente
 * AgentConversationPreview seleciona a lista pelo locale ativo (useLocale()).
 * Os rótulos de UI ("Veja em ação", "Candidato", "Agente") passam por
 * useTranslations normalmente.
 *
 * Este arquivo vive em src/lib/agents/ (fora do escopo do sensor
 * check_hardcoded_strings_in_agent_ui.py, que cobre components/pages-agent-studio/),
 * porque é uma fonte de dados, não um componente.
 *
 * Cobertura: mapeado por SLUG canonical do agent_template_catalog (migration 199)
 * com fallback por CATEGORIA quando um template novo não tem diálogo curado.
 */

export type ConversationRole = "candidate" | "agent"

export interface ConversationTurn {
  role: ConversationRole
  text: string
}

type LocalizedConversation = Record<"pt" | "en", ConversationTurn[]>

/**
 * Diálogos curados por slug de template (migration 199 _seed_agent_template_catalog).
 * Slugs canonical: tpl-triagem-tech, tpl-triagem-volume, tpl-screening-cultural,
 * tpl-sourcing-passivo, tpl-sourcing-diversidade, tpl-agendamento, tpl-followup,
 * tpl-analise-pipeline, tpl-comparacao, tpl-assistente-vaga, tpl-onboarding-prep,
 * tpl-salary-benchmark, tpl-feedback-collector, tpl-talent-pool-curator,
 * tpl-compliance-check.
 */
const CONVERSATIONS_BY_SLUG: Record<string, LocalizedConversation> = {
  "tpl-triagem-tech": {
    pt: [
      {
        role: "candidate",
        text: "Tenho 5 anos com Python, Django e AWS. Liderei a migração da plataforma para microsserviços.",
      },
      {
        role: "agent",
        text: "Perfil forte em backend e cloud. Recomendo avançar para a etapa técnica. Destaque: experiência com arquitetura distribuída alinhada à vaga. Nota de fit: 8,5/10.",
      },
      {
        role: "candidate",
        text: "Também já trabalhei com Kubernetes e observabilidade.",
      },
      {
        role: "agent",
        text: "Isso reforça o fit para o time de plataforma. Anotei como diferencial para o entrevistador técnico.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I have 5 years with Python, Django and AWS. I led the platform migration to microservices.",
      },
      {
        role: "agent",
        text: "Strong backend and cloud profile. I recommend moving to the technical stage. Highlight: distributed architecture experience aligned with the role. Fit score: 8.5/10.",
      },
      {
        role: "candidate",
        text: "I've also worked with Kubernetes and observability.",
      },
      {
        role: "agent",
        text: "That reinforces the fit for the platform team. I flagged it as a differentiator for the technical interviewer.",
      },
    ],
  },
  "tpl-triagem-volume": {
    pt: [
      {
        role: "candidate",
        text: "Moro perto da loja, tenho disponibilidade para turnos e 1 ano de experiência em atendimento.",
      },
      {
        role: "agent",
        text: "Atende aos requisitos mínimos: mobilidade, disponibilidade e experiência em atendimento. Encaminhado para a próxima etapa. Triado em 12 segundos.",
      },
      {
        role: "candidate",
        text: "Posso começar ainda este mês.",
      },
      {
        role: "agent",
        text: "Disponibilidade imediata registrada. Avancei o candidato e avisei o recrutador.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I live near the store, I'm available for shifts and have 1 year of customer service experience.",
      },
      {
        role: "agent",
        text: "Meets the minimum requirements: mobility, availability and service experience. Forwarded to the next stage. Screened in 12 seconds.",
      },
      {
        role: "candidate",
        text: "I can start this month.",
      },
      {
        role: "agent",
        text: "Immediate availability recorded. I advanced the candidate and notified the recruiter.",
      },
    ],
  },
  "tpl-screening-cultural": {
    pt: [
      {
        role: "candidate",
        text: "Prefiro times com autonomia e feedback aberto. Gosto de assumir problemas de ponta a ponta.",
      },
      {
        role: "agent",
        text: "Forte alinhamento com os valores de ownership e transparência da empresa. Soft skills compatíveis com o time. Sem perguntas sobre idade, gênero ou estado civil.",
      },
      {
        role: "candidate",
        text: "Também valorizo aprendizado contínuo.",
      },
      {
        role: "agent",
        text: "Coerente com a cultura de crescimento. Recomendo seguir para a conversa com o gestor.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I prefer teams with autonomy and open feedback. I like owning problems end to end.",
      },
      {
        role: "agent",
        text: "Strong alignment with the company's ownership and transparency values. Soft skills compatible with the team. No questions about age, gender or marital status.",
      },
      {
        role: "candidate",
        text: "I also value continuous learning.",
      },
      {
        role: "agent",
        text: "Consistent with the growth culture. I recommend moving to the conversation with the manager.",
      },
    ],
  },
  "tpl-sourcing-passivo": {
    pt: [
      {
        role: "agent",
        text: "Mapeei 18 perfis no banco de talentos com fit para a vaga de Engenheiro de Dados sênior. 6 não se candidatam há mais de 6 meses.",
      },
      {
        role: "candidate",
        text: "Não estava buscando, mas o desafio de dados em escala me interessa.",
      },
      {
        role: "agent",
        text: "Ótimo. Marquei o perfil como quente e preparei um resumo do match para o recrutador iniciar a abordagem.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "I mapped 18 profiles in the talent pool with fit for the senior Data Engineer role. 6 haven't applied in over 6 months.",
      },
      {
        role: "candidate",
        text: "I wasn't looking, but the data-at-scale challenge interests me.",
      },
      {
        role: "agent",
        text: "Great. I marked the profile as warm and prepared a match summary for the recruiter to start outreach.",
      },
    ],
  },
  "tpl-sourcing-diversidade": {
    pt: [
      {
        role: "agent",
        text: "Busquei candidatos para a vaga garantindo representatividade no funil. Filtrei só por competência e potencial, nunca por gênero, raça ou idade.",
      },
      {
        role: "candidate",
        text: "Tenho experiência sólida na área e gosto de ambientes plurais.",
      },
      {
        role: "agent",
        text: "Competências confirmadas. Adicionei ao funil mantendo o balanço de diversidade dentro da meta da empresa.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "I sourced candidates for the role ensuring representativeness in the funnel. I filtered only by skill and potential, never by gender, race or age.",
      },
      {
        role: "candidate",
        text: "I have solid experience in the area and enjoy diverse environments.",
      },
      {
        role: "agent",
        text: "Skills confirmed. I added them to the funnel keeping the diversity balance within the company's target.",
      },
    ],
  },
  "tpl-agendamento": {
    pt: [
      {
        role: "agent",
        text: "Olá! Para a entrevista técnica, tenho estes horários: terça 10h, quarta 14h ou quinta 16h. Qual prefere?",
      },
      {
        role: "candidate",
        text: "Quarta às 14h funciona melhor.",
      },
      {
        role: "agent",
        text: "Agendado para quarta, 14h. Enviei o convite para você e para o entrevistador, com o link da chamada.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "Hi! For the technical interview, I have these slots: Tuesday 10am, Wednesday 2pm or Thursday 4pm. Which do you prefer?",
      },
      {
        role: "candidate",
        text: "Wednesday at 2pm works best.",
      },
      {
        role: "agent",
        text: "Booked for Wednesday, 2pm. I sent the invite to you and the interviewer, with the call link.",
      },
    ],
  },
  "tpl-followup": {
    pt: [
      {
        role: "agent",
        text: "Oi! Obrigado pela entrevista de ontem. Queria confirmar que seu material foi recebido e que a próxima etapa é a conversa com o gestor.",
      },
      {
        role: "candidate",
        text: "Perfeito, fico no aguardo. Quando terei retorno?",
      },
      {
        role: "agent",
        text: "Damos retorno até sexta. Se houver qualquer mudança no prazo, eu aviso você antes.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "Hi! Thanks for yesterday's interview. I wanted to confirm we received your materials and the next stage is the conversation with the manager.",
      },
      {
        role: "candidate",
        text: "Perfect, I'll wait. When will I hear back?",
      },
      {
        role: "agent",
        text: "We respond by Friday. If the timeline changes, I'll let you know beforehand.",
      },
    ],
  },
  "tpl-analise-pipeline": {
    pt: [
      {
        role: "candidate",
        text: "Onde estamos perdendo candidatos no funil da vaga de Vendas?",
      },
      {
        role: "agent",
        text: "O maior gargalo é entre triagem e entrevista: 62% dos candidatos param ali, com tempo médio de 9 dias na etapa. Sugiro reduzir o intervalo de resposta para 48h.",
      },
      {
        role: "candidate",
        text: "E a conversão final?",
      },
      {
        role: "agent",
        text: "Da entrevista à oferta, 71% avançam. O problema está concentrado no topo do funil, não no fechamento.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "Where are we losing candidates in the Sales role funnel?",
      },
      {
        role: "agent",
        text: "The biggest bottleneck is between screening and interview: 62% of candidates stop there, with an average of 9 days in the stage. I suggest cutting the response window to 48h.",
      },
      {
        role: "candidate",
        text: "And the final conversion?",
      },
      {
        role: "agent",
        text: "From interview to offer, 71% advance. The problem is concentrated at the top of the funnel, not at closing.",
      },
    ],
  },
  "tpl-comparacao": {
    pt: [
      {
        role: "candidate",
        text: "Compare os três finalistas da vaga de Product Manager.",
      },
      {
        role: "agent",
        text: "Ana lidera em visão de produto (9/10) e dados (8/10). Bruno é mais forte em stakeholder management (9/10). Carla equilibra os dois (8/10 em ambos). Ranking objetivo: Ana, Carla, Bruno.",
      },
      {
        role: "candidate",
        text: "Por que Ana à frente da Carla?",
      },
      {
        role: "agent",
        text: "Ana tem evidências concretas de lançamentos de impacto. Carla é sólida, mas com menos exemplos quantificados. A diferença está na profundidade dos cases.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "Compare the three finalists for the Product Manager role.",
      },
      {
        role: "agent",
        text: "Ana leads in product vision (9/10) and data (8/10). Bruno is stronger in stakeholder management (9/10). Carla balances both (8/10 in each). Objective ranking: Ana, Carla, Bruno.",
      },
      {
        role: "candidate",
        text: "Why Ana ahead of Carla?",
      },
      {
        role: "agent",
        text: "Ana has concrete evidence of high-impact launches. Carla is solid, but with fewer quantified examples. The difference is the depth of the cases.",
      },
    ],
  },
  "tpl-assistente-vaga": {
    pt: [
      {
        role: "candidate",
        text: "Preciso de uma descrição para a vaga de Designer de Produto pleno.",
      },
      {
        role: "agent",
        text: "Montei uma descrição clara e inclusiva: responsabilidades, skills essenciais (Figma, design systems, pesquisa) e diferenciais. Removi exigências que afastam talentos sem necessidade real.",
      },
      {
        role: "candidate",
        text: "Inclui faixa salarial?",
      },
      {
        role: "agent",
        text: "Sim. Sugeri uma faixa competitiva com base no mercado para pleno na sua região, o que aumenta as candidaturas qualificadas.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I need a description for the mid-level Product Designer role.",
      },
      {
        role: "agent",
        text: "I built a clear, inclusive description: responsibilities, essential skills (Figma, design systems, research) and differentiators. I removed requirements that needlessly deter talent.",
      },
      {
        role: "candidate",
        text: "Does it include a salary range?",
      },
      {
        role: "agent",
        text: "Yes. I suggested a competitive range based on the market for mid-level in your region, which increases qualified applications.",
      },
    ],
  },
  "tpl-onboarding-prep": {
    pt: [
      {
        role: "candidate",
        text: "Fui contratado! O que preciso preparar para começar?",
      },
      {
        role: "agent",
        text: "Parabéns. Montei seu checklist: documentos para o RH, acessos a serem liberados, pessoas-chave do time para conhecer e as tarefas da primeira semana. Tudo organizado por dia.",
      },
      {
        role: "candidate",
        text: "Quando recebo os acessos?",
      },
      {
        role: "agent",
        text: "Solicitei os acessos para o primeiro dia. Vou acompanhar e avisar se algo atrasar.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I got hired! What do I need to prepare to start?",
      },
      {
        role: "agent",
        text: "Congratulations. I built your checklist: documents for HR, accesses to be granted, key team members to meet and first-week tasks. All organized by day.",
      },
      {
        role: "candidate",
        text: "When do I get the accesses?",
      },
      {
        role: "agent",
        text: "I requested the accesses for day one. I'll track them and warn you if anything is delayed.",
      },
    ],
  },
  "tpl-salary-benchmark": {
    pt: [
      {
        role: "candidate",
        text: "Qual a faixa de mercado para Engenheiro de Software sênior em São Paulo?",
      },
      {
        role: "agent",
        text: "Com base no setor e porte da empresa: P25 R$ 14k, mediana R$ 18k, P75 R$ 23k. Para reter talentos sênior, o ideal é mirar a partir da mediana.",
      },
      {
        role: "candidate",
        text: "E remoto fora de capital?",
      },
      {
        role: "agent",
        text: "A faixa cai cerca de 10% fora dos grandes centros, mas o pool de talentos cresce bastante. Vale considerar o trade-off.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "What's the market range for a senior Software Engineer in São Paulo?",
      },
      {
        role: "agent",
        text: "Based on sector and company size: P25 R$14k, median R$18k, P75 R$23k. To retain senior talent, aim from the median up.",
      },
      {
        role: "candidate",
        text: "And remote outside the capital?",
      },
      {
        role: "agent",
        text: "The range drops about 10% outside major hubs, but the talent pool grows considerably. Worth weighing the trade-off.",
      },
    ],
  },
  "tpl-feedback-collector": {
    pt: [
      {
        role: "agent",
        text: "Oi! Sobre a candidata Marina: pode me dar pontos fortes, áreas de melhoria e sua recomendação (sim / não / talvez)?",
      },
      {
        role: "candidate",
        text: "Forte em comunicação e dados. Precisa evoluir em negociação. Recomendo: sim.",
      },
      {
        role: "agent",
        text: "Registrado de forma estruturada. Consolidei com os outros entrevistadores: 2 sim e 1 talvez. Resumo pronto para a decisão.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "Hi! About candidate Marina: can you give me strengths, areas to improve and your recommendation (yes / no / maybe)?",
      },
      {
        role: "candidate",
        text: "Strong in communication and data. Needs to grow in negotiation. Recommendation: yes.",
      },
      {
        role: "agent",
        text: "Recorded in a structured way. I consolidated with the other interviewers: 2 yes and 1 maybe. Summary ready for the decision.",
      },
    ],
  },
  "tpl-talent-pool-curator": {
    pt: [
      {
        role: "candidate",
        text: "O banco de talentos está bagunçado. Pode organizar?",
      },
      {
        role: "agent",
        text: "Revisei 240 perfis: arquivei 31 desatualizados, categorizei por área e ranqueei por relevância para as vagas abertas. 12 perfis têm fit alto com as vagas atuais.",
      },
      {
        role: "candidate",
        text: "Pode priorizar os de tecnologia?",
      },
      {
        role: "agent",
        text: "Feito. Os perfis de tech estão no topo, ordenados por aderência. Prontos para abordagem imediata.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "The talent pool is messy. Can you organize it?",
      },
      {
        role: "agent",
        text: "I reviewed 240 profiles: archived 31 outdated ones, categorized by area and ranked by relevance to open roles. 12 profiles have high fit with current roles.",
      },
      {
        role: "candidate",
        text: "Can you prioritize the tech ones?",
      },
      {
        role: "agent",
        text: "Done. The tech profiles are at the top, sorted by adherence. Ready for immediate outreach.",
      },
    ],
  },
  "tpl-compliance-check": {
    pt: [
      {
        role: "candidate",
        text: "O processo desta vaga está em conformidade?",
      },
      {
        role: "agent",
        text: "Revisei o processo: consentimento LGPD coletado, critérios de avaliação documentados e prazos dentro do regulatório. Sinalizei 1 ponto: a justificativa de reprovação de 3 candidatos está incompleta.",
      },
      {
        role: "candidate",
        text: "O que preciso corrigir?",
      },
      {
        role: "agent",
        text: "Basta registrar a justificativa objetiva dessas 3 reprovações. Preparei o rascunho para você revisar e aprovar.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "Is this role's process compliant?",
      },
      {
        role: "agent",
        text: "I reviewed the process: LGPD consent collected, evaluation criteria documented and timelines within regulation. I flagged 1 point: the rejection rationale for 3 candidates is incomplete.",
      },
      {
        role: "candidate",
        text: "What do I need to fix?",
      },
      {
        role: "agent",
        text: "Just record the objective rationale for those 3 rejections. I drafted it for you to review and approve.",
      },
    ],
  },
}

/**
 * Fallback por categoria quando um template não tem diálogo curado por slug.
 * Categorias canonical (AgentCategory): screening, sourcing, communication,
 * analytics, job_management, automation, general.
 */
const CONVERSATIONS_BY_CATEGORY: Record<string, LocalizedConversation> = {
  screening: {
    pt: [
      {
        role: "candidate",
        text: "Tenho experiência relevante para a vaga e quero ser avaliado.",
      },
      {
        role: "agent",
        text: "Analisei o perfil contra os critérios da vaga. Forte aderência nas competências essenciais. Recomendo avançar, com justificativa registrada para o recrutador.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I have relevant experience for the role and want to be evaluated.",
      },
      {
        role: "agent",
        text: "I analyzed the profile against the role's criteria. Strong adherence in the essential skills. I recommend advancing, with rationale recorded for the recruiter.",
      },
    ],
  },
  sourcing: {
    pt: [
      {
        role: "agent",
        text: "Busquei candidatos com fit para a vaga em bancos de talentos e listas. Encontrei 14 perfis aderentes, com competências confirmadas.",
      },
      {
        role: "candidate",
        text: "Não estava buscando, mas o desafio me interessa.",
      },
      {
        role: "agent",
        text: "Marquei como perfil quente e preparei um resumo do match para o recrutador iniciar a abordagem.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "I sourced candidates with fit for the role across talent pools and lists. I found 14 adherent profiles, with confirmed skills.",
      },
      {
        role: "candidate",
        text: "I wasn't looking, but the challenge interests me.",
      },
      {
        role: "agent",
        text: "I marked them as a warm profile and prepared a match summary for the recruiter to start outreach.",
      },
    ],
  },
  communication: {
    pt: [
      {
        role: "agent",
        text: "Oi! Estou cuidando da comunicação do seu processo. Queria confirmar os próximos passos e manter você informado a cada etapa.",
      },
      {
        role: "candidate",
        text: "Obrigado. Quando terei retorno?",
      },
      {
        role: "agent",
        text: "Damos retorno até o fim da semana. Se houver qualquer mudança, eu aviso você antes.",
      },
    ],
    en: [
      {
        role: "agent",
        text: "Hi! I'm handling the communication for your process. I wanted to confirm the next steps and keep you informed at every stage.",
      },
      {
        role: "candidate",
        text: "Thank you. When will I hear back?",
      },
      {
        role: "agent",
        text: "We respond by the end of the week. If anything changes, I'll let you know beforehand.",
      },
    ],
  },
  analytics: {
    pt: [
      {
        role: "candidate",
        text: "Quero entender os números deste processo seletivo.",
      },
      {
        role: "agent",
        text: "Analisei os dados: identifiquei o principal gargalo do funil, o tempo médio por etapa e a taxa de conversão. Sugeri 2 ações concretas para acelerar as contratações.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I want to understand the numbers of this hiring process.",
      },
      {
        role: "agent",
        text: "I analyzed the data: I identified the main funnel bottleneck, the average time per stage and the conversion rate. I suggested 2 concrete actions to speed up hires.",
      },
    ],
  },
  job_management: {
    pt: [
      {
        role: "candidate",
        text: "Preciso de ajuda para montar uma vaga atrativa.",
      },
      {
        role: "agent",
        text: "Montei uma descrição clara e inclusiva, com responsabilidades, skills essenciais e diferenciais. Sugeri uma faixa salarial competitiva para atrair candidaturas qualificadas.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "I need help building an attractive job posting.",
      },
      {
        role: "agent",
        text: "I built a clear, inclusive description, with responsibilities, essential skills and differentiators. I suggested a competitive salary range to attract qualified applications.",
      },
    ],
  },
  automation: {
    pt: [
      {
        role: "candidate",
        text: "Pode cuidar das tarefas repetitivas deste processo?",
      },
      {
        role: "agent",
        text: "Sim. Automatizei as etapas operacionais e organizei o que precisa de atenção. Você recebe um resumo do que foi feito e do que aguarda sua decisão.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "Can you handle the repetitive tasks of this process?",
      },
      {
        role: "agent",
        text: "Yes. I automated the operational steps and organized what needs attention. You get a summary of what was done and what awaits your decision.",
      },
    ],
  },
  general: {
    pt: [
      {
        role: "candidate",
        text: "Como você pode me ajudar neste processo?",
      },
      {
        role: "agent",
        text: "Analiso as informações da vaga e dos candidatos, executo a tarefa que você definiu e devolvo um resumo com a justificativa, para você decidir com confiança.",
      },
    ],
    en: [
      {
        role: "candidate",
        text: "How can you help me in this process?",
      },
      {
        role: "agent",
        text: "I analyze the role and candidate information, run the task you defined, and return a summary with the rationale, so you can decide with confidence.",
      },
    ],
  },
}

export interface GetSampleConversationArgs {
  /** Template slug (preferred). Falls back to category when no curated dialog. */
  slug?: string | null
  /** Template id — only used to look up legacy ids that equal the slug. */
  id?: string | null
  /** AgentCategory — fallback dimension. */
  category?: string | null
  /** Active locale ('pt' | 'en'). Defaults to 'pt'. */
  locale?: string
  /** Compact mode trims to the first 2 turns (card density). */
  compact?: boolean
}

function resolveLocale(locale: string | undefined): "pt" | "en" {
  return locale === "en" ? "en" : "pt"
}

/**
 * Returns the curated conversation turns for a template, resolved by slug first,
 * then by category fallback. Always returns at least the generic 'general'
 * conversation so the UI never renders empty.
 */
export function getSampleConversation({
  slug,
  id,
  category,
  locale,
  compact,
}: GetSampleConversationArgs): ConversationTurn[] {
  const loc = resolveLocale(locale)

  const bySlug =
    (slug && CONVERSATIONS_BY_SLUG[slug]) ||
    (id && CONVERSATIONS_BY_SLUG[id]) ||
    null

  const byCategory =
    (category && CONVERSATIONS_BY_CATEGORY[category]) || null

  const conversation = bySlug ?? byCategory ?? CONVERSATIONS_BY_CATEGORY.general

  const turns = conversation[loc]
  if (compact) {
    return turns.slice(0, 2)
  }
  return turns
}

/** Test/util helper: list of slugs with a curated (non-fallback) dialog. */
export const CURATED_CONVERSATION_SLUGS = Object.keys(CONVERSATIONS_BY_SLUG)
