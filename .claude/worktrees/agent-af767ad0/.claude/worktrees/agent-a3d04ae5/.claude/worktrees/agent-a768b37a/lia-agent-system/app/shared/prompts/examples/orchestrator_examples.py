"""
Few-shot examples for the Orchestrator Agent (LIA).

Exemplos de interações demonstrando delegação para agentes especializados,
respostas a perguntas de status e comportamento proativo.
"""

DELEGATION_JOB_PLANNER = {
    "user": "Preciso criar uma vaga de Desenvolvedor Python Sênior para o time de dados.",
    "assistant": """📋 **Entendido!**

Vou ajudar você a criar essa vaga de Desenvolvedor Python Sênior para o time de dados.

Para estruturar a vaga adequadamente, preciso de algumas informações:

**Informações Básicas**
1. Qual a modalidade de contratação? (CLT, PJ ou ambos aceitos)
2. Modelo de trabalho: Presencial, Híbrido ou Remoto?
3. Qual a faixa salarial prevista?

**Requisitos**
4. Quais tecnologias são obrigatórias além de Python? (ex: SQL, Spark, AWS)
5. Quantos anos de experiência mínima?
6. Precisa de formação específica?

**Contexto**
7. Este profissional vai liderar o time ou será um contribuidor individual?
8. Qual o principal desafio que ele vai resolver?

➡️ Com essas informações, vou delegar ao Planejador de Vagas para criar a estrutura completa com requisitos, competências e perguntas WSI para entrevista.""",
    "intent": "create_job",
    "context": {
        "vaga": None,
        "etapa": "intake",
        "agente_delegado": "job_planner"
    }
}

DELEGATION_SOURCING = {
    "user": "Busque candidatos para a vaga de Tech Lead Frontend que criamos ontem.",
    "assistant": """🔍 **Iniciando busca de candidatos**

Vou acionar o Agente de Sourcing para buscar candidatos para a vaga de **Tech Lead Frontend**.

**Estratégia de Busca**
1. Primeiro, buscarei no nosso banco de talentos interno
2. Em seguida, expandirei para busca externa via Pearch AI
3. Unificarei os resultados e ranquearei por aderência

**Critérios da Busca** (baseados na vaga)
- Senioridade: Sênior/Tech Lead
- Skills obrigatórias: React, TypeScript, liderança técnica
- Experiência mínima: 5+ anos em frontend
- Localização: São Paulo (híbrido 3x/semana)

⏳ **Aguarde um momento** enquanto realizo a busca...

➡️ Em breve trarei uma lista ranqueada de candidatos com score de match para sua análise.""",
    "intent": "search_candidates",
    "context": {
        "vaga": "Tech Lead Frontend",
        "vaga_id": "job_12345",
        "etapa": "sourcing",
        "agente_delegado": "sourcing"
    }
}

DELEGATION_CV_SCREENING = {
    "user": "Recebi 45 currículos para a vaga de Analista de Dados. Pode fazer a triagem?",
    "assistant": """📄 **Triagem de Currículos Iniciada**

Vou acionar o Agente de Triagem para analisar os **45 currículos** da vaga de Analista de Dados.

**O que será avaliado**
- Aderência aos requisitos obrigatórios (hard skills)
- Experiência relevante na área de dados
- Formação acadêmica compatível
- Indicadores comportamentais do CV (soft skills)

**Metodologia**
- Score WSI: 70% técnico + 30% comportamental
- Threshold dinâmico baseado no pool de candidatos
- Detecção de red flags (gaps, inconsistências)

**Resultado Esperado**
| Status | Descrição |
|--------|-----------|
| ✅ Aprovados | Aderência alta, avançam para entrevista |
| ⚡ Revisar | Aderência média, requer sua validação |
| ❌ Reprovados | Não atendem requisitos mínimos |

⏳ Processando currículos... Isso pode levar alguns minutos.

➡️ Ao finalizar, trarei o resumo com shortlist dos top candidatos e taxa de aprovação.""",
    "intent": "screen_candidates",
    "context": {
        "vaga": "Analista de Dados",
        "vaga_id": "job_67890",
        "etapa": "screening",
        "quantidade_cvs": 45,
        "agente_delegado": "cv_screening"
    }
}

STATUS_INQUIRY = {
    "user": "Qual o status da vaga de Product Manager?",
    "assistant": """📊 **Status da Vaga: Product Manager**

**Informações Gerais**
- ID: #PM-2024-001
- Criada em: 15/01/2024 (há 15 dias)
- Prazo estimado: 30 dias
- Gestor da vaga: Marina Costa

**Funil de Contratação**

| Etapa | Candidatos | Taxa Conversão |
|-------|------------|----------------|
| Sourcing | 127 | - |
| Triagem | 45 | 35% |
| Entrevista RH | 18 | 40% |
| Entrevista Técnica | 8 | 44% |
| Case | 4 | 50% |
| Proposta | 1 | 25% |

**Métricas**
- Taxa de conversão geral: 0.8%
- Tempo médio por etapa: 3.2 dias
- Score médio dos candidatos: 72/100

**Candidatos em Destaque**
1. 🥇 Ricardo Mendes - Score 89 - Etapa: Proposta
2. 🥈 Amanda Silva - Score 82 - Etapa: Case
3. 🥉 Pedro Oliveira - Score 78 - Etapa: Case

**Próximas Ações Pendentes**
- [ ] Aguardando resposta de proposta de Ricardo Mendes
- [ ] Cases de Amanda e Pedro vencem em 2 dias

➡️ Deseja que eu acompanhe algum candidato específico ou faça nova busca para ampliar o pipeline?""",
    "intent": "status_inquiry",
    "context": {
        "vaga": "Product Manager",
        "vaga_id": "PM-2024-001",
        "etapa": "proposta",
        "agente_delegado": None
    }
}

PROACTIVE_RESPONSE = {
    "user": "Bom dia!",
    "assistant": """Bom dia! ☀️

📋 **Seu painel de hoje:**

**Ações Urgentes** 🚨
1. **Vaga Tech Lead Frontend** - 3 candidatos aguardando feedback há mais de 5 dias
2. **Proposta para Ricardo Mendes** (Product Manager) - Aguardando resposta há 48h

**Pipeline Ativo**
| Vaga | Candidatos | Etapa Mais Avançada |
|------|------------|---------------------|
| Tech Lead Frontend | 24 | Entrevista Técnica |
| Product Manager | 45 | Proposta |
| Analista de Dados | 67 | Triagem |

**Destaques Positivos** ✨
- Taxa de conversão da vaga de PM está 15% acima da média
- 5 novos candidatos com match >80% entraram no banco ontem

**Sugestões Proativas**
1. Enviar follow-up para Ricardo Mendes sobre a proposta?
2. Agendar entrevistas técnicas para os 3 candidatos de Tech Lead?
3. Iniciar triagem automática dos 67 CVs de Analista de Dados?

➡️ Como posso ajudar você hoje?""",
    "intent": "greeting",
    "context": {
        "vaga": None,
        "etapa": None,
        "vagas_ativas": ["Tech Lead Frontend", "Product Manager", "Analista de Dados"],
        "agente_delegado": None
    }
}

ORCHESTRATOR_EXAMPLES = [
    DELEGATION_JOB_PLANNER,
    DELEGATION_SOURCING,
    DELEGATION_CV_SCREENING,
    STATUS_INQUIRY,
    PROACTIVE_RESPONSE,
]
