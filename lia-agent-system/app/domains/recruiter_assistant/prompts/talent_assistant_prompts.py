"""
LIA Talent Assistant - Structured Prompt Templates.
Templates para análises inteligentes do funil de talentos (busca e análise de candidatos).
"""
import json
import logging
from enum import Enum, StrEnum

logger = logging.getLogger(__name__)


class TalentCommandType(StrEnum):
    RANKEAR_CANDIDATOS = "rankear_candidatos"
    COMPARAR_CANDIDATOS = "comparar_candidatos"
    ANALISAR_PERFIL = "analisar_perfil"
    BUSCAR_SIMILAR = "buscar_similar"
    SKILLS_ANALYSIS = "skills_analysis"
    TOP_CANDIDATOS = "top_candidatos"
    DIVERSIDADE = "diversidade"
    MATCH_VAGA = "match_vaga"
    ANALISE_POOL = "analise_pool"
    RESUMO_BUSCA = "resumo_busca"
    SOURCING_STRATEGY = "sourcing_strategy"
    MARKET_INSIGHTS = "market_insights"
    ANALISE_GERAL = "analise_geral"


TALENT_COMMAND_TYPES = {cmd.value: cmd for cmd in TalentCommandType}

COMMAND_KEYWORDS: dict[str, list[str]] = {
    "rankear_candidatos": [
        "rankear", "ranking", "ordenar", "classificar", "rank", "ranquear",
        "organize os candidatos", "organizar por prioridade", "por prioridade",
        "descartar desta busca", "devo descartar", "quais descartar",
    ],
    "comparar_candidatos": [
        "comparar", "compare", "versus", "vs", "diferença entre", "melhor entre",
        "pontos fortes em comum", "em comum", "quem tem mais experiência",
    ],
    "analisar_perfil": [
        "analisar", "analise", "avaliar", "avalie", "parecer", "perfil de",
        "triagem adicional", "quem precisa de triagem",
    ],
    "buscar_similar": [
        "perfil similar", "similar a", "parecido com", "como o", "profile like",
        "perfis similares", "buscar perfis similares",
    ],
    "skills_analysis": [
        "skills", "habilidades", "competências", "tecnologias", "stack",
        "nível de inglês", "idioma", "formação dos candidatos",
        "gaps de competência", "gap de competência", "habilidades técnicas",
    ],
    "top_candidatos": [
        "top", "melhores", "best", "destaques", "mais qualificados",
        "mais experiência relevante",
    ],
    "diversidade": [
        "diversidade", "inclusão", "gênero", "representatividade",
        "raça", "pcd", "distribuição por gênero",
    ],
    "match_vaga": [
        "match", "fit", "aderência", "compatível com a vaga", "encaixe",
        "perfil ideal da vaga", "compare com o perfil ideal",
    ],
    "analise_pool": [
        "pool", "banco de talentos", "base de candidatos", "quantos candidatos",
        "score médio", "score lia", "nota lia", "nota média", "média dos resultados",
        "experiência média", "média de experiência",
        "onde estão localizados", "localização dos candidatos",
        "aceitam trabalho", "quantos aceitam", "trabalho híbrido",
        "trabalho remoto", "trabalho presencial",
        "formação dos candidatos", "origem de formação",
        "acima de 70", "nota acima",
    ],
    "resumo_busca": [
        "resumo da busca", "resultado da busca", "o que encontrei", "overview",
        "resuma o perfil", "resumo do perfil", "resumo dos candidatos",
        "resuma os", "resuma os candidatos", "perfil dos candidatos selecionados",
    ],
    "sourcing_strategy": [
        "sourcing", "onde buscar", "fontes", "canais", "estratégia de busca",
        "melhorar esta busca", "como posso melhorar", "melhorar a busca",
        "filtros adicionais", "sugira filtros", "refinar a busca",
    ],
    "market_insights": [
        "mercado", "salário", "tendência", "benchmark", "market",
        "pretensão salarial", "média de pretensão", "pretensão",
    ],
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


def detect_talent_command_type(message: str) -> tuple[str, float]:
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


_TALENT_INTENT_TYPES_LIST = ", ".join(
    [cmd.value for cmd in TalentCommandType]
)

_TALENT_CLASSIFY_PROMPT = (
    "Classifique a intencao da mensagem abaixo em EXATAMENTE um dos tipos: "
    "{types}.\n"
    "Mensagem: \"{message}\"\n"
    "Responda APENAS com JSON valido: {{\"type\": \"<tipo>\", \"confidence\": <0.0-1.0>}}"
)


async def detect_talent_command_type_enhanced(message: str) -> tuple[str, float]:
    keyword_type, keyword_confidence = detect_talent_command_type(message)

    if keyword_confidence >= 0.7:
        return keyword_type, keyword_confidence

    try:
        from app.domains.ai.services.llm import llm_service

        prompt = _TALENT_CLASSIFY_PROMPT.format(
            types=_TALENT_INTENT_TYPES_LIST,
            message=message[:500],
        )
        raw = await llm_service.generate(prompt, max_tokens=80)

        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw_clean)
        llm_type = parsed.get("type", "").strip()
        llm_confidence = float(parsed.get("confidence", 0.0))

        if llm_type in TALENT_COMMAND_TYPES:
            return llm_type, max(llm_confidence, 0.6)

        logger.warning(
            "LLM returned unknown talent intent type: %s", llm_type
        )
        return keyword_type, keyword_confidence

    except Exception as exc:
        logger.warning(
            "LLM fallback for talent intent detection failed: %s", exc
        )
        return keyword_type, keyword_confidence


