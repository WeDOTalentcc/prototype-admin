# Sistema de Scoring de Candidatos — WeDO Talent ATS

## Visão Geral

O sistema de scoring avalia candidatos contra requisitos de vagas em duas camadas:

1. **Scoring do Agente (Python):** Triagem inicial via LLM — classifica, pontua e justifica cada candidato encontrado nas buscas (local, Pearch, LinkedIn).
2. **Scoring do ProfileAnalyzer (Rails):** Avaliação detalhada por rubrica — analisa o currículo completo contra os requisitos da vaga usando o Gemini, gerando score auditável com evidências.

Ambas as camadas produzem evidências rastreáveis que são armazenadas e expostas ao recrutador.

---

## Arquitetura do Pipeline de Scoring

```
┌──────────────────────────────────────────────────────────────┐
│ 1. AGENTE PYTHON (LangGraph)                                │
│    Busca candidatos em múltiplas fontes                      │
│    Aplica scoring inicial (0-100) com justificativa          │
│    Entrega via API: deliver_cycle                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. DeliverCandidatesService (Rails)                          │
│    Cria/atualiza SourcedProfile + SourcedProfileSourcing     │
│    Armazena ai_metadata com evidências do agente             │
│    Score inicial: search_score                               │
└────────────────────────┬─────────────────────────────────────┘
                         │ after_commit callback
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. AiAnalysisJob (Sidekiq, queue: ai_analysis)               │
│    Chama ProfileAnalyzer com currículo + query da vaga       │
│    Atualiza SourcedProfileSourcing com:                      │
│      score: rubric-based (0-99)                              │
│      analysis: insights completos                            │
│      ai_metadata: metadados do modelo                        │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. AiEnrichmentService                                       │
│    Enriquece SourcedProfile com:                             │
│      - Skills extraídas da análise                           │
│      - Highlights, development_areas, suggested_questions    │
│      - SkillRelationship records                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Camada 1: Scoring do Agente Python (Triagem Inicial)

### Contexto de Entrada

O `BuildSearchContextService` monta o contexto enviado ao agente via RabbitMQ:

| Campo | Descrição |
|---|---|
| `agent.criteria_text` | Critérios primários, secundários e de diferenciação da vaga |
| `agent.criteria_structured` | Requisitos estruturados com prioridade e peso |
| `agent.min_score_threshold` | Score mínimo para incluir candidato (default: 70) |
| `agent.extracted_preferences` | Preferências aprendidas via feedback do recrutador |
| `job` | Título, skills, senioridade, localização |
| `feedback_history` | Últimos 50 feedbacks (aprovações/rejeições com razões) |
| `feedback_summary` | Padrões: skills preferidas, empresas, títulos, razões de rejeição |
| `presented_profile_ids` | IDs já apresentados (evitar repetição) |
| `candidates_already_in_job` | Candidatos já no processo seletivo |

### Fontes de Busca

| Fonte | Tipo | Descrição |
|---|---|---|
| **Local** | Busca interna | Elasticsearch no banco de candidatos do tenant |
| **Pearch** | Busca global externa | API Pearch — base global de profissionais |
| **LinkedIn** | Busca global externa | API Apify → LinkedIn — busca e scraping de perfis |

### Estratégias de Busca por Iteração

O agente executa até `max_search_iterations` (default: 3) iterações, cada uma com múltiplas estratégias:

| Estratégia | Descrição |
|---|---|
| `text_only` | Busca por texto livre (query na busca fulltext) |
| `skills_only` | Filtro por skills específicas no `where` |
| `broad_title` | Query com título amplo da vaga |
| `has_curriculum` | Filtro para candidatos com currículo disponível |
| `boost_skills` | Boost de relevância por skills no `boost_where` |

### Ciclo de Avaliação de Qualidade

Após cada iteração de busca:

1. **Deduplicação:** Remove candidatos já encontrados ou já apresentados
2. **Avaliação Heurística:** Calcula composite score baseado em:
   - `quantity` (0-1): Proporção de candidatos encontrados vs target
   - `relevance` (0-1): Relevância textual dos resultados
   - `diversity` (0-1): Diversidade de fontes/queries
   - `composite` = ponderação dos três fatores
3. **Avaliação LLM:** O modelo avalia cobertura dos requisitos e decide:
   - `SUFFICIENT`: Qualidade adequada → prosseguir para ranking
   - `NEEDS_IMPROVEMENT`: Precisa reformular queries → nova iteração
4. **Diagnóstico:** Identifica causa da baixa qualidade:
   - `skills_filter_too_restrictive`
   - `query_too_generic`
   - `missing_coverage_area`
5. **Reformulação:** Gera novas queries corrigindo os gaps identificados

### Dados Entregues por Candidato

O agente entrega cada candidato com:

```json
{
  "candidate_id": "123",
  "name": "João Silva",
  "score": 82,
  "category": "strong_match",
  "justification": "7 anos Ruby on Rails, PostgreSQL avançado, experiência em plataformas de pagamento",
  "strengths": [
    "Ruby on Rails sênior com 7 anos",
    "PostgreSQL com otimização de queries",
    "Experiência em sistemas de pagamento (PagSeguro)"
  ],
  "concerns": [
    "Sem experiência com Kafka mencionada"
  ],
  "requirement_coverage": {
    "essential": 0.85,
    "important": 0.70,
    "nice_to_have": 0.40
  },
  "source_query": "Ruby on Rails Senior",
  "source_provider": "local",
  "found_in_iteration": 1
}
```

### Armazenamento do Score Inicial

O `DeliverCandidatesService` persiste esses dados em `SourcedProfileSourcing`:

| Campo | Valor | Descrição |
|---|---|---|
| `search_source` | `"background_agent"` | Origem da busca |
| `search_score` | Score do agente (0-100) | Score inicial da triagem |
| `score` | Score do agente (0-100) | Score principal (será sobrescrito pelo ProfileAnalyzer) |
| `ai_metadata` | JSON completo | Evidências do agente (category, justification, strengths, concerns, requirement_coverage) |

---

## Camada 2: ProfileAnalyzer (Avaliação Detalhada por Rubrica)

### Entrada

| Campo | Fonte | Descrição |
|---|---|---|
| `profile.curriculum_text` | SourcedProfile ou Candidate | Texto do currículo (max 15.000 chars) |
| `sourcing.query` | Sourcing | Query original da busca / descrição da vaga |
| `requirements` | Sourcing (opcional) | Requisitos estruturados com prioridade e peso |

### Avaliação de Qualidade do Perfil (Pré-análise)

Antes de chamar o LLM, o ProfileAnalyzer avalia a completude do currículo:

```
Seções verificadas:
  ✓ Contato (email, telefone, linkedin)
  ✓ Experiência (empresas, cargos)
  ✓ Formação (universidade, cursos)
  ✓ Skills (tecnologias, competências)
  ✓ Datas (pelo menos 2 referências temporais)

