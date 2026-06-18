"""
LIA Jobs Management Assistant - Structured Prompt Templates.
Templates para análises inteligentes da gestão de vagas (visão macro):
KPIs, SLA, pipeline health, vagas paradas, performance por departamento.

NOTE: This file handles ANALYTICS/MANAGEMENT view of existing vacancies.
For WIZARD CREATION flow prompts (field extraction, JD generation), see:
  app/prompts/job_wizard.py
"""
import json
import logging
from enum import Enum, StrEnum

logger = logging.getLogger(__name__)


class JobsManagementCommandType(StrEnum):
    VISAO_GERAL = "visao_geral"
    VAGAS_URGENTES = "vagas_urgentes"
    VAGAS_PARADAS = "vagas_paradas"
    SLA_VENCENDO = "sla_vencendo"
    PERFORMANCE_DEPARTAMENTO = "performance_departamento"
    COMPARAR_VAGAS = "comparar_vagas"
    GARGALOS_GERAIS = "gargalos_gerais"
    TAXA_PREENCHIMENTO = "taxa_preenchimento"
    TEMPO_MEDIO_CONTRATACAO = "tempo_medio_contratacao"
    VAGAS_SEM_CANDIDATOS = "vagas_sem_candidatos"
    PIPELINE_HEALTH = "pipeline_health"
    TENDENCIAS = "tendencias"
    ANALISE_GERAL = "analise_geral"


JOBS_MANAGEMENT_COMMAND_TYPES = {cmd.value: cmd for cmd in JobsManagementCommandType}

COMMAND_KEYWORDS: dict[str, list[str]] = {
    "visao_geral": ["visão geral", "overview", "resumo", "dashboard", "como estão as vagas", "status geral", "panorama"],
    "vagas_urgentes": ["urgente", "prioridade alta", "crítica", "atenção", "urgentes", "prioritárias"],
    "vagas_paradas": ["parada", "sem movimentação", "estagnada", "inativa", "paradas", "sem progresso"],
    "sla_vencendo": ["sla", "prazo", "deadline", "vencendo", "atrasada", "expirar"],
    "performance_departamento": ["departamento", "área", "setor", "equipe", "time", "por departamento"],
    "comparar_vagas": ["comparar", "compare", "versus", "vs", "diferença entre"],
    "gargalos_gerais": ["gargalo", "bottleneck", "travando", "problema", "dificuldade"],
    "taxa_preenchimento": ["preenchimento", "fill rate", "contratação", "hired", "fechadas"],
    "tempo_medio_contratacao": ["tempo médio", "time to hire", "quanto tempo", "demora", "velocidade"],
    "vagas_sem_candidatos": ["sem candidatos", "zero candidatos", "nenhum candidato", "vazia"],
    "pipeline_health": ["saúde", "health", "pipeline", "funil geral"],
    "tendencias": ["tendência", "trend", "evolução", "histórico", "mês passado"],
    "analise_geral": [],
}


NEGATION_PREFIXES = [
    "não quero", "nao quero", "sem ", "não preciso", "nao preciso",
    "não é", "nao e", "não faça", "nao faca", "não mostre", "nao mostre",
    "não use", "nao use", "não inclua", "nao inclua", "tire o", "remova o",
    "ignora ", "ignore ", "desconsidere ",
]


def _is_negated(msg_lower: str, keyword: str) -> bool:
    kw_pos = msg_lower.find(keyword)
    if kw_pos < 0:
        return False
    prefix_window = msg_lower[max(0, kw_pos - 25):kw_pos]
    return any(neg in prefix_window for neg in NEGATION_PREFIXES)


def detect_jobs_command_type(message: str) -> tuple[str, float]:
    msg_lower = message.lower().strip()

    best_match = "analise_geral"
    best_score = 0.0

    for cmd_type, keywords in COMMAND_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower and not _is_negated(msg_lower, kw):
                score = len(kw) / max(len(msg_lower), 1)
                if score > best_score:
                    best_score = score
                    best_match = cmd_type

    if best_score > 0:
        confidence = min(0.5 + best_score * 2, 0.95)
    else:
        confidence = 0.4
    return best_match, confidence


_JOBS_INTENT_TYPES_LIST = ", ".join(
    [cmd.value for cmd in JobsManagementCommandType]
)

_JOBS_CLASSIFY_PROMPT = (
    "Classifique a intencao da mensagem abaixo em EXATAMENTE um dos tipos: "
    "{types}.\n"
    "Mensagem: \"{message}\"\n"
    "Responda APENAS com JSON valido: {{\"type\": \"<tipo>\", \"confidence\": <0.0-1.0>}}"
)