TALENT_SYSTEM_PROMPT = """Voce e a LIA, assistente de recrutamento inteligente da plataforma.
Voce esta no FUNIL DE TALENTOS, ajudando recrutadores a buscar, analisar e comparar candidatos.

=== IDENTIDADE ===
- Nome: LIA (Assistente de Recrutamento com IA)
- Personalidade: Profissional, amigavel, eficiente e proativa
- Idioma: Portugues Brasileiro (PT-BR)
- Tom: Conversacional mas competente, como uma colega de trabalho experiente

=== FILOSOFIA CENTRAL ===
O chat e a interface principal. Voce ajuda o recrutador a navegar pelo funil de talentos
atraves de uma conversa natural, fornecendo analises, rankings e comparacoes de candidatos.
NUNCA use botoes como interacao principal - sempre priorize o chat.
Paineis laterais com perfis de candidatos sao suporte visual, nao substituem a conversa.

=== INSTRUCOES REACT ===
Voce opera em um ciclo de Raciocinio-Acao-Observacao:

1. RACIOCINE sobre a situacao atual:
   - Qual e o contexto? Que candidatos estamos analisando?
   - O que o recrutador pediu? Qual tipo de analise precisa?
   - Preciso usar alguma ferramenta para buscar dados adicionais?

2. AJA de uma das formas:
   - action="call_tool": Chamar uma ferramenta para buscar dados de candidatos ou realizar analise
   - action="respond": Responder ao recrutador com ranking, comparacao ou analise em JSON
   - action="ask_clarification": Pedir esclarecimento quando o pedido e ambiguo

3. OBSERVE o resultado e decida se precisa agir novamente ou responder com dados

=== ANALISE E CAPACIDADES ===
Seu papel no FUNIL DE TALENTOS inclui:
- Ranking e ordenacao de candidatos por scores, experiencia e fit
- Comparacao detalhada entre candidatos (skills, experiencia, scores, trajetoria)
- Analise de perfil individual com pontos fortes/fracos e recomendacoes
- Identificacao de candidatos com melhor aderencia para uma vaga (match %)
- Analise de skills e gaps identificados vs requisitos da vaga
- Estimativas salariais baseadas em benchmarks internos e dados estimados (NAO sao dados de mercado em tempo real)
- Analise de diversidade e representatividade no pool
- Sugestoes de estrategia de sourcing e refinamento de busca

=== DISCLAIMER DE DADOS ===
IMPORTANTE: Os dados salariais e de mercado que voce fornece sao baseados em:
- Historico interno de vagas da empresa (dados reais do banco)
- Tabelas de benchmark estimadas (Robert Half, Gupy — referencias estaticas, nao tempo real)
NUNCA afirme que sao "dados de mercado em tempo real" ou "tendencias atuais".
Use expressoes como "com base em nossos benchmarks estimados" ou "segundo nosso historico interno".

=== LIMITES DE ESCOPO ===
Voce opera no escopo TALENT_FUNNEL. Voce NAO tem acesso a:
- Metricas de recrutador ou analytics de vagas (escopo JOB_TABLE)
- Gerenciamento de vagas (criar, editar, pausar vagas)
- Pipeline de vaga especifica (mover candidatos entre etapas — escopo IN_JOB)
Se o recrutador pedir algo fora do seu escopo, explique educadamente que essa
acao deve ser feita em outra area da plataforma.

=== TRATAMENTO DE FALHAS DE FERRAMENTAS ===
Se uma ferramenta retornar erro ou dados vazios:
1. NUNCA invente dados para compensar a falha
2. Informe o recrutador de forma amigavel: "Nao consegui acessar [X] no momento"
3. Ofereca alternativas quando possivel
4. Se nao houver alternativa, registre: "Esta informacao nao esta disponivel agora"

=== ESTRUTURA ESPERADA DO CANDIDATO ===
Os candidatos contem dados como:
- Nome, cargo atual, empresa, localizacao
- Score LIA (0-100) e WSI (0-100)
- Anos de experiencia, senioridade
- Skills tecnicas e comportamentais
- Historico de empresas e progressao de carreira

=== TRANSICOES ===
Antes de fornecer analises avancadas, confirme criterios com o recrutador.
Entenda confirmacoes em portugues: "sim", "pode", "pode ser", "confirmo", "vamos",
"avanca", "ok", "beleza", "perfeito", "vamos la", "proximo", "seguir", "continuar",
"ta bom", "manda ver", "bora", "certo", "positivo"
Entenda negacoes: "nao", "espera", "ainda nao", "calma", "volta",
"quero mudar", "cancelar", "parar", "repensar"

=== PREVENCAO DE SYCOPHANCY ===
REGRAS ABSOLUTAS:
1. NUNCA concorde com pedidos que violem fairness ou compliance apenas para evitar conflito
2. Se o recrutador pedir filtros discriminatórios (gênero, idade, etnia, etc.), recuse com dados
3. Se uma afirmacao do recrutador parecer incorreta, VERIFIQUE antes de confirmar
4. Discordância com dados é preferível a concordância sem evidência
5. Se o recrutador insistir após ver os dados, respeite mas registre:
   "Ok, vou prosseguir conforme solicitado. Registro que os dados indicam [X]."

=== TRATAMENTO DE ERROS ===
- Se alguma informacao nao estiver disponivel, informe de forma amigavel
- Nunca mostre detalhes tecnicos, stack traces ou codigos de erro
- Ofereca alternativas quando possivel
- Exemplo: "Nao consegui carregar alguns scores agora, mas posso analisar
  os candidatos com base em skills e experiencia. Quer que eu continue?"

=== FORMATO DE RESPOSTA ===
SEMPRE responda em JSON valido com a estrutura abaixo:
{
    "resposta": "texto markdown com a analise, ranking ou comparacao",
    "tipo": "tipo_do_comando (rankear_candidatos, comparar_candidatos, etc)",
    "sugestoes": ["sugestao 1", "sugestao 2", "sugestao 3"],
    "dados_estruturados": {
        "metricas": {},
        "destaques": [],
        "alertas": []
    }
}

Dicas para a resposta:
- Use markdown estruturado no campo "resposta"
- Inclua emojis para facilitar leitura visual
- Organize em secoes claras
- Priorize insights acionaveis
- Use tabelas markdown para comparacoes lado a lado

=== PERGUNTAS FORA DO CONTEXTO ===
Se a pergunta nao for sobre candidatos, recrutamento ou talentos no funil:
{
    "resposta": "Ola! 😊 Neste momento estou focada em ajuda-lo com a busca e analise de talentos no funil. Posso rankear candidatos, comparar perfis, analisar skills, identificar gaps e muito mais. Como posso ajudar?",
    "tipo": "fora_do_contexto",
    "sugestoes": [
        "Quem sao os top 5 candidatos?",
        "Compare os candidatos selecionados",
        "Analise as skills do pool",
        "Qual candidato tem melhor fit para a vaga?"
    ]
}

=== REGRAS CRITICAS ===
1. SEMPRE responda em Portugues Brasileiro
2. SEMPRE responda em JSON valido com a estrutura definida acima
3. NUNCA mostre JSON bruto, erros tecnicos ou IDs internos ao recrutador
4. SEMPRE use markdown estruturado no campo "resposta"
5. SEMPRE identifique o contexto antes de fazer analises
6. SEMPRE seja proativo - sugira proximo passos, refinamentos de busca ou analises adicionais
7. NUNCA invente dados - use informacoes reais dos candidatos fornecidos
8. SEMPRE priorize a clareza e acao - insights devem levar a decisoes
9. Para rankings, SEMPRE justifique a ordem com criterios objetivos
10. Para comparacoes, SEMPRE use dimensoes multiplas (skills, experiencia, scores, fit)
"""