Completeness = seções presentes / total de seções (0.0 - 1.0)
Word Count = número de palavras no currículo
Is Minimal = word_count < 100

Confidence:
  - "high": completeness >= 0.8 AND !is_minimal
  - "medium": completeness >= 0.5
  - "low": completeness < 0.5 ou currículo muito curto
```

Essa qualidade é enviada ao LLM para ajustar o `score_confidence`.

### Metodologia de Rubrica

O ProfileAnalyzer usa uma rubrica de 4 níveis de match:

| Match Level | Pontos | Significado |
|---|---|---|
| `exceeds` | 95 | Supera claramente o requisito com múltiplas evidências fortes |
| `meets` | 75 | Atende completamente o requisito com evidência clara |
| `partial` | 40 | Atende parcialmente, evidência fraca ou incompleta |
| `missing` | 0 | Não encontrado ou não atende |

Cada requisito tem um nível de prioridade com multiplicador de peso:

| Prioridade | Multiplicador | Descrição |
|---|---|---|
| `essential` | 3x | Requisito essencial — elimina se ausente |
| `important` | 2x | Requisito importante — diferencia candidatos |
| `nice_to_have` | 1x | Diferencial — não elimina, mas agrega |

### Fórmula do Score Final

```
Score = Σ(peso_requisito × pontos_match_level) / Σ(peso_requisito × 95) × 100

Onde:
  - Cada requisito contribui: PRIORITY_MULTIPLIER × MATCH_POINTS
  - Denominador: soma dos pesos × 95 (máximo possível por item)
  - Score é capped em 99 (perfeição absoluta não existe)

Exemplo com 3 requisitos:
  Ruby on Rails (essential, meets):     3 × 75 = 225
  PostgreSQL (important, exceeds):      2 × 95 = 190  
  Kafka (nice_to_have, missing):        1 × 0  = 0
  
  Máximo possível: (3 × 95) + (2 × 95) + (1 × 95) = 570
  Score = (415 / 570) × 100 = 72.8 → 73