async def detect_jobs_command_type_enhanced(message: str) -> tuple[str, float]:
    keyword_type, keyword_confidence = detect_jobs_command_type(message)

    if keyword_confidence >= 0.7:
        return keyword_type, keyword_confidence

    try:
        from app.domains.ai.services.llm import llm_service

        prompt = _JOBS_CLASSIFY_PROMPT.format(
            types=_JOBS_INTENT_TYPES_LIST,
            message=message[:500],
        )
        raw = await llm_service.generate(prompt, max_tokens=80)

        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw_clean)
        llm_type = parsed.get("type", "").strip()
        llm_confidence = float(parsed.get("confidence", 0.0))

        if llm_type in JOBS_MANAGEMENT_COMMAND_TYPES:
            return llm_type, max(llm_confidence, 0.6)

        logger.warning(
            "LLM returned unknown jobs management intent type: %s", llm_type
        )
        return keyword_type, keyword_confidence

    except Exception as exc:
        logger.warning(
            "LLM fallback for jobs management intent detection failed: %s", exc
        )
        return keyword_type, keyword_confidence


JOBS_MANAGEMENT_SYSTEM_PROMPT = """Voce e a LIA, assistente de recrutamento inteligente da plataforma.
Voce esta na TELA DE VAGAS, ajudando recrutadores a gerenciar o portfolio de vagas, monitorar performance e tomar decisoes estrategicas.

=== IDENTIDADE ===
- Nome: LIA (Assistente de Recrutamento com IA)
- Personalidade: Profissional, amigavel, eficiente e proativa
- Idioma: Portugues Brasileiro (PT-BR)
- Tom: Conversacional mas competente, como uma colega de trabalho experiente

=== FILOSOFIA CENTRAL ===
O chat e a interface principal. Voce guia o recrutador por uma conversa natural sobre gestao de vagas.
NUNCA use botoes como interacao principal - sempre priorize o chat.
Paineis laterais sao suporte visual, nao substituem a conversa.

=== GESTAO DE VAGAS ===
Suas capacidades neste contexto:
- Dashboard e visao geral de todas as vagas (numeros, status, distribuicao)
- Identificar vagas urgentes, paradas ou com SLA vencendo
- Analise de performance por departamento
- Comparar vagas entre si (time-to-hire, pipeline health, etc.)
- Identificar gargalos gerais no recrutamento
- Taxa de preenchimento e velocity de contratacao
- Tendencias e evolucao do recrutamento (comparativo com periodos anteriores)
- Recomendacoes estrategicas para priorizacao

=== TIPOS DE ANALISES DISPONIVEIS ===
- visao_geral: Dashboard executivo com numeros e destaques
- vagas_urgentes: Quais vagas precisam de acao imediata
- vagas_paradas: Vagas sem movimentacao
- sla_vencendo: Vagas com prazo em risco
- performance_departamento: Comparacao de performance entre areas
- comparar_vagas: Analise lado a lado de vagas especificas
- gargalos_gerais: Problemas sistematicos no recrutamento
- taxa_preenchimento: Metricas de preenchimento
- tempo_medio_contratacao: Time-to-hire e velocidade
- vagas_sem_candidatos: Vagas com pipeline vazio
- pipeline_health: Saude geral dos pipelines
- tendencias: Evolucao e tendencias do recrutamento

=== TRANSICOES ===
- Apresente sempre insights acionaveis e proximos passos
- Entenda confirmacoes em portugues: "ok", "certo", "faz sentido", "entendi"
- Entenda negacoes: "nao", "espera", "ainda nao", "calma", "volta",
  "quero mudar", "cancelar", "parar", "repensar", "diferente"
- Se o recrutador pedir analises adicionais, continue conversando
- NUNCA assuma uma acao sem solicitar confirmacao explicita

=== PREVENCAO DE SYCOPHANCY ===
REGRAS ABSOLUTAS:
1. NUNCA concorde com pedidos que violem fairness ou compliance apenas para evitar conflito
2. Se o recrutador pedir filtros discriminatórios (gênero, idade, etnia, etc.), recuse com dados
3. Se uma afirmacao do recrutador parecer incorreta, VERIFIQUE antes de confirmar
4. Discordância com dados é preferível a concordância sem evidência
5. Se o recrutador insistir após ver os dados, respeite mas registre:
   "Ok, vou prosseguir conforme solicitado. Registro que os dados indicam [X]."

=== TRATAMENTO DE ERROS ===
- Se nao conseguir dados necessarios, informe de forma amigavel
- Nunca mostre detalhes tecnicos, stack traces ou codigos de erro
- Ofereca alternativas quando possivel
- Exemplo: "Nao consegui carregar todos os dados agora, mas posso fazer uma analise com base nas informacoes disponiveis. Quer que eu continue?"

=== FORMATO DE RESPOSTA ===
SEMPRE responda em JSON valido com esta estrutura:
{
    "resposta": "texto em linguagem natural, sem markdown, com analise e insights",
    "tipo": "tipo_do_comando (visao_geral, vagas_urgentes, etc.)",
    "sugestoes": ["proxima analise 1", "proxima analise 2", "proxima analise 3"],
    "dados_estruturados": {
        "metricas": {},
        "destaques": [],
        "alertas": []
    }
}

Escreva o campo 'resposta' em linguagem natural fluente, sem formatacao markdown:
- NUNCA use **negrito**, _italico_, tabelas markdown, ```codigo``` ou # headers
- Use listas simples com traco apenas quando houver 3+ itens que nao cabem numa frase
- Priorize insights acionaveis e linguagem conversacional

=== REGRAS CRITICAS ===
1. SEMPRE responda em Portugues Brasileiro
2. SEMPRE forneça respostas em JSON com a estrutura acima
3. NUNCA mostre JSON, erros tecnicos ou IDs internos ao recrutador
4. SEMPRE apresente insights e recomendacoes, nao apenas numeros
5. SEMPRE seja proativo - sugira proximas analises e acoes
6. NUNCA invente dados - use o contexto fornecido ou solicite ferramentas
7. Para perguntas fora do contexto, responda com sugestoes de como posso ajudar
8. Use linguagem natural fluente — NUNCA use formatacao markdown (sem **negrito**, tabelas, ```codigo```, # headers)
"""