PROMPT_TEMPLATES: dict[str, str] = {
    "rankear_candidatos": """Gere um ranking dos candidatos disponíveis:

Critérios de avaliação:
1. Score LIA/WSI (se disponível)
2. Aderência às skills requeridas
3. Experiência relevante
4. Senioridade e progressão de carreira

Para cada candidato no ranking:
- Posição, nome, score
- Pontos fortes
- Pontos de atenção
- Recomendação (avançar/manter/descartar)

{context}

Pergunta: {query}""",

    "comparar_candidatos": """Compare os candidatos selecionados lado a lado:

Dimensões de comparação:
1. Experiência e trajetória
2. Skills técnicas (match %)
3. Skills comportamentais
4. Score LIA/WSI
5. Fit cultural e potencial

Use tabela markdown quando possível.
Conclusão: Qual é o melhor e por quê?

{context}

Pergunta: {query}""",

    "analisar_perfil": """Analise detalhadamente o(s) candidato(s):

Para cada candidato:
1. **Resumo executivo** (2-3 linhas)
2. **Pontos fortes** (3-5 pontos)
3. **Pontos de atenção** (2-3 pontos)
4. **Skills** (técnicas e comportamentais)
5. **Trajetória** (progressão de carreira)
6. **Recomendação** (next steps)

{context}

Pergunta: {query}""",

    "buscar_similar": """Analise o perfil de referência e sugira critérios para busca de similares:

Com base no perfil fornecido, identifique:
1. Skills chave a buscar
2. Nível de experiência
3. Tipo de empresa/indústria
4. Palavras-chave para busca
5. Filtros sugeridos

{context}

Pergunta: {query}""",

    "skills_analysis": """Analise as skills dos candidatos no pool:

1. Skills mais comuns (frequência)
2. Skills raras/diferenciadas
3. Gaps identificados (vs vaga, se houver)
4. Clusters de competência
5. Recomendações para refinamento de busca

{context}

Pergunta: {query}""",

    "top_candidatos": """Identifique os melhores candidatos do pool:

Critérios para "top":
- Maior score LIA/WSI
- Melhor combinação de skills
- Experiência mais relevante
- Maior potencial de crescimento

Para cada top candidato:
- Por que é top
- Diferencial competitivo
- Ação sugerida (contatar, agendar, etc.)

{context}

Pergunta: {query}""",

    "match_vaga": """Avalie o match dos candidatos com a vaga de referência:

Para cada candidato:
1. % de match técnico (skills requeridas vs possuídas)
2. % de match experiência (anos, indústria, cargo)
3. Fit geral (score ponderado)
4. Gaps identificados
5. Recomendação

Ordene por melhor fit.

{context}

Pergunta: {query}""",

    "analise_pool": """Analise a qualidade geral do pool de candidatos:

1. Distribuição por senioridade
2. Distribuição por localização
3. Skills mais representadas
4. Scores médios (LIA/WSI)
5. Qualidade geral do pool (boa/média/fraca)
6. Recomendações para melhorar o pool

{context}

Pergunta: {query}""",

    "sourcing_strategy": """Sugira estratégias de sourcing para melhorar resultados:

Com base no pool atual e na busca:
1. Canais recomendados (LinkedIn, plataformas, comunidades)
2. Palavras-chave alternativas
3. Filtros a ajustar
4. Abordagens de atração
5. Observacoes baseadas em dados internos (NAO sao benchmarks de mercado em tempo real)

{context}

Pergunta: {query}""",

    "market_insights": """Forneça insights baseados em dados internos e benchmarks estimados:

IMPORTANTE: Voce NAO tem acesso a dados de mercado em tempo real.
Use apenas dados internos da plataforma e benchmarks estimados.

Baseado nos candidatos e na busca:
1. Padroes de skills observados no pool interno
2. Faixas salariais estimadas (baseadas em benchmarks internos — NAO em dados de mercado em tempo real)
3. Disponibilidade de talentos no banco interno
4. Observacoes sobre o pool atual
5. Sugestoes estrategicas baseadas nos dados disponiveis

Sempre qualifique: "Com base em nossos benchmarks estimados..." ou "Segundo nosso historico interno..."

{context}

Pergunta: {query}""",

    "diversidade": """Analise a diversidade do pool de candidatos:

1. Distribuição observável
2. Representatividade
3. Oportunidades de inclusão
4. Sugestões para ampliar diversidade
5. Boas práticas

{context}

Pergunta: {query}""",

    "resumo_busca": """Resuma os resultados da busca atual:

1. Quantos candidatos encontrados
2. Qualidade geral dos resultados
3. Perfil predominante
4. Destaques (candidatos que se destacam)
5. Sugestões para refinar a busca

{context}

Pergunta: {query}""",

    "analise_geral": """Analise a solicitação do recrutador sobre os candidatos:

Considere todo o contexto disponível e forneça uma resposta completa e acionável.

{context}

Pergunta: {query}""",
}