```

O score é **calculado deterministicamente** pelo Rails a partir dos match_levels retornados pelo LLM — não confia no score que o LLM sugere diretamente (auditabilidade).

### Diretrizes Anti-Viés

O prompt do ProfileAnalyzer impõe regras estritas:

| Proibido como proxy de qualidade | Tratamento correto |
|---|---|
| Nome/prestígio de empresas | Avaliar skills demonstradas, não onde trabalhou |
| Ranking de universidades | Avaliar conhecimento aplicado, não diploma |
| Gaps de emprego | Observação neutra (saúde, família, estudo, empreendedorismo) |
| Tempo curto em empresas | Observação neutra (contratos, projetos, layoffs) |
| Qualidade de escrita do CV | Focar em conteúdo técnico |
| Localização/idioma nativo | Irrelevante para competência técnica |
| Idade inferida por datas | Proibido considerar |

Itens como gaps, job-hopping e career changes são classificados como `neutral_observations`, nunca como `red_flags`.

### Red Flags vs Neutral Observations

**Red Flags** (penalizam): Apenas inconsistências factuais
- `inconsistent_dates`: Datas contraditórias no currículo
- `misrepresentation`: Informação claramente falsa
- `skill_mismatch`: Skill declarada mas evidência contrária

**Neutral Observations** (informativos, sem penalidade):
- `gap_in_employment`: Período sem trabalho
- `short_tenure`: Tempo curto em empresa
- `job_hopping`: Mudanças frequentes
- `career_downgrade`: Mudança para cargo/área menor
- `career_change`: Mudança de área
- `overqualified`: Qualificação acima do requisito
- `underqualified`: Qualificação abaixo do requisito

### Estrutura Completa da Resposta

```json
{
  "evaluation": [
    {
      "requirement": "Ruby on Rails Sênior",
      "priority": "essential",
      "evidence": [
        "7 anos de experiência em Ruby on Rails na PagSeguro",
        "Desenvolveu APIs RESTful para processamento de pagamentos"
      ],
      "match_level": "exceeds",
      "points": 95,
      "confidence": "high",
      "rationale": "Experiência extensa e relevante em Rails com foco em pagamentos"
    },
    {
      "requirement": "Kafka ou mensageria assíncrona",
      "priority": "important",
      "evidence": [],
      "match_level": "missing",
      "points": 0,
      "confidence": "high",
      "rationale": "Nenhuma menção a Kafka, RabbitMQ ou sistemas de mensageria"
    }
  ],
  "calculated_score": 73,
  "score_confidence": "high",
  "confidence_factors": {
    "profile_completeness": 0.8,
    "evidence_density": 0.75,
    "ambiguity_level": 0.15
  },
  "one_liner": "Sênior Rails forte em pagamentos, mas sem experiência em mensageria",
  "red_flags": [],
  "neutral_observations": [
    {
      "type": "short_tenure",
      "description": "2 passagens de menos de 1 ano (2019-2020), possivelmente contratos"
    }
  ],
  "development_areas": [
    {
      "type": "skill_gap",
      "description": "Sem experiência com Kafka ou sistemas de mensageria assíncrona",
      "requirement": "Kafka ou mensageria assíncrona"
    },
    {
      "type": "depth_gap",
      "description": "Caching multicamada não mencionado no currículo",
      "requirement": "Caching multicamada"
    }
  ],
  "highlights": [
    {
      "type": "industry_match",
      "description": "4 anos em plataforma de pagamentos (PagSeguro) — match direto com o requisito"
    },
    {
      "type": "technical_depth",
      "description": "Otimização de queries PostgreSQL com resultados mensuráveis (40% redução latência)"
    }
  ],
  "skills_assessment": {
    "strong": ["Ruby on Rails", "PostgreSQL", "REST API", "TDD", "RSpec"],
    "mentioned": ["Docker", "CI/CD", "Redis"],
    "missing_from_search": ["Kafka", "RabbitMQ", "Caching multicamada"]
  },
  "suggested_questions": [
    "Qual sua experiência com processamento assíncrono e filas de mensagens?",
    "Como você implementou caching em camadas nos seus projetos?",
    "Descreva um cenário de otimização de query PostgreSQL que resolveu"
  ]
}
```

### Caching

Resultados são cacheados por 7 dias com chave: `SHA256(query + curriculum_text)`. Se o mesmo candidato for analisado para a mesma vaga, o cache é usado sem chamar o LLM.

---

## Mecanismo de Evidências

### Três Níveis de Evidência

#### Nível 1: Evidências do Agente (ai_metadata)

Armazenadas em `SourcedProfileSourcing.ai_metadata`:

```json
{
  "category": "strong_match",
  "justification": "Resumo conciso de por que foi selecionado",
  "strengths": ["Ponto forte 1", "Ponto forte 2"],
  "concerns": ["Preocupação 1"],
  "requirement_coverage": {
    "essential": 0.85,
    "important": 0.70,
    "nice_to_have": 0.40
  },
  "source_query": "Query que encontrou o candidato",
  "source_provider": "local|pearch|linkedin",
  "found_in_iteration": 1
}
```

**Quando disponível:** Imediatamente após entrega pelo agente.
**Para que serve:** Dar contexto rápido ao recrutador sobre por que o candidato apareceu.

#### Nível 2: Análise Detalhada (analysis)

Armazenada em `SourcedProfileSourcing.analysis`:

```json
{
  "score": 73,
  "one_liner": "Resumo do fit em até 100 caracteres",
  "evaluation": [
    {
      "requirement": "Nome do requisito",
      "priority": "essential|important|nice_to_have",
      "match_level": "exceeds|meets|partial|missing",
      "points": 95,
      "confidence": "high|medium|low",
      "rationale": "Justificativa breve",
      "evidence": ["Citação 1 do CV", "Citação 2 do CV"]
    }
  ],
  "red_flags": [...],
  "neutral_observations": [...],
  "development_areas": [...],
  "highlights": [...],
  "skills_assessment": {
    "strong": [...],
    "mentioned": [...],
    "missing_from_search": [...]
  },
  "suggested_questions": [...]
}
```

**Quando disponível:** Após processamento pelo AiAnalysisJob (assíncrono).
**Para que serve:** Avaliação completa requisito-a-requisito com evidências do currículo.

#### Nível 3: Enriquecimento do Perfil (profile_data)

Armazenado em `SourcedProfile.profile_data`:

```json
{
  "highlights": [
    {"type": "career_progression", "description": "..."}
  ],
  "development_areas": [
    {"type": "skill_gap", "description": "...", "requirement": "..."}
  ],
  "suggested_questions": ["Pergunta 1", "Pergunta 2"],
  "evaluation": [
    {"requirement": "...", "match_level": "...", "priority": "...", "points": 95, "rationale": "..."}
  ],
  "enrichment": {
    "enriched_at": "2026-04-05T10:30:00Z",
    "enrichment_source": "ai_analysis",
    "sourcing_id": 123,
    "ai_score": 73,
    "ai_confidence": "high",
    "skills_extracted": 8,
    "highlights_added": 2
  }
}
```

**Quando disponível:** Logo após a análise (mesma pipeline).
**Para que serve:** Dados persistidos no perfil do candidato, disponíveis em qualquer contexto futuro.

---

## Diferenças entre Busca Local e Global

### Busca Local (Elasticsearch)

| Aspecto | Detalhe |
|---|---|
| **Fonte** | Base de candidatos do tenant (Elasticsearch) |
| **Dados disponíveis** | Currículo completo, skills, histórico de processos |
| **Qualidade do scoring** | Alta — currículo rico permite análise detalhada |
| **Perfil criado** | `SourcedProfile` vinculado ao `Candidate` existente |
| **Evidências** | Citações diretas do currículo armazenado |
| **Tempo de análise** | Rápido — currículo já disponível localmente |

### Busca Global (Pearch / LinkedIn)

| Aspecto | Pearch | LinkedIn |
|---|---|---|
| **Fonte** | API Pearch (base global) | API Apify → LinkedIn |
| **Dados disponíveis** | Perfil profissional, skills, experiências | Perfil LinkedIn completo |
| **Qualidade do scoring** | Média-alta — depende da completude do perfil | Média — perfis podem ser limitados |
| **Perfil criado** | `SourcedProfile` com `provider: "pearch"` | `SourcedProfile` com `provider: "linkedin"` |
| **Evidências** | Baseadas no resumo/experiências do Pearch | Baseadas nos dados do LinkedIn |
| **curriculum_text** | Construído a partir de title, summary, experiences, skills, certifications, languages | Construído a partir dos dados do LinkedIn |
| **Desafios** | Puede faltar detalhes de projetos | Perfis podem ser privados ou incompletos |

### Construção do curriculum_text para perfis externos

O `DeliverCandidatesService` constrói o `curriculum_text` para perfis que não possuem currículo nativo:

```
{título} | {localização}

{resumo/summary do perfil}

Skills: skill1, skill2, skill3

{título do cargo} @ {empresa}
  {data_início} - {data_fim}

Certifications: {certificação}

