"""
LIA Kanban Assistant - Structured Prompt Templates.
Templates para análises inteligentes do pipeline de recrutamento.
"""
from enum import Enum, StrEnum


class KanbanCommandType(StrEnum):
    RANKEAR_CANDIDATOS = "rankear_candidatos"
    PERFORMANCE_FUNIL = "performance_funil"
    GARGALOS_PROCESSO = "gargalos_processo"
    COMPARAR_CANDIDATOS = "comparar_candidatos"
    RESUMIR_PERFIL = "resumir_perfil"
    CANDIDATOS_ATIVOS = "candidatos_ativos"
    TAXA_CONVERSAO = "taxa_conversao"
    TEMPO_MEDIO = "tempo_medio"
    CANDIDATOS_PARADOS = "candidatos_parados"
    TOP_CANDIDATOS = "top_candidatos"
    MOVER_CANDIDATO = "mover_candidato"
    ENVIAR_EMAIL = "enviar_email"
    DISPARAR_TRIAGEM = "disparar_triagem"
    AGENDAR_ENTREVISTA = "agendar_entrevista"
    SOLICITAR_DADOS = "solicitar_dados"
    ANALISAR_PERFIL = "analisar_perfil"
    APROVAR_CANDIDATO = "aprovar_candidato"
    ANALISE_GERAL = "analise_geral"


KANBAN_COMMAND_TYPES = {cmd.value: cmd for cmd in KanbanCommandType}


LIA_SYSTEM_PROMPT = """Voce e a LIA, assistente de recrutamento inteligente da plataforma.
Voce esta no PIPELINE DE RECRUTAMENTO (Kanban), ajudando recrutadores a gerenciar candidatos em cada etapa do processo seletivo.

=== IDENTIDADE ===
- Nome: LIA (Assistente de Recrutamento com IA)
- Personalidade: Profissional, amigavel, eficiente e proativa
- Idioma: Portugues Brasileiro (PT-BR)
- Tom: Conversacional mas competente, como uma colega de trabalho experiente

=== FILOSOFIA CENTRAL ===
O chat e a interface principal. Voce guia o recrutador por uma conversa natural no gerenciamento do pipeline.
SEMPRE pergunte antes de mover candidatos entre etapas.
Acoes destrutivas (rejeicao, movimentacao em massa) EXIGEM confirmacao explicita.
Paineis laterais sao suporte visual, nao substituem a conversa.

=== INSTRUCOES REACT ===
Voce opera em um ciclo de Raciocinio-Acao-Observacao:

1. RACIOCINE sobre a situacao atual:
   - Em que etapa do pipeline estamos? Qual candidato estamos analisando?
   - O que o recrutador pediu? Que acao devo tomar?
   - Preciso usar alguma ferramenta?

2. AJA de uma das formas:
   - action="call_tool": Chamar uma ferramenta para consultar dados ou executar acao
   - action="respond": Responder ao recrutador com informacoes ou perguntas
   - action="ask_clarification": Pedir esclarecimento quando a intencao e ambigua

3. OBSERVE o resultado e decida se precisa agir novamente ou responder

=== FERRAMENTAS DISPONIVEIS (implementadas e funcionais) ===

**Candidatos:**
- Mover candidato entre etapas (update_candidate_stage) — requer confirmacao
- Mover candidatos em lote (bulk_update_candidates_stage) — requer confirmacao + lista previa
- Rejeitar candidato (reject_candidate) — requer confirmacao dupla
- Adicionar a shortlist (shortlist_candidate)
- Adicionar a lista (add_to_list)
- Ocultar candidato (hide_candidate)
- Iniciar triagem WSI (wsi_screening)

**Comunicacao:**
- Enviar email (send_email)
- Enviar feedback/devolutiva (send_feedback)
- Enviar WhatsApp (send_whatsapp)

**Entrevistas:**
- Agendar entrevista (schedule_interview)

**Consultas e Analytics:**
- Ver detalhes da vaga (get_job_details)
- Ver funil da vaga (get_vacancy_funnel)
- Ver detalhes de candidato (get_candidate_details)
- Resumo de atividades (get_activity_summary)
- Acoes pendentes (get_pending_actions)
- Comparar candidatos (compare_candidates)
- Estatisticas de candidatos (get_candidate_stats)
- Analise de gargalos (get_bottleneck_analysis)
- Velocidade da vaga (get_job_velocity)
- Metricas de qualidade (get_job_quality_metrics)
- Metricas de stakeholders (get_stakeholder_metrics)
- Predicoes (get_prediction_metrics)
- Benchmark da vaga (get_job_benchmark)
- Alertas inteligentes (get_smart_alerts)

=== ACOES CONFIRMACAO OBRIGATORIA ===
Para acoes que alteram dados, voce DEVE usar o fluxo de confirmacao:
1. Apresente ao recrutador o que sera feito e quais candidatos serao afetados
2. Aguarde confirmacao explicita ("confirmo", "sim", "pode")
3. Somente entao execute a acao
Para rejeicao e movimentacao em massa, exija confirmacao DUPLA.

=== TRATAMENTO DE FALHAS DE FERRAMENTAS ===
Se uma ferramenta retornar erro ou dados vazios:
1. NUNCA invente dados para compensar a falha
2. Informe o recrutador: "Nao consegui executar [acao] no momento"
3. Ofereca alternativas ou sugira tentar novamente
4. NUNCA afirme que uma acao foi concluida se a ferramenta falhou

=== MOVIMENTACAO NO PIPELINE ===
- NUNCA mova candidatos sem confirmacao explicita do recrutador
- Antes de mover, explique o motivo e consequencias
- Para rejeicao, SEMPRE peca confirmacao dupla
- Para movimentacao em massa (bulk_update_candidates_stage), liste todos os candidatos antes
- Sempre identifique o candidato antes de executar qualquer acao
- Apresente informacoes relevantes do perfil antes de sugerir movimentacao

=== CONFIRMACOES ===
- Entenda confirmacoes em portugues: "sim", "pode", "confirmo", "mover",
  "avanca", "ok", "beleza", "perfeito", "vamos la", "proximo", "seguir",
  "continuar", "ta bom", "pode ser", "manda ver", "bora", "certo", "positivo"
- Entenda negacoes: "nao", "espera", "ainda nao", "calma", "volta",
  "quero mudar", "cancelar", "parar"
- Para acoes destrutivas, exija palavras fortes: "confirmo", "sim tenho certeza",
  "pode rejeitar", "confirmo a rejeicao"

=== PREVENCAO DE SYCOPHANCY ===
REGRAS ABSOLUTAS:
1. NUNCA concorde com pedidos que violem fairness ou compliance apenas para evitar conflito
2. Se o recrutador pedir filtros discriminatórios (gênero, idade, etnia, etc.), recuse com dados
3. Se uma afirmacao do recrutador parecer incorreta, VERIFIQUE antes de confirmar
4. Discordância com dados é preferível a concordância sem evidência
5. Se o recrutador insistir após ver os dados, respeite mas registre:
   "Ok, vou prosseguir conforme solicitado. Registro que os dados indicam [X]."

=== TRATAMENTO DE ERROS ===
- Se uma ferramenta falhar, informe o recrutador de forma amigavel
- Nunca mostre detalhes tecnicos, stack traces ou codigos de erro
- Ofereca alternativas quando possivel
- Exemplo: "Nao consegui carregar o perfil agora, mas posso tentar novamente. Quer que eu tente?"

=== FORMATO DE RESPOSTA ===
- Use markdown estruturado
- Inclua emojis para facilitar leitura visual
- Organize informacoes em secoes claras
- Priorize insights acionaveis
- Sempre sugira proximos passos
- Responda em portugues natural quando action="respond"

=== PERGUNTAS FORA DO CONTEXTO ===
Se o recrutador fizer uma pergunta que NAO esta relacionada a recrutamento, selecao, candidatos, vagas ou pipeline, responda de forma amigavel e humanizada.

Responda SEMPRE em JSON com esta estrutura para perguntas fora do contexto:
{
    "resposta": "Ola! 😊 Eu ainda estou evoluindo e em breve estarei pronta para atender a todas as suas solicitacoes e esclarecer todas as suas duvidas. Peco desculpas por nao conseguir te ajudar com essa pergunta especifica agora. Neste momento, posso te ajudar com analises e informacoes sobre seus candidatos e vagas. Vamos conversar muito em breve!",
    "tipo": "fora_do_contexto",
    "sugestoes": [
        "Quem sao os melhores candidatos para esta vaga?",
        "Como esta a performance do funil?",
        "Identifique gargalos no processo",
        "Compare os candidatos selecionados"
    ]
}

=== REGRAS CRITICAS ===
1. SEMPRE responda em Portugues Brasileiro
2. NUNCA mova candidatos sem confirmacao explicita
3. NUNCA mostre JSON, erros tecnicos ou IDs internos ao usuario
4. SEMPRE confirme antes de acoes destrutivas (rejeicao, exclusao)
5. SEMPRE identifique o candidato antes de qualquer acao
6. SEMPRE seja proativa - sugira proximos passos e analises
7. NUNCA invente dados - use ferramentas para buscar informacoes reais
8. Para bulk_update_candidates_stage, SEMPRE liste candidatos e peca confirmacao"""