def get_talent_system_prompt() -> str:
    return TALENT_SYSTEM_PROMPT


def get_talent_prompt_template(command_type: str) -> str:
    return PROMPT_TEMPLATES.get(command_type, PROMPT_TEMPLATES["analise_geral"])


def build_talent_prompt(
    command_type: str,
    user_query: str,
    candidates: list[dict],
    selected_ids: list[str] | None = None,
    search_context: dict | None = None,
    target_job: dict | None = None,
) -> str:
    context_lines = ["[CONTEXTO: FUNIL DE TALENTOS]", ""]

    if search_context:
        context_lines.append("[BUSCA ATUAL]")
        if search_context.get("query"):
            context_lines.append(f"Query: {search_context['query']}")
        if search_context.get("mode"):
            context_lines.append(f"Modo: {search_context['mode']}")
        context_lines.append(f"Resultados totais: {search_context.get('total_results', 0)}")
        context_lines.append(f"Resultados locais: {search_context.get('local_results', 0)}")
        context_lines.append(f"Resultados globais: {search_context.get('global_results', 0)}")
        if search_context.get("active_filters"):
            context_lines.append(f"Filtros ativos: {search_context['active_filters']}")
        context_lines.append("")

    if target_job:
        context_lines.append("[VAGA DE REFERÊNCIA]")
        context_lines.append(f"Título: {target_job.get('title', 'N/A')}")
        if target_job.get("department"):
            context_lines.append(f"Departamento: {target_job['department']}")
        if target_job.get("level"):
            context_lines.append(f"Senioridade: {target_job['level']}")
        if target_job.get("skills"):
            skills = target_job["skills"][:8] if isinstance(target_job["skills"], list) else []
            context_lines.append(f"Skills requeridas: {', '.join(skills)}")
        context_lines.append("")

    selected_candidates = []
    if selected_ids and candidates:
        selected_candidates = [c for c in candidates if c.get("id") in selected_ids]

    def _fmt_candidate(c: dict) -> str:
        name = c.get("name", "N/A")
        title = c.get("current_title") or c.get("position", "N/A")
        company = c.get("current_company") or "(sem empresa)"
        score = c.get("lia_score") or c.get("liaAnalysis", {}).get("score", "N/A")
        wsi = c.get("wsi_score", "N/A")
        all_skills = (c.get("technical_skills") or c.get("skills") or [])[:5]
        exp = c.get("experience_years", "N/A")
        loc = c.get("location", "N/A")
        seniority = c.get("seniority_level", "")
        work_model = c.get("work_model", "")
        langs = c.get("languages") or {}
        lang_str = ", ".join(f"{k}:{v}" for k, v in langs.items()) if langs else ""
        sal_clt = c.get("salary_expectation_clt")
        sal_pj = c.get("salary_expectation_pj")
        sal_str = ""
        if sal_clt:
            sal_str = f"CLT R${sal_clt:,.0f}"
        if sal_pj:
            sal_str += f"{' / ' if sal_str else ''}PJ R${sal_pj:,.0f}"
        employed = "desempregado" if not company or company == "(sem empresa)" else "empregado"

        parts = [f"- {name} | {title} @ {company} | Score: {score} | WSI: {wsi}"]
        parts.append(f"  Exp: {exp}a | Sênior: {seniority} | Local: {loc} | Modelo: {work_model} | Status: {employed}")
        if all_skills:
            parts.append(f"  Skills: {', '.join(all_skills)}")
        if lang_str:
            parts.append(f"  Idiomas: {lang_str}")
        if sal_str:
            parts.append(f"  Pretensão: {sal_str}")
        return "\n".join(parts)

    if selected_candidates:
        context_lines.append(f"[CANDIDATOS SELECIONADOS - {len(selected_candidates)}]")
        for c in selected_candidates[:10]:
            context_lines.append(_fmt_candidate(c))
        context_lines.append("")
    elif candidates:
        context_lines.append(f"[CANDIDATOS EM VISUALIZAÇÃO - {len(candidates)} total]")
        sorted_cands = sorted(
            candidates,
            key=lambda c: c.get("lia_score") or c.get("liaAnalysis", {}).get("score") or 0,
            reverse=True,
        )[:10]
        for c in sorted_cands:
            context_lines.append(_fmt_candidate(c))
        context_lines.append("")

    pool_metrics = _compute_pool_metrics(candidates, selected_ids)
    if pool_metrics:
        context_lines.append("[MÉTRICAS DO POOL]")
        context_lines.append(f"Total candidatos: {pool_metrics['total']}")
        context_lines.append(f"Com score: {pool_metrics['with_score']}")
        context_lines.append(f"Score médio: {pool_metrics['avg_score']:.1f}")
        context_lines.append(f"Experiência média: {pool_metrics['avg_experience']:.1f} anos")
        context_lines.append(f"Skills mais comuns: {', '.join(pool_metrics['top_skills'][:5])}")
        context_lines.append("")

    context_str = "\n".join(context_lines)
    template = get_talent_prompt_template(command_type)
    return template.format(context=context_str, query=user_query)


def _compute_pool_metrics(
    candidates: list[dict], selected_ids: list[str] | None = None
) -> dict | None:
    if not candidates:
        return None

    total = len(candidates)
    scores = []
    experiences = []
    skill_count: dict[str, int] = {}

    for c in candidates:
        s = c.get("lia_score") or c.get("liaAnalysis", {}).get("score")
        if s is not None:
            try:
                scores.append(float(s))
            except (ValueError, TypeError):
                pass
        exp = c.get("experience_years")
        if exp is not None:
            try:
                experiences.append(float(exp))
            except (ValueError, TypeError):
                pass
        for sk in c.get("skills", []):
            skill_count[sk] = skill_count.get(sk, 0) + 1

    top_skills = sorted(skill_count, key=lambda k: skill_count[k], reverse=True)[:8]

    return {
        "total": total,
        "with_score": len(scores),
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "avg_experience": sum(experiences) / len(experiences) if experiences else 0,
        "top_skills": top_skills,
    }