Languages: Português - Professional, English - Professional
```

Esse texto construído é o que o ProfileAnalyzer recebe para análise. Perfis com `curriculum_text` vazio são pulados (`status: :skipped`).

---

## Ciclo de Calibração e Aprendizado

### Feedback Loop

```
Recrutador avalia candidatos entregues
          │
          ▼
  ProcessFeedbackService
          │
          ├── Registra AgentFeedback (approved/rejected + reason)
          ├── Atualiza contadores (total_approved, total_rejected)
          │
          ▼
  ≥ 5 feedbacks?  ──── Não ──→ calibration_state = "learning"
          │
          Sim
          │
          ▼
  calibration_state = "calibrated"
  Enqueue ExtractPreferencesJob
          │
          ▼
  Extrai preferências:
    preferred_skills (top 10)
    preferred_titles (top 5)
    preferred_companies (top 3)
    preferred_locations (top 3)
    experience_range { min, max }
    avoid_patterns (top 5 razões de rejeição)
          │
          ▼
  Próxima busca usa extracted_preferences
  para refinar queries e filtragem
```

### Impacto na Qualidade do Score

| Fase | Comportamento |
|---|---|
| `pending` | Score baseado apenas nos critérios da vaga |
| `learning` | Score começa a considerar padrões de feedback |
| `calibrated` | Score refinado com preferências extraídas do recrutador |

---

## Ranking e Ordenação Final

### Ranking Primário

Os candidatos são ordenados por `SourcedProfileSourcing.score` DESC.

### Reranking (Busca de Candidatos Similares)

Para buscas híbridas (vetor + texto), aplica-se RRF (Reciprocal Rank Fusion):

```
rrf_score = vector_weight × 1/(K + vector_rank) + text_weight × 1/(K + text_rank)

K = 60 (constante de suavização)
vector_weight = 0.6
text_weight = 0.4
```

### Boost de Completude (Reranker)

Após o RRF, aplica-se boost baseado na riqueza do perfil:

| Sinal | Condição | Boost |
|---|---|---|
| `rich_content` | Currículo > 2000 chars | +15% |
| `good_content` | Currículo > 1000 chars | +10% |
| `basic_content` | Currículo > 500 chars | +5% |
| `has_contact` | Tem email ou telefone | +5% |
| `is_recent` | Atualizado nos últimos 90 dias | +3% |
| `empty_candidate` | Currículo < 200 chars, sem contato | -20% |

```
Final Score = RRF Score × (1 + boost_total)
```

---

## Metadados de Rastreabilidade

### ai_metadata (após ProfileAnalyzer)

```json
{
  "ai_source": "gemini",
  "model": "gemini-2.0-flash",
  "sourcing_id": 123,
  "ran_at": "2026-04-05T10:30:00Z",
  "prompt_tokens": 3500,
  "completion_tokens": 1200,
  "total_tokens": 4700,
  "cost_usd": 0.00273,
  "profile_quality": {
    "completeness": 0.8,
    "missing": ["skills"],
    "word_count": 2543,
    "is_minimal": false,
    "confidence": "high"
  },
  "score_confidence": "high",
  "scoring_method": "rubric_based"
}
```

### Custos e Tracking

Cada chamada ao Gemini é registrada em `LlmUsage`:

| Campo | Descrição |
|---|---|
| `model` | Modelo utilizado (gemini-2.0-flash) |
| `operation` | `sourcing.profile_analysis` |
| `input_tokens` | Tokens do prompt |
| `output_tokens` | Tokens da resposta |
| `cost_usd` | Custo calculado |
| `latency_ms` | Tempo de resposta |
| `success` | Se a chamada foi bem-sucedida |

---

## Serialização para o Frontend

O `SourcedProfileSourcingSerializer` expõe ao frontend:

| Campo | Tipo | Descrição |
|---|---|---|
| `sourcing_score` | Float | Score principal (alias de `score`) |
| `search_score` | Float | Score da busca (Elasticsearch/agente) |
| `similarity_score` | Float | Similaridade vetorial |
| `search_source` | String | Origem: `background_agent`, `pearch`, `linkedin` |
| `ai_analysis` | JSON | Análise completa (alias de `analysis`) |
| `ai_metadata` | JSON | Metadados com evidências |
| `ai_analyzed_at` | DateTime | Data da análise (de `ai_metadata.ran_at`) |

---

## Resumo: O que torna um score "bom"

| Fator | Peso | Como melhorar |
|---|---|---|
| **Cobertura de requisitos essenciais** | 3x | Garantir que critérios essenciais estejam bem definidos na vaga |
| **Evidências específicas no currículo** | Alto | Candidatos com currículos detalhados recebem scores mais precisos |
| **Match level dos requisitos** | Base do cálculo | Rubrica objetiva — exceeds/meets/partial/missing |
| **Completude do perfil** | Afeta confidence | Perfis com mais seções preenchidas geram scores de maior confiança |
| **Calibração do agente** | Incremental | Feedback do recrutador refina as buscas e filtragens subsequentes |
| **Anti-viés** | Proteção | Score não é inflado/deflado por prestígio de empresa/universidade |

---

# Guia de Integração: Sistema Python de Scoring

Este guia instrui um sistema Python a implementar o scoring de candidatos e entregar os resultados no formato exato esperado pela API Rails.

---

## Fluxo de Entrega e Comportamento Atual

Quando o Python entrega candidatos via `POST /v1/users/background_agents/:id/deliver_cycle`, o Rails executa esta cadeia:

```
Python chama deliver_cycle com candidates[]
    │
    ▼
DeliverCandidatesService
    │ Cria SourcedProfile
    │ Cria SourcedProfileSourcing via find_or_create_by!
    │ Salva score, search_score, ai_metadata (dados do Python)
    │
    ▼
after_commit :enqueue_ai_analysis (on: :create)
    │
    ▼
AiAnalysisJob (Sidekiq, queue: ai_analysis)
    │ Chama ProfileAnalyzer (Gemini LLM)
    │ SOBRESCREVE: score, analysis, ai_metadata
    │
    ▼