COMMAND_TEMPLATES: dict[str, dict] = {
    KanbanCommandType.RANKEAR_CANDIDATOS.value: {
        "description": "Ordenar candidatos por fit com a vaga",
        "keywords": ["rankear", "ranking", "ordenar", "classificar", "melhores candidatos", "top candidatos", "ordenação"],
        "prompt_template": """## Tarefa: Ranking de Candidatos

Analise os candidatos abaixo e ordene-os por fit com a vaga.

### Contexto da Vaga
{job_context}

### Candidatos para Análise
{candidates_context}

### Instrução
Crie um ranking dos TOP 10 candidatos (ou todos se houver menos de 10), ordenados do melhor para o pior fit com a vaga.

### Formato de Resposta Obrigatório (JSON):
{{
    "ranking": [
        {{
            "posicao": 1,
            "candidato_id": "id",
            "candidato_nome": "nome",
            "score_fit": 95,
            "principais_forcas": ["força 1", "força 2"],
            "principais_gaps": ["gap 1"],
            "justificativa": "Breve justificativa do ranking"
        }}
    ],
    "insights": "Observações gerais sobre o pool de candidatos",
    "recomendacao": "Próximos passos recomendados"
}}""",
        "response_sections": ["ranking", "insights", "recomendacao"],
        "follow_up_prompts": [
            "Compare os 3 primeiros candidatos em detalhes",
            "Quais candidatos precisam de mais avaliação?",
            "Sugira próximos passos para os top 5"
        ]
    },
    
    KanbanCommandType.PERFORMANCE_FUNIL.value: {
        "description": "Análise de métricas do pipeline de recrutamento",
        "keywords": ["performance", "funil", "métricas", "pipeline", "desempenho", "números", "estatísticas",
                     "sugerir melhorias", "melhorias para", "mês vs anterior", "contratações", "trimestre",
                     "performance dos últimos", "análise geral das vagas"],
        "prompt_template": """## Tarefa: Análise de Performance do Funil

Analise as métricas e performance do pipeline desta vaga.

### Contexto da Vaga
{job_context}

### Dados do Pipeline
{pipeline_context}

### Candidatos por Etapa
{candidates_context}

### Instrução
Faça uma análise completa da performance do funil de recrutamento.

### Formato de Resposta Obrigatório (JSON):
{{
    "metricas": {{
        "total_candidatos": 0,
        "por_etapa": {{"etapa": 0}},
        "taxa_conversao_geral": 0,
        "taxa_conversao_por_etapa": {{"etapa1_etapa2": 0}}
    }},
    "performance": {{
        "status": "saudável|atenção|crítico",
        "pontos_fortes": ["ponto 1"],
        "pontos_atencao": ["ponto 1"],
        "benchmark": "Comparação com benchmarks de mercado"
    }},
    "recomendacoes": ["Ação 1", "Ação 2"],
    "insights": "Análise geral do funil"
}}""",
        "response_sections": ["metricas", "performance", "recomendacoes", "insights"],
        "follow_up_prompts": [
            "Quais etapas precisam de mais atenção?",
            "Como posso melhorar a taxa de conversão?",
            "Identifique gargalos no processo"
        ]
    },
    
    KanbanCommandType.GARGALOS_PROCESSO.value: {
        "description": "Identificar onde candidatos ficam parados",
        "keywords": ["gargalo", "gargalos", "travados", "parados", "atraso", "bloqueio", "problema", "lentidão",
                     "processo seletivo", "maior taxa de rejeição", "etapa crítica"],
        "prompt_template": """## Tarefa: Identificação de Gargalos no Processo

Analise o pipeline e identifique onde os candidatos estão ficando parados.

### Contexto da Vaga
{job_context}

### Dados do Pipeline
{pipeline_context}

### Candidatos e Tempo em Cada Etapa
{candidates_context}

### Instrução
Identifique gargalos no processo seletivo e sugira ações corretivas.

### Formato de Resposta Obrigatório (JSON):
{{
    "gargalos": [
        {{
            "etapa": "Nome da etapa",
            "severidade": "alta|média|baixa",
            "candidatos_impactados": 0,
            "tempo_medio_parado": "X dias",
            "causa_provavel": "Explicação",
            "acao_sugerida": "O que fazer"
        }}
    ],
    "candidatos_criticos": [
        {{
            "id": "id",
            "nome": "nome",
            "etapa_atual": "etapa",
            "dias_parado": 0,
            "acao_urgente": "O que fazer"
        }}
    ],
    "plano_acao": ["Ação prioritária 1", "Ação 2"],
    "impacto_estimado": "Descrição do impacto se resolver os gargalos"
}}""",
        "response_sections": ["gargalos", "candidatos_criticos", "plano_acao", "impacto_estimado"],
        "follow_up_prompts": [
            "Quais ações são mais urgentes?",
            "Como priorizar a resolução dos gargalos?",
            "Sugira um plano de ação semanal"
        ]
    },
    
    KanbanCommandType.COMPARAR_CANDIDATOS.value: {
        "description": "Comparação detalhada entre candidatos selecionados",
        "keywords": ["comparar", "compare", "comparação", "versus", "vs", "diferença", "qual melhor", "entre eles", "entre candidatos"],
        "prompt_template": """## Tarefa: Comparação de Candidatos

Compare os candidatos selecionados em detalhes.

### Contexto da Vaga
{job_context}

### Candidatos para Comparação
{selected_candidates_context}

### Instrução
Faça uma comparação detalhada entre os candidatos, destacando pontos fortes e fracos de cada um.

### Formato de Resposta Obrigatório (JSON):
{{
    "comparacao": [
        {{
            "candidato_id": "id",
            "candidato_nome": "nome",
            "score_geral": 85,
            "match_tecnico": 90,
            "match_cultural": 80,
            "pontos_fortes": ["força 1", "força 2"],
            "pontos_fracos": ["fraqueza 1"],
            "diferencial": "O que destaca este candidato"
        }}
    ],
    "analise_comparativa": {{
        "melhor_fit_tecnico": {{"id": "id", "motivo": "explicação"}},
        "melhor_fit_cultural": {{"id": "id", "motivo": "explicação"}},
        "melhor_custo_beneficio": {{"id": "id", "motivo": "explicação"}}
    }},
    "recomendacao_final": {{
        "candidato_recomendado": "id",
        "justificativa": "Por que este candidato",
        "ressalvas": ["O que considerar"]
    }},
    "proximos_passos": ["Passo 1", "Passo 2"]
}}""",
        "response_sections": ["comparacao", "analise_comparativa", "recomendacao_final", "proximos_passos"],
        "follow_up_prompts": [
            "O que perguntar na entrevista de cada um?",
            "Quais gaps precisam ser validados?",
            "Como avaliar o fit cultural de cada candidato?"
        ]
    },
    
    KanbanCommandType.RESUMIR_PERFIL.value: {
        "description": "Resumo executivo de um candidato específico",
        "keywords": ["resumir", "resumo", "perfil", "sobre", "quem é", "me fale sobre", "detalhe"],
        "prompt_template": """## Tarefa: Resumo Executivo de Candidato

Crie um resumo executivo completo do candidato.

### Contexto da Vaga
{job_context}

### Dados do Candidato
{selected_candidates_context}

### Instrução
Gere um resumo executivo completo e acionável sobre o candidato.

### Formato de Resposta Obrigatório (JSON):
{{
    "resumo_executivo": {{
        "candidato_id": "id",
        "candidato_nome": "nome",
        "headline": "Frase resumo do candidato",
        "score_fit": 85,
        "recomendacao": "Recomendado para próxima etapa"
    }},
    "perfil_profissional": {{
        "experiencia_total": "X anos",
        "nivel_senioridade": "Sênior",
        "especializacao": "Área de foco",
        "empresas_destaque": ["Empresa 1"],
        "skills_principais": ["Skill 1", "Skill 2"]
    }},
    "analise_fit": {{
        "match_requisitos": 90,
        "match_cultura": 85,
        "match_expectativas": 80,
        "principais_forcas": ["Força 1", "Força 2"],
        "principais_gaps": ["Gap 1"],
        "riscos": ["Risco potencial"]
    }},
    "perguntas_entrevista": [
        "Pergunta sugerida 1",
        "Pergunta sugerida 2"
    ],
    "proximos_passos": ["Ação recomendada 1"]
}}""",
        "response_sections": ["resumo_executivo", "perfil_profissional", "analise_fit", "perguntas_entrevista", "proximos_passos"],
        "follow_up_prompts": [
            "Quais perguntas fazer na entrevista?",
            "Como validar os gaps identificados?",
            "Compare com outros candidatos no pipeline"
        ]
    },
    
    KanbanCommandType.CANDIDATOS_ATIVOS.value: {
        "description": "Quantos candidatos e distribuição por etapa",
        "keywords": ["quantos", "candidatos ativos", "total", "distribuição", "por etapa",
                     "sem candidatos", "vagas sem", "atenção urgente", "por departamento",
                     "vagas abertas", "listar vagas"],
        "prompt_template": """## Tarefa: Análise de Candidatos Ativos

Analise a distribuição atual de candidatos no pipeline.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Instrução
Forneça uma visão clara da distribuição de candidatos por etapa.

### Formato de Resposta Obrigatório (JSON):
{{
    "visao_geral": {{
        "total_candidatos": 0,
        "candidatos_ativos": 0,
        "candidatos_finalizados": 0,
        "taxa_atividade": "X%"
    }},
    "distribuicao_etapas": [
        {{
            "etapa": "Nome",
            "quantidade": 0,
            "percentual": "X%",
            "status": "saudável|atenção|crítico"
        }}
    ],
    "alertas": [
        {{
            "tipo": "warning|info|critical",
            "mensagem": "Descrição do alerta"
        }}
    ],
    "recomendacoes": ["Recomendação 1"]
}}""",
        "response_sections": ["visao_geral", "distribuicao_etapas", "alertas", "recomendacoes"],
        "follow_up_prompts": [
            "Quais candidatos precisam de atenção?",
            "Como está a performance do funil?",
            "Identifique gargalos no processo"
        ]
    },
    
    KanbanCommandType.TAXA_CONVERSAO.value: {
        "description": "Análise de conversão entre etapas",
        "keywords": ["conversão", "taxa", "aprovação", "reprovação", "passagem", "avanço"],
        "prompt_template": """## Tarefa: Análise de Taxa de Conversão

Analise as taxas de conversão entre etapas do funil.

### Contexto da Vaga
{job_context}

### Dados do Pipeline
{pipeline_context}

### Histórico de Movimentações
{candidates_context}

### Instrução
Calcule e analise as taxas de conversão entre cada etapa.

### Formato de Resposta Obrigatório (JSON):
{{
    "conversao_geral": {{
        "inicio_fim": "X%",
        "benchmark_mercado": "Y%",
        "status": "acima|dentro|abaixo da média"
    }},
    "conversao_por_etapa": [
        {{
            "de_etapa": "Etapa 1",
            "para_etapa": "Etapa 2",
            "taxa": "X%",
            "aprovados": 0,
            "reprovados": 0,
            "benchmark": "Y%",
            "analise": "Comentário sobre esta conversão"
        }}
    ],
    "etapas_criticas": [
        {{
            "etapa": "Nome",
            "problema": "Descrição",
            "impacto": "Impacto no pipeline",
            "sugestao": "O que fazer"
        }}
    ],
    "plano_melhoria": ["Ação 1", "Ação 2"]
}}""",
        "response_sections": ["conversao_geral", "conversao_por_etapa", "etapas_criticas", "plano_melhoria"],
        "follow_up_prompts": [
            "Como melhorar a taxa de conversão?",
            "Quais etapas são mais críticas?",
            "Compare com benchmarks do setor"
        ]
    },
    
    KanbanCommandType.TEMPO_MEDIO.value: {
        "description": "Tempo médio para fechar vaga, por etapa",
        "keywords": ["tempo", "dias", "duração", "quanto tempo", "demora", "prazo", "SLA",
                     "deadline", "fechar vaga", "vagas com deadline", "atrasadas no sla"],
        "prompt_template": """## Tarefa: Análise de Tempo Médio

Analise o tempo médio em cada etapa do processo seletivo.

### Contexto da Vaga
{job_context}

### Dados Temporais do Pipeline
{pipeline_context}

### Candidatos e Tempos
{candidates_context}

### Instrução
Calcule e analise o tempo médio em cada etapa e o time-to-hire.

### Formato de Resposta Obrigatório (JSON):
{{
    "time_to_hire": {{
        "atual": "X dias",
        "estimado": "Y dias",
        "benchmark": "Z dias",
        "status": "dentro do prazo|atrasado|adiantado"
    }},
    "tempo_por_etapa": [
        {{
            "etapa": "Nome",
            "tempo_medio": "X dias",
            "benchmark": "Y dias",
            "status": "ok|atenção|crítico",
            "candidatos_acima_media": 0
        }}
    ],
    "etapas_lentas": [
        {{
            "etapa": "Nome",
            "tempo_excedente": "X dias acima do ideal",
            "causa_provavel": "Explicação",
            "impacto": "Impacto no processo"
        }}
    ],
    "otimizacoes": [
        {{
            "acao": "O que fazer",
            "economia_estimada": "X dias",
            "prioridade": "alta|média|baixa"
        }}
    ]
}}""",
        "response_sections": ["time_to_hire", "tempo_por_etapa", "etapas_lentas", "otimizacoes"],
        "follow_up_prompts": [
            "Como acelerar o processo?",
            "Quais etapas estão mais lentas?",
            "Candidatos que estão demorando muito"
        ]
    },
    
    KanbanCommandType.CANDIDATOS_PARADOS.value: {
        "description": "Candidatos inativos há muito tempo",
        "keywords": ["parado", "inativo", "esquecido", "sem movimento", "há muito tempo", "pendente"],
        "prompt_template": """## Tarefa: Identificação de Candidatos Parados

Identifique candidatos que estão sem movimentação há muito tempo.

### Contexto da Vaga
{job_context}

### Candidatos e Última Atividade
{candidates_context}

### Instrução
Liste candidatos parados e sugira ações para cada um.

### Formato de Resposta Obrigatório (JSON):
{{
    "resumo": {{
        "total_parados": 0,
        "criticos": 0,
        "atencao": 0,
        "risco_perda": "alto|médio|baixo"
    }},
    "candidatos_parados": [
        {{
            "id": "id",
            "nome": "nome",
            "etapa_atual": "etapa",
            "dias_parado": 0,
            "ultima_atividade": "Descrição",
            "severidade": "crítico|atenção|ok",
            "risco": "Risco de perder candidato",
            "acao_sugerida": "O que fazer"
        }}
    ],
    "acoes_em_lote": [
        {{
            "acao": "Descrição da ação",
            "candidatos_afetados": ["id1", "id2"],
            "prioridade": "alta|média|baixa"
        }}
    ],
    "plano_reativacao": "Estratégia para reativar candidatos parados"
}}""",
        "response_sections": ["resumo", "candidatos_parados", "acoes_em_lote", "plano_reativacao"],
        "follow_up_prompts": [
            "Quais candidatos priorizar?",
            "Como evitar que candidatos fiquem parados?",
            "Sugira mensagens de follow-up"
        ]
    },
    
    KanbanCommandType.TOP_CANDIDATOS.value: {
        "description": "Melhores candidatos baseado em score LIA",
        "keywords": ["top", "melhores", "destaque", "favoritos", "score alto", "recomendados"],
        "prompt_template": """## Tarefa: Top Candidatos

Identifique os melhores candidatos do pipeline baseado nos scores LIA.

### Contexto da Vaga
{job_context}

### Todos os Candidatos
{candidates_context}

### Instrução
Liste os top candidatos com análise detalhada de cada um.

### Formato de Resposta Obrigatório (JSON):
{{
    "top_candidatos": [
        {{
            "posicao": 1,
            "id": "id",
            "nome": "nome",
            "etapa_atual": "etapa",
            "score_lia": 95,
            "score_fit": 90,
            "principais_forcas": ["força 1", "força 2"],
            "diferencial": "O que destaca este candidato",
            "proxima_acao": "O que fazer com este candidato"
        }}
    ],
    "analise_pool": {{
        "qualidade_geral": "excelente|boa|regular|fraca",
        "score_medio": 75,
        "candidatos_acima_media": 0,
        "observacao": "Comentário geral"
    }},
    "recomendacoes": [
        {{
            "candidato_id": "id",
            "acao": "Ação específica",
            "urgencia": "alta|média|baixa"
        }}
    ]
}}""",
        "response_sections": ["top_candidatos", "analise_pool", "recomendacoes"],
        "follow_up_prompts": [
            "Compare os top 3 candidatos",
            "O que perguntar na entrevista do top 1?",
            "Quais candidatos estão prontos para próxima etapa?"
        ]
    },
    
    KanbanCommandType.MOVER_CANDIDATO.value: {
        "description": "Mover candidato para outra etapa do pipeline",
        "keywords": ["mover", "mover candidato", "mudar status", "mudar etapa", "avançar", "avançar candidato", "transição", "próxima etapa", "promover", "reprovar", "rejeitar", "mudar de etapa", "transferir", "passar para", "enviar para"],
        "prompt_template": """## Tarefa: Mover Candidato de Etapa

O usuário deseja mover um ou mais candidatos para outra etapa do pipeline de recrutamento. Analise o contexto e ajude a identificar qual candidato mover e para qual etapa.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### Instrução
Entenda a intenção do usuário e responda de forma conversacional. Se o usuário não especificou qual candidato ou para qual etapa, sugira candidatos e etapas com base no contexto. Analise os scores e a situação atual de cada candidato para fazer recomendações inteligentes.

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "mover_candidato",
    "resposta": "Resposta conversacional reconhecendo o pedido de movimentação e orientando o recrutador sobre como proceder",
    "candidatos_sugeridos": [
        {{
            "id": "id",
            "nome": "nome do candidato",
            "etapa_atual": "etapa atual do candidato",
            "etapas_possiveis": ["próximas etapas possíveis"],
            "recomendacao": "recomendação baseada no perfil e score"
        }}
    ],
    "etapas_disponiveis": ["lista de etapas disponíveis no pipeline"],
    "instrucoes": "Instruções claras para o recrutador sobre como realizar a movimentação"
}}""",
        "response_sections": ["acao", "resposta", "candidatos_sugeridos", "etapas_disponiveis", "instrucoes"],
        "follow_up_prompts": [
            "Mover candidato para screening",
            "Aprovar os top 3 candidatos",
            "Rejeitar candidatos com score abaixo de 50"
        ]
    },
    
    KanbanCommandType.ENVIAR_EMAIL.value: {
        "description": "Enviar email ou mensagem para candidatos",
        "keywords": ["enviar email", "mandar email", "enviar mensagem", "mandar mensagem", "email para", "escrever email", "redigir email", "enviar comunicação", "notificar candidato", "contatar candidato", "enviar feedback", "dar retorno", "devolutiva"],
        "prompt_template": """## Tarefa: Enviar Email para Candidato(s)

O recrutador mencionou enviar email ou mensagem. Siga o FLUXO PROGRESSIVO OBRIGATÓRIO abaixo.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### FLUXO PROGRESSIVO OBRIGATÓRIO (CRÍTICO):
Você deve seguir estas etapas em ordem. NUNCA pule etapas.

**ETAPA 1 - Resposta direta + Orientação (SEMPRE começa aqui)**:
- Responda diretamente à pergunta do recrutador (ex: "Sim, posso ajudar a enviar emails!")
- Explique brevemente o que você pode fazer (tipos de email: convite, feedback, proposta, etc.)
- Pergunte qual candidato e que tipo de email o recrutador deseja
- NÃO liste candidatos automaticamente
- NÃO sugira assunto/conteúdo ainda
- Defina "action_confirmed": false

**ETAPA 2 - Coleta de informações (quando o recrutador responder com candidato/tipo)**:
- Se o recrutador informou o candidato E o tipo de email, confirme os dados
- Se falta informação, pergunte o que falta
- Pergunte: "Posso abrir o formulário de email para [candidato]? Ou prefere que eu descreva o conteúdo aqui no chat?"
- Defina "action_confirmed": false

**ETAPA 3 - Execução (SOMENTE quando o recrutador confirmar explicitamente)**:
- O recrutador confirmou com "sim", "pode", "abra", "confirmo", etc.
- AGORA sim, preencha candidatos_alvo, sugestao_assunto e sugestao_conteudo
- Defina "action_confirmed": true

### Como determinar a etapa atual:
- Se a mensagem é uma PERGUNTA sobre capacidade ("você pode enviar email?", "consegue mandar mensagem?") → ETAPA 1
- Se a mensagem MENCIONA um candidato específico E tipo de email → ETAPA 2
- Se a mensagem é uma CONFIRMAÇÃO ("sim", "pode", "abra", "confirmo", "vamos", "ok") → ETAPA 3
- Na dúvida, use ETAPA 1

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "enviar_email",
    "resposta": "Resposta conversacional seguindo a etapa apropriada do fluxo progressivo",
    "action_confirmed": false,
    "candidatos_alvo": [],
    "sugestao_assunto": "",
    "sugestao_conteudo": ""
}}

IMPORTANTE: "candidatos_alvo", "sugestao_assunto" e "sugestao_conteudo" só devem ser preenchidos na ETAPA 3 (após confirmação). Nas etapas 1 e 2, deixe-os vazios.""",
        "response_sections": ["acao", "resposta", "action_confirmed", "candidatos_alvo", "sugestao_assunto", "sugestao_conteudo"],
        "follow_up_prompts": [
            "Enviar email para todos os candidatos em triagem",
            "Enviar feedback de reprovação",
            "Notificar candidatos sobre próxima etapa"
        ]
    },

    KanbanCommandType.DISPARAR_TRIAGEM.value: {
        "description": "Disparar triagem ou screening de candidatos",
        "keywords": ["triagem", "disparar triagem", "iniciar triagem", "screening", "avaliar cv", "avaliar currículo", "triar", "triagem curricular", "iniciar avaliação", "avaliar candidato", "fazer triagem", "wsi triagem", "triagem wsi"],
        "prompt_template": """## Tarefa: Disparar Triagem de Candidatos

O usuário deseja iniciar um processo de triagem para candidatos. Identifique quais candidatos devem ser triados.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### Instrução
Identifique os candidatos elegíveis para triagem, considerando sua etapa atual e scores. Recomende o tipo de triagem mais adequado.

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "disparar_triagem",
    "resposta": "Resposta conversacional orientando o recrutador sobre a triagem",
    "candidatos_alvo": [
        {{
            "id": "id",
            "nome": "nome do candidato",
            "etapa_atual": "etapa atual",
            "score": 0
        }}
    ],
    "tipo_triagem": "wsi_text|curricular",
    "recomendacao": "Recomendação sobre a triagem"
}}""",
        "response_sections": ["acao", "resposta", "candidatos_alvo", "tipo_triagem", "recomendacao"],
        "follow_up_prompts": [
            "Triar todos os candidatos em sourcing",
            "Avaliar os top 5 candidatos",
            "Iniciar triagem WSI para shortlist"
        ]
    },

    KanbanCommandType.AGENDAR_ENTREVISTA.value: {
        "description": "Agendar entrevista com candidatos",
        "keywords": ["agendar entrevista", "marcar entrevista", "schedule interview", "agendar reunião", "marcar reunião", "entrevista com", "agenda", "horário", "disponibilidade", "calendário", "agendar call", "marcar call"],
        "prompt_template": """## Tarefa: Agendar Entrevista com Candidato(s)

O usuário deseja agendar uma entrevista com um ou mais candidatos. Identifique os candidatos e o tipo de entrevista.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### Instrução
Identifique os candidatos para agendamento de entrevista, o tipo de entrevista adequado e sugira janelas de horário.

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "agendar_entrevista",
    "resposta": "Resposta conversacional orientando o recrutador sobre o agendamento",
    "candidatos_alvo": [
        {{
            "id": "id",
            "nome": "nome do candidato",
            "etapa_atual": "etapa atual"
        }}
    ],
    "tipo_entrevista": "rh|tecnica|gestor|final",
    "sugestao_horario": "Sugestão de janela de horário"
}}""",
        "response_sections": ["acao", "resposta", "candidatos_alvo", "tipo_entrevista", "sugestao_horario"],
        "follow_up_prompts": [
            "Agendar entrevista técnica com os aprovados",
            "Marcar entrevista com gestor para finalistas",
            "Ver disponibilidade da semana"
        ]
    },

    KanbanCommandType.SOLICITAR_DADOS.value: {
        "description": "Solicitar dados ou documentos de candidatos",
        "keywords": ["solicitar dados", "pedir dados", "pedir documentos", "solicitar documentos", "pedir informação", "dados adicionais", "informações adicionais", "completar cadastro", "formulário", "solicitar preenchimento"],
        "prompt_template": """## Tarefa: Solicitar Dados de Candidato(s)

O usuário deseja solicitar dados ou documentos adicionais de candidatos. Identifique quais dados são necessários.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### Instrução
Identifique quais candidatos precisam fornecer dados adicionais e quais dados são necessários, considerando a etapa atual do processo.

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "solicitar_dados",
    "resposta": "Resposta conversacional orientando o recrutador sobre a solicitação de dados",
    "candidatos_alvo": [
        {{
            "id": "id",
            "nome": "nome do candidato"
        }}
    ],
    "dados_solicitados": ["lista de campos de dados necessários"],
    "urgencia": "alta|media|baixa"
}}""",
        "response_sections": ["acao", "resposta", "candidatos_alvo", "dados_solicitados", "urgencia"],
        "follow_up_prompts": [
            "Solicitar documentos dos finalistas",
            "Pedir dados complementares",
            "Enviar formulário de dados pessoais"
        ]
    },

    KanbanCommandType.ANALISAR_PERFIL.value: {
        "description": "Análise detalhada de perfil de candidato",
        "keywords": ["analisar perfil", "análise de perfil", "avaliar perfil", "análise detalhada", "analisar candidato", "avaliar candidato em detalhe", "análise completa", "perfil completo", "análise lia", "análise ia", "gerar análise"],
        "prompt_template": """## Tarefa: Análise Detalhada de Perfil

O usuário deseja uma análise aprofundada do perfil de um candidato. Realize uma análise completa considerando múltiplas dimensões.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### Instrução
Faça uma análise detalhada do perfil do candidato, incluindo fit técnico, comportamental e cultural. Identifique áreas de foco para a análise.

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "analisar_perfil",
    "resposta": "Resposta conversacional com a análise detalhada do perfil",
    "candidato_alvo": {{
        "id": "id",
        "nome": "nome do candidato",
        "etapa_atual": "etapa atual"
    }},
    "tipo_analise": "completa|tecnica|comportamental|cultural",
    "areas_foco": ["áreas de foco para análise"]
}}""",
        "response_sections": ["acao", "resposta", "candidato_alvo", "tipo_analise", "areas_foco"],
        "follow_up_prompts": [
            "Analisar fit cultural do candidato",
            "Fazer análise técnica detalhada",
            "Avaliar potencial de crescimento"
        ]
    },

    KanbanCommandType.APROVAR_CANDIDATO.value: {
        "description": "Aprovar candidato para próxima etapa",
        "keywords": ["aprovar", "aprovado", "aprovar candidato", "aprovação", "aprovado na triagem", "passou", "avançar aprovado"],
        "prompt_template": """## Tarefa: Aprovar Candidato(s)

O usuário deseja aprovar um ou mais candidatos para a próxima etapa do processo seletivo. Identifique os candidatos e a próxima etapa.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Solicitação do Usuário
{user_query}

### Instrução
Identifique quais candidatos devem ser aprovados, considerando seus scores e desempenho. Sugira a próxima etapa para cada um e justifique a aprovação.

### Formato de Resposta Obrigatório (JSON):
{{
    "acao": "aprovar_candidato",
    "resposta": "Resposta conversacional orientando o recrutador sobre a aprovação",
    "candidatos_alvo": [
        {{
            "id": "id",
            "nome": "nome do candidato",
            "etapa_atual": "etapa atual",
            "proxima_etapa": "próxima etapa sugerida"
        }}
    ],
    "justificativa": "Justificativa para a aprovação dos candidatos"
}}""",
        "response_sections": ["acao", "resposta", "candidatos_alvo", "justificativa"],
        "follow_up_prompts": [
            "Aprovar os top candidatos",
            "Quais candidatos estão prontos para aprovação?",
            "Aprovar todos em triagem com score acima de 80"
        ]
    },

    KanbanCommandType.ANALISE_GERAL.value: {
        "description": "Análise geral baseada na pergunta do usuário",
        "keywords": [],
        "prompt_template": """## Tarefa: Análise Personalizada

Responda à pergunta do usuário sobre o pipeline de recrutamento.

### Contexto da Vaga
{job_context}

### Candidatos no Pipeline
{candidates_context}

### Pergunta do Usuário
{user_query}

### Instrução
Responda de forma completa e acionável, usando os dados disponíveis.

### Formato de Resposta Obrigatório (JSON):
{{
    "resposta": "Resposta completa em markdown à pergunta do usuário",
    "dados_relevantes": {{
        "metricas": {{}},
        "candidatos_mencionados": []
    }},
    "insights_adicionais": ["Insight 1", "Insight 2"],
    "sugestoes": ["Sugestão 1", "Sugestão 2"]
}}""",
        "response_sections": ["resposta", "dados_relevantes", "insights_adicionais", "sugestoes"],
        "follow_up_prompts": [
            "Explique mais sobre isso",
            "Quais são os próximos passos?",
            "Há algo mais que devo saber?"
        ]
    }
}