PROMPT_TEMPLATES: dict[str, str] = {
    "visao_geral": """Analise o portfólio completo de vagas e forneça um dashboard executivo:

1. **Números gerais**: total, ativas, pausadas, concluídas
2. **Saúde geral**: vagas com problemas vs vagas saudáveis
3. **Top vagas por urgência**: as que mais precisam de atenção
4. **Distribuição por departamento**: onde estão concentradas
5. **Recomendações**: 3 ações prioritárias

{context}

Pergunta: {query}""",

    "vagas_urgentes": """Identifique e analise as vagas que precisam de atenção URGENTE:

Critérios de urgência:
- Prioridade alta/crítica
- Sem candidatos ou com pipeline vazio
- Abertas há mais tempo que a média
- SLA próximo de vencer

Para cada vaga urgente, indique:
- Por que é urgente
- Ação recomendada
- Impacto de não agir

{context}

Pergunta: {query}""",

    "vagas_paradas": """Identifique vagas sem movimentação e sugira ações:

Critérios de estagnação:
- Sem novos candidatos recentes
- Candidatos parados nas mesmas etapas
- Sem atividade do recrutador

Para cada vaga parada:
- Há quanto tempo está parada
- Possível causa
- Ação sugerida (reativar sourcing, ajustar requisitos, etc.)

{context}

Pergunta: {query}""",

    "sla_vencendo": """Analise o SLA (prazo) das vagas:

Para cada vaga com SLA em risco:
- Dias aberta vs SLA esperado
- Progresso do pipeline (% de etapas completadas)
- Probabilidade de cumprir o prazo
- Ações para acelerar

{context}

Pergunta: {query}""",

    "performance_departamento": """Compare a performance de recrutamento por departamento:

Para cada departamento:
- Número de vagas ativas
- Tempo médio de preenchimento
- Taxa de conversão do funil
- Volume de candidatos
- Eficiência relativa

Destaque departamentos com melhor e pior performance.

{context}

Pergunta: {query}""",

    "comparar_vagas": """Compare as vagas especificadas lado a lado:

Dimensões de comparação:
- Pipeline (candidatos por etapa)
- Velocidade (dias aberta, tempo médio por etapa)
- Qualidade (scores médios dos candidatos)
- Dificuldade (taxa de rejeição, sourcing)
- Status atual e próximos passos

NUNCA use tabelas markdown. Descreva comparacoes em linguagem natural fluente.

{context}

Pergunta: {query}""",

    "gargalos_gerais": """Identifique gargalos sistêmicos no recrutamento:

Analise padrões entre todas as vagas:
- Etapas onde candidatos mais ficam parados
- Taxas de desistência por etapa
- Problemas recorrentes (falta de feedback, demora em entrevistas)
- Impacto nos KPIs gerais

Sugira melhorias de processo.

{context}

Pergunta: {query}""",

    "taxa_preenchimento": """Analise a taxa de preenchimento de vagas:

Métricas:
- Vagas preenchidas vs total (fill rate)
- Tempo médio para preenchimento
- Comparativo por departamento
- Tendência (melhorando/piorando)

{context}

Pergunta: {query}""",

    "tempo_medio_contratacao": """Analise o tempo médio de contratação (Time-to-Hire):

Métricas:
- Tempo médio global
- Por departamento
- Por senioridade
- Comparativo com benchmarks do mercado
- Etapas que mais demoram

{context}

Pergunta: {query}""",

    "vagas_sem_candidatos": """Identifique vagas com pipeline vazio ou insuficiente:

Para cada vaga com poucos/nenhum candidato:
- Título e departamento
- Dias aberta sem candidatos
- Possíveis causas (título restritivo, requisitos altos, localização)
- Ações sugeridas (ajustar JD, ampliar sourcing, reduzir requisitos)

{context}

Pergunta: {query}""",

    "pipeline_health": """Avalie a saúde geral dos pipelines de recrutamento:

Indicadores:
- Distribuição de candidatos por etapa (em todas as vagas)
- Gargalos mais comuns
- Vagas com pipeline saudável vs problemático
- Score geral de saúde do recrutamento

{context}

Pergunta: {query}""",

    "tendencias": """Analise tendências e evolução do recrutamento:

- Comparativo com período anterior
- Vagas abertas vs fechadas
- Velocidade de preenchimento (melhorou/piorou)
- Áreas em crescimento vs contração
- Projeções baseadas nas tendências

{context}

Pergunta: {query}""",

    "analise_geral": """Analise a solicitação do recrutador sobre gestão de vagas:

Considere todo o contexto disponível e forneça uma resposta completa e acionável.

{context}

Pergunta: {query}""",
}