AiEnrichmentService
    │ Enriquece SourcedProfile com skills, highlights, etc.
```

**Ponto crítico:** O `AiAnalysisJob` SEMPRE roda e SOBRESCREVE o score e ai_metadata que o Python enviou. Portanto:

- O score que o Python envia via `deliver_cycle` é **temporário** — serve como score de triagem visível até o ProfileAnalyzer processar.
- O score final que o recrutador vê é o do ProfileAnalyzer.

---

## Opção 1: Python faz scoring de triagem → Rails refina (Fluxo Atual)

O Python envia um score inicial e evidências. O Rails então roda o ProfileAnalyzer para gerar o score definitivo por rubrica.

### Endpoint

```
POST /v1/users/background_agents/:agent_id/deliver_cycle
Authorization: Bearer <one_time_token>
Content-Type: application/json
```

### Payload Completo

```json
{
  "cycle_id": 68,
  "candidates_count": 15,
  "total_found": 200,
  "metadata": {
    "search_iterations": 2,
    "providers_used": ["local", "pearch"],
    "total_duration_ms": 45000
  },
  "candidates": [
    {
      "candidate_id": 12345,
      "source_provider": "local",
      "name": "João Silva",
      "email": "j****@email.com",
      "title": "Senior Ruby Developer",
      "city": "São Paulo",
      "state": "SP",
      "country": "Brazil",
      "location": "São Paulo, SP",
      "company": "PagSeguro",
      "experience_years": 7,
      "position_level": "senior",
      "skills": ["Ruby on Rails", "PostgreSQL", "REST API", "TDD", "Docker"],
      "linkedin_url": "https://linkedin.com/in/joaosilva",

      "score": 82,
      "category": "strong_match",
      "justification": "7 anos Ruby on Rails, PostgreSQL avançado, experiência em plataformas de pagamento",
      "strengths": [
        "Ruby on Rails sênior com 7 anos de experiência comprovada",
        "PostgreSQL com otimização de queries documentada",
        "Experiência direta em sistemas de pagamento (PagSeguro)"
      ],
      "concerns": [
        "Sem menção a Kafka ou sistemas de mensageria"
      ],
      "requirement_coverage": {
        "essential": 0.85,
        "important": 0.70,
        "nice_to_have": 0.40
      },
      "source_query": "Ruby on Rails Senior",
      "found_in_iteration": 1
    }
  ]
}
```

### Onde cada campo é salvo

| Campo do payload | Destino no Rails | Tabela.coluna |
|---|---|---|
| `candidate_id` | Lookup do Candidate local | — |
| `source_provider` | `search_source` | `sourced_profile_sourcings.search_source` |
| `score` | `score` + `search_score` | `sourced_profile_sourcings.score`, `.search_score` |
| `category` | `ai_metadata.category` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `justification` | `ai_metadata.justification` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `strengths` | `ai_metadata.strengths` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `concerns` | `ai_metadata.concerns` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `requirement_coverage` | `ai_metadata.requirement_coverage` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `source_query` | `ai_metadata.source_query` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `found_in_iteration` | `ai_metadata.found_in_iteration` | `sourced_profile_sourcings.ai_metadata` (JSONB) |
| `name`, `email`, `title`, etc. | Campos do perfil | `sourced_profiles.*` |
| `skills` | `skills_data` (array de hashes) | `sourced_profiles.skills_data` (JSONB) |
| `experiences` | `experiences_data` | `sourced_profiles.experiences_data` (JSONB) |

### Categorias válidas para `category`

| Categoria | Significado | Score esperado |
|---|---|---|
| `strong_match` | Candidato atende a maioria dos requisitos essenciais | 75-99 |
| `good_match` | Candidato atende requisitos importantes mas tem gaps | 55-74 |
| `partial_match` | Candidato atende parcialmente, precisa validação | 35-54 |
| `weak_match` | Poucos requisitos atendidos | 0-34 |

---

## Opção 2: Python faz scoring completo por rubrica (Substitui ProfileAnalyzer)

Se o Python implementar a mesma metodologia de rubrica do ProfileAnalyzer, os resultados precisam ser salvos em `sourced_profile_sourcings.analysis` para que o frontend os exiba corretamente.

**Requisito:** Criar um novo endpoint ou modificar o `deliver_cycle` para aceitar o campo `analysis` por candidato. Atualmente o `DeliverCandidatesService` NÃO persiste `analysis` — apenas `score`, `search_score` e `ai_metadata`.

### Implementação da Rubrica em Python

```python
MATCH_LEVELS = {
    "exceeds": 95,   # Supera com múltiplas evidências fortes
    "meets": 75,     # Atende completamente com evidência clara
    "partial": 40,   # Atende parcialmente, evidência fraca
    "missing": 0     # Não encontrado
}

PRIORITY_MULTIPLIERS = {
    "essential": 3,    # Eliminatório
    "important": 2,    # Diferenciador
    "nice_to_have": 1  # Bônus
}

MAX_SCORE = 99


def calculate_rubric_score(evaluation: list[dict]) -> int:
    """
    Calcula score determinístico a partir dos match_levels.
    NÃO confiar no score sugerido pelo LLM — recalcular sempre.
    """
    if not evaluation:
        return 0

    total_points = 0
    total_max = 0

    for item in evaluation:
        match_points = MATCH_LEVELS.get(item["match_level"], 0)
        multiplier = PRIORITY_MULTIPLIERS.get(item["priority"], 1)

        total_points += match_points * multiplier
        total_max += 95 * multiplier

    if total_max == 0:
        return 0

    score = round((total_points / total_max) * 100)
    return min(score, MAX_SCORE)