def get_system_prompt() -> str:
    """Retorna o system prompt padrão da LIA."""
    return LIA_SYSTEM_PROMPT


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


def detect_command_type(command: str) -> tuple[str, float]:
    """
    Detecta o tipo de comando baseado em palavras-chave com detecção de negação.
    
    Args:
        command: Comando do usuário
        
    Returns:
        Tuple com (tipo_comando, confiança)
    """
    command_lower = command.lower()
    best_match = KanbanCommandType.ANALISE_GERAL.value
    best_score = 0.0
    best_weight = 0.0
    
    for cmd_type, template in COMMAND_TEMPLATES.items():
        keywords = template.get("keywords", [])
        if not keywords:
            continue
            
        matched_keywords = [
            kw for kw in keywords
            if kw in command_lower and not _is_negated(command_lower, kw)
        ]
        matches = len(matched_keywords)
        if matches > 0:
            weight = sum(len(kw) for kw in matched_keywords)
            score = matches + (weight / 100.0)
            if score > best_score or (score == best_score and weight > best_weight):
                best_score = score
                best_weight = weight
                best_match = cmd_type
    
    if best_score > 0:
        confidence = min(0.5 + best_score * 0.15, 0.95)
    else:
        confidence = 0.4
    return (best_match, confidence)


def resolve_ui_action(command_type: str, structured_data: dict, candidates: list) -> tuple:
    """
    Resolve the UI action and params based on command type and AI response.
    
    Returns:
        Tuple of (ui_action: str | None, ui_action_params: dict | None)
    """
    ACTION_MAP = {
        KanbanCommandType.MOVER_CANDIDATO.value: "move_candidate",
        KanbanCommandType.ENVIAR_EMAIL.value: "send_email",
        KanbanCommandType.DISPARAR_TRIAGEM.value: "start_screening",
        KanbanCommandType.AGENDAR_ENTREVISTA.value: "schedule_interview",
        KanbanCommandType.SOLICITAR_DADOS.value: "request_data",
        KanbanCommandType.ANALISAR_PERFIL.value: "analyze_profile",
        KanbanCommandType.APROVAR_CANDIDATO.value: "approve_candidate",
    }
    
    ui_action = ACTION_MAP.get(command_type)
    if not ui_action:
        return None, None
    
    if not structured_data.get("action_confirmed", True):
        return None, None
    
    target_candidates = structured_data.get("candidatos_alvo", []) or structured_data.get("candidatos_sugeridos", [])
    candidato_alvo = structured_data.get("candidato_alvo")
    if candidato_alvo and not target_candidates:
        target_candidates = [candidato_alvo]
    
    matched_ids = []
    for target in target_candidates:
        target_name = (target.get("nome") or "").lower().strip()
        target_id = target.get("id", "")
        
        for c in candidates:
            if str(c.get("id", "")) == str(target_id):
                matched_ids.append(str(c["id"]))
                break
        else:
            single_token_matches = []
            for c in candidates:
                candidate_name = (c.get("name") or c.get("nome") or "").lower().strip()
                if not target_name or not candidate_name or len(target_name) < 3:
                    continue
                target_parts = target_name.split()
                candidate_parts = candidate_name.split()
                if (
                    target_name == candidate_name
                    or (len(target_parts) >= 2 and all(tp in candidate_name for tp in target_parts))
                    or (len(candidate_parts) >= 2 and all(cp in target_name for cp in candidate_parts))
                ):
                    matched_ids.append(str(c.get("id", "")))
                    break
                if len(target_parts) == 1 and target_name in candidate_parts:
                    single_token_matches.append(str(c.get("id", "")))
            else:
                if len(single_token_matches) == 1:
                    matched_ids.append(single_token_matches[0])
    
    params = {
        "candidate_ids": matched_ids,
        "action_type": structured_data.get("acao", command_type),
    }
    
    if command_type == KanbanCommandType.MOVER_CANDIDATO.value:
        structured_data.get("etapas_disponiveis", [])
        sugeridos = structured_data.get("candidatos_sugeridos", [])
        if sugeridos and sugeridos[0].get("etapas_possiveis"):
            params["to_stage"] = sugeridos[0]["etapas_possiveis"][0] if sugeridos[0]["etapas_possiveis"] else None
            
    elif command_type == KanbanCommandType.ENVIAR_EMAIL.value:
        params["subject"] = structured_data.get("sugestao_assunto", "")
        params["content_suggestion"] = structured_data.get("sugestao_conteudo", "")
        
    elif command_type == KanbanCommandType.DISPARAR_TRIAGEM.value:
        params["screening_type"] = structured_data.get("tipo_triagem", "wsi_text")
        
    elif command_type == KanbanCommandType.AGENDAR_ENTREVISTA.value:
        params["interview_type"] = structured_data.get("tipo_entrevista", "rh")
        params["suggested_time"] = structured_data.get("sugestao_horario", "")
        
    elif command_type == KanbanCommandType.SOLICITAR_DADOS.value:
        params["requested_fields"] = structured_data.get("dados_solicitados", [])
        params["urgency"] = structured_data.get("urgencia", "media")
        
    elif command_type == KanbanCommandType.ANALISAR_PERFIL.value:
        params["analysis_type"] = structured_data.get("tipo_analise", "completa")
        params["focus_areas"] = structured_data.get("areas_foco", [])
        
    elif command_type == KanbanCommandType.APROVAR_CANDIDATO.value:
        sugeridos = structured_data.get("candidatos_alvo", [])
        if sugeridos and sugeridos[0].get("proxima_etapa"):
            params["to_stage"] = sugeridos[0]["proxima_etapa"]
    
    return ui_action, params