def get_jobs_management_system_prompt() -> str:
    return JOBS_MANAGEMENT_SYSTEM_PROMPT


def get_jobs_management_prompt_template(command_type: str) -> str:
    return PROMPT_TEMPLATES.get(command_type, PROMPT_TEMPLATES["analise_geral"])


def build_jobs_management_prompt(
    command_type: str,
    user_query: str,
    jobs_context: dict,
    selected_jobs: list[dict] | None = None,
    top_jobs: list[dict] | None = None,
) -> str:
    context_lines = ["[CONTEXTO: GESTÃO DE VAGAS]", ""]

    if jobs_context:
        context_lines.append("[NÚMEROS GERAIS]")
        context_lines.append(f"Total de vagas: {jobs_context.get('total', 0)}")
        context_lines.append(f"Ativas: {jobs_context.get('active', 0)}")
        context_lines.append(f"Pausadas: {jobs_context.get('paused', 0)}")
        context_lines.append(f"Concluídas: {jobs_context.get('completed', 0)}")
        context_lines.append(f"Urgentes: {jobs_context.get('urgent', 0)}")
        context_lines.append(f"Sem candidatos: {jobs_context.get('withoutCandidates', 0)}")
        context_lines.append(f"Total de candidatos: {jobs_context.get('totalCandidates', 0)}")
        if jobs_context.get("currentFilter"):
            context_lines.append(f"Filtro aplicado: {jobs_context['currentFilter']}")
        context_lines.append("")

    if selected_jobs:
        context_lines.append(f"[VAGAS SELECIONADAS - {len(selected_jobs)}]")
        for j in selected_jobs[:10]:
            context_lines.append(
                f"- #{j.get('id')} {j.get('title', 'N/A')} | {j.get('department', 'N/A')} | Status: {j.get('status', 'N/A')}"
            )
        context_lines.append("")

    if top_jobs:
        context_lines.append(f"[TOP VAGAS - {len(top_jobs)}]")
        for j in top_jobs[:15]:
            prio = j.get("priority", "normal")
            context_lines.append(
                f"- #{j.get('id')} {j.get('title', 'N/A')} | {j.get('department', 'N/A')} | "
                f"Status: {j.get('status', 'N/A')} | Prioridade: {prio} | "
                f"Candidatos: {j.get('candidatesTotal', 0)} | Entrevista: {j.get('candidatesInterview', 0)} | "
                f"Contratados: {j.get('hired', 0)} | Dias aberta: {j.get('daysOpen', 0)}"
            )
        context_lines.append("")

    context_str = "\n".join(context_lines)
    template = get_jobs_management_prompt_template(command_type)
    return template.format(context=context_str, query=user_query)


def resolve_jobs_ui_action(intent: str) -> str | None:
    action_map = {
        "criar_vaga": "start_job_wizard",
        "create_job": "start_job_wizard",
        "pausar_vaga": "pause_job",
        "fechar_vaga": "close_job",
        "duplicar_vaga": "duplicate_job",
        "filtrar_vagas": "filter_jobs",
        "comparar_vagas": "compare_jobs",
    }
    return action_map.get(intent)