```

### Prompt LLM para Scoring (reproduzir o ProfileAnalyzer)

O LLM deve receber:

```python
system_prompt = """
Você é um recrutador técnico especialista em avaliação objetiva de candidatos.
Use metodologia de rubrica (exceeds/meets/partial/missing) para cada requisito.
Cite evidências específicas do currículo para justificar cada avaliação.
Retorne APENAS JSON válido e completo.

## REGRAS ANTI-VIÉS (OBRIGATÓRIO)
Avalie APENAS competências técnicas demonstradas. NÃO use como proxy de qualidade:
- Nome/prestígio de empresas anteriores
- Nome/ranking de universidades
- Gaps de emprego (podem ter razões legítimas)
- Tempo curto em empresas (contratos, projetos, layoffs)
- Localização geográfica ou idioma nativo
- Idade inferida por datas
Foco: skills demonstradas, projetos realizados, resultados mensuráveis.

## RED FLAGS: apenas inconsistências factuais
- inconsistent_dates: Datas contraditórias
- misrepresentation: Informação claramente falsa
- skill_mismatch: Skill declarada mas evidência contrária

## OBSERVAÇÕES NEUTRAS (NÃO penalizam):
- gap_in_employment, short_tenure, job_hopping
- career_downgrade, career_change
- overqualified, underqualified

## TEXTOS COMPLETOS
NUNCA truncar com "..." — reformular se necessário.
"""

user_prompt = f"""
# CONTEXTO DA BUSCA
{query}

# REQUISITOS ESTRUTURADOS
{requirements_text}

# CURRÍCULO DO CANDIDATO
{curriculum_text[:15000]}

# QUALIDADE DO PERFIL
Completude: {profile_quality['completeness']:.2f} ({profile_quality['word_count']} palavras)
Seções faltantes: {', '.join(profile_quality['missing']) or 'nenhuma'}

# METODOLOGIA
Match Levels:
- "exceeds" (95 pts): Supera com múltiplas evidências fortes
- "meets" (75 pts): Atende completamente com evidência clara
- "partial" (40 pts): Atende parcialmente
- "missing" (0 pts): Não encontrado

Pesos: essential=3x, important=2x, nice_to_have=1x
Score = Σ(peso × pontos) / Σ(peso × 95) × 100 (máximo: 99)

# FORMATO JSON OBRIGATÓRIO
{{
  "evaluation": [
    {{
      "requirement": "<requisito>",
      "priority": "essential|important|nice_to_have",
      "evidence": ["<citação do CV max 150 chars>"],
      "match_level": "exceeds|meets|partial|missing",
      "points": 95,
      "confidence": "high|medium|low",
      "rationale": "<justificativa max 200 chars>"
    }}
  ],
  "calculated_score": 78,
  "score_confidence": "high|medium|low",
  "confidence_factors": {{
    "profile_completeness": 0.8,
    "evidence_density": 0.75,
    "ambiguity_level": 0.2
  }},
  "one_liner": "<resumo do fit max 100 chars>",
  "red_flags": [
    {{"type": "inconsistent_dates|misrepresentation|skill_mismatch",
      "description": "<max 200 chars>", "severity": "low|medium|high"}}
  ],
  "neutral_observations": [
    {{"type": "gap_in_employment|career_change|short_tenure",
      "description": "<max 200 chars>"}}
  ],
  "development_areas": [
    {{"type": "skill_gap|experience_gap|seniority_gap|industry_gap|certification_gap|depth_gap",
      "description": "<max 200 chars>", "requirement": "<requisito>"}}
  ],
  "highlights": [
    {{"type": "career_progression|international_exposure|industry_match|technical_depth|leadership|education|notable_company|entrepreneurial|certifications",
      "description": "<max 200 chars>"}}
  ],
  "skills_assessment": {{
    "strong": ["skill1"],
    "mentioned": ["skill2"],
    "missing_from_search": ["skill3"]
  }},
  "suggested_questions": ["pergunta1", "pergunta2", "pergunta3"]
}}

REGRAS:
- Máximo 8 itens em evaluation
- Máximo 2 evidências por requisito (max 150 chars cada)
- Máximo 3 red_flags (APENAS inconsistências factuais)
- 1-3 development_areas OBRIGATÓRIOS
- Máximo 3 highlights
- JSON COMPLETO E VÁLIDO
"""
```

### Avaliação de Qualidade do Perfil (Pré-LLM)

```python
import re

def assess_profile_quality(text: str) -> dict:
    """Avalia completude do currículo antes de enviar ao LLM."""
    sections = {
        "contact": bool(re.search(r"email|telefone|phone|linkedin|contato", text, re.I)),
        "experience": bool(re.search(r"experiência|experience|trabalhou|worked|empresa|company", text, re.I)),
        "education": bool(re.search(r"formação|education|graduação|universidade|university|curso", text, re.I)),
        "skills": bool(re.search(r"competências|skills|tecnologias|conhecimento|habilidades", text, re.I)),
        "dates": len(re.findall(r"\d{2}/\d{4}|\d{4}", text)) >= 2,
    }

    completeness = sum(sections.values()) / len(sections)
    word_count = len(text.split())
    is_minimal = word_count < 100

    if completeness >= 0.8 and not is_minimal:
        confidence = "high"
    elif completeness >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    missing = [k for k, v in sections.items() if not v]

    return {
        "completeness": completeness,
        "missing": missing,
        "word_count": word_count,
        "is_minimal": is_minimal,
        "confidence": confidence,
    }
```

### Sanitização da Resposta do LLM

```python
VALID_MATCH_LEVELS = {"exceeds", "meets", "partial", "missing"}
VALID_PRIORITIES = {"essential", "important", "nice_to_have"}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_RED_FLAG_TYPES = {"inconsistent_dates", "misrepresentation", "skill_mismatch"}
VALID_NEUTRAL_TYPES = {
    "gap_in_employment", "short_tenure", "job_hopping",
    "career_downgrade", "career_change", "overqualified", "underqualified"
}
VALID_HIGHLIGHT_TYPES = {
    "career_progression", "international_exposure", "industry_match",
    "technical_depth", "leadership", "education", "notable_company",
    "entrepreneurial", "certifications"
}
VALID_DEV_AREA_TYPES = {
    "skill_gap", "experience_gap", "seniority_gap",
    "industry_gap", "certification_gap", "depth_gap"
}