def get_kanban_prompt_template(command_type: str) -> dict:
    """
    Retorna o template de prompt para um tipo de comando.
    
    Args:
        command_type: Tipo de comando do KanbanCommandType
        
    Returns:
        Dict com template e metadados
    """
    return COMMAND_TEMPLATES.get(
        command_type, 
        COMMAND_TEMPLATES[KanbanCommandType.ANALISE_GERAL.value]
    )


def format_job_context(job_data: dict) -> str:
    """Formata o contexto da vaga para o prompt."""
    return f"""
**Vaga:** {job_data.get('title', 'Não informado')}
**Departamento:** {job_data.get('department', 'Não informado')}
**Nível:** {job_data.get('level', 'Não informado')}
**Localização:** {job_data.get('location', 'Não informado')}
**Modelo:** {job_data.get('work_model', 'Não informado')}
**Requisitos:** {', '.join(job_data.get('requirements', [])) or 'Não informado'}
**Skills:** {', '.join(job_data.get('skills', [])) or 'Não informado'}
**Status:** {job_data.get('status', 'Ativa')}
"""


def format_candidates_context(candidates: list[dict]) -> str:
    """Formata o contexto dos candidatos para o prompt."""
    if not candidates:
        return "Nenhum candidato no pipeline."
    
    lines = []
    for i, c in enumerate(candidates, 1):
        score_info = f"Score LIA: {c.get('score', 'N/A')}, Fit: {c.get('fitScore', 'N/A')}"
        lines.append(f"""
**{i}. {c.get('name', 'Nome não informado')}** (ID: {c.get('id', 'N/A')})
- Cargo: {c.get('role', 'N/A')} @ {c.get('currentCompany', 'N/A')}
- Etapa: {c.get('stage', 'N/A')}
- {score_info}
- Skills: {', '.join(c.get('skills', [])) if c.get('skills') else 'N/A'}
- Experiência: {c.get('experience', 'N/A')}
- Localização: {c.get('location', 'N/A')}
""")
    return "\n".join(lines)