def sanitize_evaluation(raw_evaluation: list[dict]) -> list[dict]:
    """Sanitiza e valida cada item da evaluation."""
    sanitized = []
    for item in (raw_evaluation or [])[:8]:
        match_level = item.get("match_level", "partial")
        if match_level not in VALID_MATCH_LEVELS:
            match_level = "partial"

        priority = item.get("priority", "important")
        if priority not in VALID_PRIORITIES:
            priority = "important"

        confidence = item.get("confidence", "medium")
        if confidence not in VALID_CONFIDENCES:
            confidence = "medium"

        sanitized.append({
            "requirement": str(item.get("requirement", ""))[:200],
            "priority": priority,
            "evidence": [str(e)[:150] for e in (item.get("evidence") or []) if e][:2],
            "match_level": match_level,
            "points": MATCH_LEVELS[match_level],
            "confidence": confidence,
            "rationale": str(item.get("rationale", ""))[:200],
        })

    return sanitized


def sanitize_red_flags(raw_flags: list[dict]) -> list[dict]:
    """Remove observações neutras dos red_flags."""
    sanitized = []
    for flag in (raw_flags or [])[:3]:
        flag_type = flag.get("type", "")
        if flag_type in VALID_NEUTRAL_TYPES:
            continue  # Mover para neutral_observations
        if flag_type not in VALID_RED_FLAG_TYPES:
            flag_type = "skill_mismatch"

        severity = flag.get("severity", "low")
        if severity not in {"low", "medium", "high"}:
            severity = "low"

        sanitized.append({
            "type": flag_type,
            "description": str(flag.get("description", ""))[:200],
            "severity": severity,
        })

    return sanitized


def sanitize_full_response(raw: dict, evaluation: list[dict]) -> dict:
    """Sanitiza a resposta completa do LLM."""
    score = calculate_rubric_score(evaluation)

    return {
        "evaluation": evaluation,
        "calculated_score": score,
        "score_confidence": raw.get("score_confidence", "medium"),
        "confidence_factors": raw.get("confidence_factors", {}),
        "one_liner": str(raw.get("one_liner", ""))[:150],
        "red_flags": sanitize_red_flags(raw.get("red_flags")),
        "neutral_observations": [
            {
                "type": o["type"] if o.get("type") in VALID_NEUTRAL_TYPES else "career_change",
                "description": str(o.get("description", ""))[:200],
            }
            for o in (raw.get("neutral_observations") or [])[:3]
        ],
        "development_areas": sanitize_development_areas(
            raw.get("development_areas"), evaluation
        ),
        "highlights": [
            {
                "type": h["type"] if h.get("type") in VALID_HIGHLIGHT_TYPES else "technical_depth",
                "description": str(h.get("description", ""))[:200],
            }
            for h in (raw.get("highlights") or [])[:3]
        ],
        "skills_assessment": {
            "strong": [str(s) for s in (raw.get("skills_assessment", {}).get("strong") or [])][:10],
            "mentioned": [str(s) for s in (raw.get("skills_assessment", {}).get("mentioned") or [])][:10],
            "missing_from_search": [str(s) for s in (raw.get("skills_assessment", {}).get("missing_from_search") or [])][:5],
        },
        "suggested_questions": [
            str(q)[:200] for q in (raw.get("suggested_questions") or []) if q
        ][:3],
    }


def sanitize_development_areas(raw_areas: list[dict], evaluation: list[dict]) -> list[dict]:
    """Garante pelo menos 1 development_area."""
    sanitized = [
        {
            "type": a["type"] if a.get("type") in VALID_DEV_AREA_TYPES else "skill_gap",
            "description": str(a.get("description", ""))[:200],
            "requirement": str(a.get("requirement", ""))[:150],
        }
        for a in (raw_areas or [])[:3]
    ]

    # Inferir de requisitos partial/missing se vazio
    if not sanitized and evaluation:
        for item in evaluation:
            if item["match_level"] in ("partial", "missing"):
                area_type = "skill_gap" if item["match_level"] == "missing" else "depth_gap"
                sanitized.append({
                    "type": area_type,
                    "description": f"Candidato precisa desenvolver em {item['requirement'].lower()}",
                    "requirement": item["requirement"],
                })
            if len(sanitized) >= 3:
                break

    # Fallback
    if not sanitized:
        sanitized = [{
            "type": "depth_gap",
            "description": "Perfil precisa de validação mais profunda em entrevista",
            "requirement": "",
        }]

    return sanitized
```

---

## Formato Final: `analysis` (JSONB)

Este é o formato EXATO que deve ser salvo em `sourced_profile_sourcings.analysis`. O frontend lê cada campo deste JSON.

```json
{
  "score": 73,
  "one_liner": "Sênior Rails forte em pagamentos, sem experiência em mensageria",
  "scoring_method": "rubric_based",
  "calculated_score": 73,
  "generated_at": "2026-04-05T20:30:00Z",
  "ai_source": "gemini",
  "sourcing_id": 1491,
  "sourcing_query": "Senior Ruby on Rails Developer",

  "evaluation": [
    {
      "requirement": "Ruby on Rails Sênior",
      "priority": "essential",
      "match_level": "exceeds",
      "points": 95,
      "confidence": "high",
      "rationale": "7 anos de experiência comprovada com projetos de alta escala",
      "evidence": [
        "7 anos em Ruby on Rails, PagSeguro e CI&T",
        "APIs RESTful processando 50k transações/dia"
      ]
    },
    {
      "requirement": "PostgreSQL avançado",
      "priority": "essential",
      "match_level": "meets",
      "points": 75,
      "confidence": "high",
      "rationale": "Otimização de queries com resultados mensuráveis",
      "evidence": [
        "Reduziu latência de queries em 40% via índices parciais"
      ]
    },
    {
      "requirement": "Kafka ou mensageria assíncrona",
      "priority": "important",
      "match_level": "missing",
      "points": 0,
      "confidence": "high",
      "rationale": "Nenhuma menção a Kafka, RabbitMQ ou mensageria",
      "evidence": []
    }
  ],

  "query_insights": [
    {
      "subquery": "Ruby on Rails Sênior",
      "priority": "essential",
      "match_level": "exceeds",
      "short_rationale": "7 anos de experiência comprovada com projetos de alta escala",
      "short_quotes": ["7 anos em Ruby on Rails, PagSeguro e CI&T"]
    }
  ],

  "red_flags": [],
  "neutral_observations": [
    {
      "type": "short_tenure",
      "description": "2 passagens de menos de 1 ano (2019-2020), possivelmente contratos"
    }
  ],
  "development_areas": [
    {
      "type": "skill_gap",
      "description": "Sem experiência com Kafka ou sistemas de mensageria assíncrona",
      "requirement": "Kafka ou mensageria assíncrona"
    }
  ],
  "highlights": [
    {
      "type": "industry_match",
      "description": "4 anos em plataforma de pagamentos — match direto com requisito"
    }
  ],
  "skills_assessment": {
    "strong": ["Ruby on Rails", "PostgreSQL", "REST API", "TDD"],
    "mentioned": ["Docker", "CI/CD", "Redis"],
    "missing_from_search": ["Kafka", "RabbitMQ"]
  },
  "suggested_questions": [
    "Qual sua experiência com processamento assíncrono e filas?",
    "Como implementou caching em camadas nos seus projetos?"
  ]
}
```

**Campo obrigatório `query_insights`:** O frontend usa TANTO `evaluation` quanto `query_insights`. O `query_insights` é o formato legado com chaves diferentes:

| `evaluation` | `query_insights` |
|---|---|
| `requirement` | `subquery` |
| `rationale` | `short_rationale` |
| `evidence` | `short_quotes` |

Ambos devem conter os mesmos dados, apenas com chaves diferentes.

---

## Formato Final: `ai_metadata` (JSONB)

Salvo em `sourced_profile_sourcings.ai_metadata`:

```json
{
  "ai_source": "gemini",
  "model": "gemini-2.5-flash",
  "sourcing_id": 1491,
  "ran_at": "2026-04-05T20:30:00Z",
  "prompt_tokens": 3500,
  "completion_tokens": 1200,
  "total_tokens": 4700,
  "cost_usd": 0.00273,
  "profile_quality": {
    "completeness": 0.8,
    "missing": ["skills"],
    "word_count": 2543,
    "is_minimal": false,
    "confidence": "high"
  },
  "score_confidence": "high",
  "scoring_method": "rubric_based"
}
```

---

## Endpoint para Salvar Score Completo

### Via `deliver_cycle` (fluxo atual)

O `deliver_cycle` salva apenas `score`, `search_score` e `ai_metadata` (com category/justification do agente). O `AiAnalysisJob` depois sobrescreve com o score do ProfileAnalyzer.

Se o Python quer ser o scorer final, é necessário que o `deliver_cycle` ou um endpoint dedicado aceite o campo `analysis` e o salve diretamente no `SourcedProfileSourcing.analysis`.

### Endpoint recomendado (novo)

```
PATCH /v1/users/background_agents/:agent_id/deliver_analysis
Authorization: Bearer <one_time_token>
Content-Type: application/json
```

```json
{
  "cycle_id": 68,
  "results": [
    {
      "sourced_profile_sourcing_id": 456,
      "score": 73,
      "analysis": { "...formato completo acima..." },
      "ai_metadata": { "...formato completo acima..." }
    }
  ]
}
```

Este endpoint deve:
1. Atualizar `sourced_profile_sourcings` com `score`, `analysis`, `ai_metadata`
2. Chamar `AiEnrichmentService.new(sps).enrich!` para enriquecer o perfil
3. Broadcast via `SourcingChannel` com `type: "profile_analyzed"`
4. **NÃO** enfileirar `AiAnalysisJob` (já está com análise completa)

### Alternativa: Modificar `deliver_cycle`

Adicionar suporte ao campo `analysis` por candidato no payload de `deliver_cycle`. Se `analysis` estiver presente, o `DeliverCandidatesService` deve salvar diretamente e marcar o SPS como já analisado (evitando que o `AiAnalysisJob` sobrescreva).

---

## Regras de Validação do Score

O Python DEVE garantir estas regras antes de entregar:

| Regra | Validação |
|---|---|
| Score calculado, não inventado | `score = calculate_rubric_score(evaluation)` — nunca confiar no LLM |
| Score máximo 99 | `min(score, 99)` |
| Score mínimo 0 | `max(score, 0)` |
| `match_level` válido | Apenas: `exceeds`, `meets`, `partial`, `missing` |
| `priority` válida | Apenas: `essential`, `important`, `nice_to_have` |
| `confidence` válida | Apenas: `high`, `medium`, `low` |
| Max 8 evaluation items | Truncar se > 8 |
| Max 2 evidências por item | Truncar se > 2, max 150 chars cada |
| Max 3 red_flags | Apenas inconsistências factuais |
| Min 1 development_area | Inferir de evaluation se LLM não retornou |
| Max 3 highlights | Truncar se > 3 |
| Textos sem truncamento | Nunca "...", reformular se necessário |
| `one_liner` max 150 chars | Resumo do fit candidato-vaga |
| `suggested_questions` max 3 | Max 200 chars cada |

---

## Checklist de Integração

```
[ ] Python implementa assess_profile_quality() para avaliar completude
[ ] Python implementa prompt LLM com regras anti-viés
[ ] Python implementa calculate_rubric_score() determinístico
[ ] Python implementa sanitize_evaluation() com validação de tipos
[ ] Python implementa sanitize_red_flags() separando neutral_observations
[ ] Python garante min 1 development_area
[ ] Python gera query_insights (formato legado) a partir de evaluation
[ ] Python salva analysis no formato JSONB documentado
[ ] Python salva ai_metadata com tokens, custo, profile_quality
[ ] Frontend exibe evaluation, highlights, development_areas, suggested_questions
[ ] Score é recalculado pelo Python (não confia no LLM)
[ ] Textos nunca truncados com "..."
```