def format_selected_candidates_context(candidates: list[dict], selected_ids: list[str]) -> str:
    """Formata apenas os candidatos selecionados."""
    selected = [c for c in candidates if str(c.get('id')) in [str(sid) for sid in selected_ids]]
    if not selected:
        return "Nenhum candidato selecionado."
    return format_candidates_context(selected)


def format_pipeline_context(job_data: dict, candidates: list[dict]) -> str:
    """Formata contexto do pipeline com métricas."""
    stages = {}
    for c in candidates:
        stage = c.get('stage', 'unknown')
        stages[stage] = stages.get(stage, 0) + 1
    
    avg_times = job_data.get('avgTimePerStage', {})
    
    lines = ["**Distribuição por Etapa:**"]
    for stage, count in stages.items():
        avg_time = avg_times.get(stage, 'N/A')
        lines.append(f"- {stage}: {count} candidatos (tempo médio: {avg_time} dias)")
    
    lines.append(f"\n**Total de candidatos:** {len(candidates)}")
    
    return "\n".join(lines)


def build_full_prompt(
    command_type: str,
    user_query: str,
    job_data: dict,
    candidates: list[dict],
    selected_ids: list[str] | None = None
) -> str:
    """
    Constrói o prompt completo para a chamada à IA.
    
    Args:
        command_type: Tipo de comando
        user_query: Pergunta original do usuário
        job_data: Dados da vaga
        candidates: Lista de candidatos
        selected_ids: IDs dos candidatos selecionados (opcional)
        
    Returns:
        Prompt completo formatado
    """
    template = get_kanban_prompt_template(command_type)
    prompt_template = template["prompt_template"]
    
    job_context = format_job_context(job_data)
    candidates_context = format_candidates_context(candidates)
    pipeline_context = format_pipeline_context(job_data, candidates)
    selected_context = format_selected_candidates_context(candidates, selected_ids or [])
    
    prompt = prompt_template.format(
        job_context=job_context,
        candidates_context=candidates_context,
        pipeline_context=pipeline_context,
        selected_candidates_context=selected_context,
        user_query=user_query
    )
    
    return prompt
