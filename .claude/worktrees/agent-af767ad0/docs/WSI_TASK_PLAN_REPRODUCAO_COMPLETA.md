# WSI — Task Plan: Reprodução Completa da Metodologia
## Plataforma LIA · WeDOTalent · v1.0 · 25/03/2026

> **Finalidade:** Documento de referência para o time de desenvolvimento reproduzir 100% do sistema WSI (Work Suitability Index) em um ambiente novo.
> **Fonte de verdade:** `docs/WSI_FLOW_PONTA_A_PONTA.md` + `docs/WSI_METHODOLOGY_COMPLETE_v2.md` + código validado em 25/03/2026.
> **Modo de uso:** Cada tarefa tem critério de aceite. Marcar `[x]` após implementação e validação.

---

## Índice

1. [Fundamentos e Arquitetura](#1-fundamentos-e-arquitetura)
2. [Banco de Dados](#2-banco-de-dados)
3. [Constantes e Configurações](#3-constantes-e-configurações)
4. [Bloco A — F1: Análise de Qualidade do JD](#4-bloco-a--f1-análise-de-qualidade-do-jd)
5. [Bloco A — F2-F3: Big Five / OCEAN](#5-bloco-a--f2-f3-big-five--ocean)
6. [Bloco A — F4: Resolução de Senioridade](#6-bloco-a--f4-resolução-de-senioridade)
7. [Bloco A — F5: Distribuição Adaptativa de Perguntas](#7-bloco-a--f5-distribuição-adaptativa-de-perguntas)
8. [Bloco A — F6: Geração de Perguntas com Validação](#8-bloco-a--f6-geração-de-perguntas-com-validação)
9. [Bloco B — F7: Canais de Triagem (E1, E2, E3)](#9-bloco-b--f7-canais-de-triagem-e1-e2-e3)
10. [Bloco B — F8: Scoring Tri-Componente](#10-bloco-b--f8-scoring-tri-componente)
11. [Bloco B — F9: Composição WSI Final](#11-bloco-b--f9-composição-wsi-final)
12. [Bloco B — F10: Gates Absolutos e Decisão](#12-bloco-b--f10-gates-absolutos-e-decisão)
13. [Bloco B — F11: Relatório e Feedback](#13-bloco-b--f11-relatório-e-feedback)
14. [Endpoints REST](#14-endpoints-rest)
15. [Pipeline LangGraph (Canal E2)](#15-pipeline-langgraph-canal-e2)
16. [Canal de Voz — OpenMic.ai (E3)](#16-canal-de-voz--openmicai-e3)
17. [Frontend — Modal de Detalhes WSI](#17-frontend--modal-de-detalhes-wsi)
18. [Frontend — Painel de Avaliação do JD](#18-frontend--painel-de-avaliação-do-jd)
19. [Testes Automatizados](#19-testes-automatizados)
20. [Compliance e Segurança](#20-compliance-e-segurança)
21. [Itens Futuros (não implementar agora)](#21-itens-futuros-não-implementar-agora)
22. [Checklist Final de Entrega](#22-checklist-final-de-entrega)

---

## 1. Fundamentos e Arquitetura

### Conceito
O WSI é um índice 0–5 (ou 0–10 internamente em alguns contextos) que mede a adequação de um candidato a uma vaga usando 4 frameworks científicos:

| Framework | Uso |
|-----------|-----|
| **CBI** (Competency-Based Interview) | Perguntas técnicas — pede situação passada real |
| **Bloom's Taxonomy** | Níveis cognitivos esperados vs. demonstrados (1=Recordar … 6=Criar) |
| **Dreyfus Model** | Proficiência (1=Iniciante … 5=Especialista) |
| **Big Five / OCEAN** | Perfil comportamental via 5 traits (O/C/E/A/N) |

### Dois Blocos
```
BLOCO A (por vaga, 1x):
  F1 → F2 → F3 → F4 → F5 → F6
  Análise JD → OCEAN → Ranking Traits → Senioridade → Distribuição → Gerar Perguntas

BLOCO B (por candidato, n vezes):
  F7 → F8 → F9 → F10 → F11
  Coletar Respostas → Scoring → Composição WSI → Gates → Relatório + Feedback
```

### Stack obrigatória

- **Backend:** FastAPI (Python 3.11), SQLAlchemy 2.0 async, PostgreSQL, Redis
- **IA:** LangGraph + LangChain, Claude Sonnet 4.5 (Anthropic) — modelo primário
- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Voz:** OpenMic.ai (E3), Deepgram STT
- **Filas:** Celery + RabbitMQ (para callbacks de voz)

### Checklist de Pré-requisitos

- [ ] Ambiente Python 3.11+ configurado
- [ ] PostgreSQL + pgvector instalados
- [ ] Redis disponível
- [ ] Chave de API Anthropic (Claude Sonnet 4.5)
- [ ] Conta OpenMic.ai com agent configurado (para E3)
- [ ] Conta Deepgram (STT)
- [ ] RabbitMQ + Celery configurados

---

## 2. Banco de Dados

### 2.1 Tabela `wsi_results`

Principal tabela de resultados WSI por candidato/vaga.

```sql
CREATE TABLE wsi_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        VARCHAR(255) NOT NULL,
    job_vacancy_id      VARCHAR(255) NOT NULL,
    company_id          VARCHAR(255) NOT NULL,
    session_id          VARCHAR(255),

    -- Scores (escala 0-5)
    technical_wsi       FLOAT NOT NULL DEFAULT 0,
    behavioral_wsi      FLOAT NOT NULL DEFAULT 0,
    overall_wsi         FLOAT NOT NULL DEFAULT 0,

    -- Classificação textual
    classification      VARCHAR(50),  -- excepcional|excelente|alto|medio|regular|baixo

    -- Gates e decisão
    failed_gates        JSON DEFAULT '[]',   -- lista de gates ativados: ["G1","G4"]
    decision_result     VARCHAR(50),  -- APROVADO|EM_AVALIACAO|REPROVADO
    decision_confidence VARCHAR(20),  -- alta|media|baixa
    human_review_required BOOLEAN DEFAULT false,

    -- Cache do relatório F11 (F11-3)
    f11_report_json     JSONB,

    -- Metadados
    screening_type      VARCHAR(50) DEFAULT 'text',  -- text|voice|async
    seniority_resolved  VARCHAR(50),
    llm_fallback_count  INTEGER DEFAULT 0,
    score_variance      FLOAT DEFAULT 0,

    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE (candidate_id, job_vacancy_id),
    INDEX idx_wsi_results_job (job_vacancy_id),
    INDEX idx_wsi_results_candidate (candidate_id),
    INDEX idx_wsi_results_company (company_id),
    INDEX idx_wsi_results_overall (overall_wsi)
);
```

**Checklist:**
- [ ] Criar tabela `wsi_results` com todas as colunas acima
- [ ] Criar índices listados
- [ ] Validar constraint UNIQUE `(candidate_id, job_vacancy_id)`
- [ ] Confirmar coluna `f11_report_json JSONB` presente (cache F11-3)

---

### 2.2 Tabela `wsi_sessions`

Sessões de triagem (uma por candidato/vaga, por canal).

```sql
CREATE TABLE wsi_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    VARCHAR(255) NOT NULL,
    job_vacancy_id  VARCHAR(255) NOT NULL,
    company_id      VARCHAR(255) NOT NULL,
    screening_type  VARCHAR(50) NOT NULL,  -- text|voice|async
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
                    -- pending|in_progress|completed|expired|failed
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    expires_at      TIMESTAMP,   -- E1: link expira em 72h (armazenado em Redis também)
    metadata        JSONB,

    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    INDEX idx_wsi_sessions_candidate (candidate_id),
    INDEX idx_wsi_sessions_job (job_vacancy_id),
    INDEX idx_wsi_sessions_status (status)
);
```

**Checklist:**
- [ ] Criar tabela `wsi_sessions`
- [ ] Canal E1 (async): configurar TTL 72h no Redis (`session:{id}:token`)

---

### 2.3 Tabela `screening_question_sets`

Perguntas geradas para cada vaga (reutilizadas entre candidatos).

```sql
CREATE TABLE screening_question_sets (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_vacancy_id          VARCHAR(255) NOT NULL,
    version                 INTEGER NOT NULL DEFAULT 1,
    questions_hash          VARCHAR(64) NOT NULL,  -- SHA-256 do JSON
    questions_snapshot      JSONB NOT NULL,         -- array completo de WSIQuestion
    questions_count         INTEGER NOT NULL,
    block_distribution      JSONB,  -- {technical: N, behavioral: M}
    seniority_resolved      VARCHAR(50),
    mode                    VARCHAR(20) DEFAULT 'compact',  -- compact|full
    source                  VARCHAR(50) NOT NULL,   -- ai_generated|manual
    created_by              VARCHAR(255),
    is_active               BOOLEAN DEFAULT true,
    difficulty_coefficient  FLOAT,
    metadata                JSONB,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW(),

    UNIQUE (job_vacancy_id, version),
    INDEX idx_qsets_job_active (job_vacancy_id, is_active)
);
```

**Checklist:**
- [ ] Criar tabela `screening_question_sets`
- [ ] Implementar lógica de versioning (nova geração → version++)
- [ ] Hash SHA-256 do `questions_snapshot` para detecção de duplicatas

---

### 2.4 Tabela `wsi_responses`

Respostas brutas e análises por pergunta.

```sql
CREATE TABLE wsi_responses (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID NOT NULL REFERENCES wsi_sessions(id),
    question_id             VARCHAR(255) NOT NULL,  -- id da WSIQuestion
    candidate_id            VARCHAR(255) NOT NULL,
    job_vacancy_id          VARCHAR(255) NOT NULL,

    -- Resposta bruta
    response_text           TEXT,
    response_audio_url      VARCHAR(1024),
    response_hash           VARCHAR(64),  -- SHA-256 (EU AI Act auditoria)

    -- Análise F8
    autodeclaration_score   FLOAT,   -- 1-5
    context_score           FLOAT,   -- 1-5
    bloom_demonstrated      INTEGER, -- 1-6
    dreyfus_demonstrated    INTEGER, -- 1-5
    star_components         JSONB,   -- {S: bool, T: bool, A: bool, R: bool}
    star_score              FLOAT,   -- 0-1
    evidences               JSONB,   -- lista de strings
    red_flags               JSONB,   -- lista de strings
    consistency_penalty     FLOAT DEFAULT 0,
    final_score             FLOAT,   -- 1-5
    justification           TEXT,

    -- Contexto da pergunta
    competency              VARCHAR(255),
    framework               VARCHAR(50),  -- CBI|Bloom|Dreyfus|BigFive
    question_type           VARCHAR(50),  -- technical|behavioral|situational
    bloom_expected          INTEGER,
    dreyfus_expected        INTEGER,
    is_critical             BOOLEAN DEFAULT false,
    trait_weight            FLOAT DEFAULT 1.0,  -- F9-1: peso do trait OCEAN

    -- Flags de validação (F6.8)
    needs_manual_review     BOOLEAN DEFAULT false,
    validation_flags        JSONB,

    created_at              TIMESTAMP DEFAULT NOW(),

    INDEX idx_wsi_responses_session (session_id),
    INDEX idx_wsi_responses_candidate (candidate_id)
);
```

**Checklist:**
- [ ] Criar tabela `wsi_responses`
- [ ] Armazenar `response_hash` (SHA-256) para auditoria EU AI Act
- [ ] Confirmar campo `trait_weight` presente para F9-1

---

### 2.5 Tabelas Auxiliares

```sql
-- Chamadas de voz (Canal E3)
CREATE TABLE voice_screening_calls (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id             VARCHAR(255) NOT NULL UNIQUE,
    agent_id            VARCHAR(255),
    call_type           VARCHAR(50) NOT NULL,   -- outbound|inbound
    call_status         VARCHAR(50) NOT NULL,   -- completed|failed|in_progress
    direction           VARCHAR(20) NOT NULL,
    from_number         VARCHAR(50),
    to_number           VARCHAR(50),
    start_timestamp     TIMESTAMP,
    end_timestamp       TIMESTAMP,
    duration_seconds    INTEGER,
    candidate_name      VARCHAR(255) NOT NULL,
    candidate_id        VARCHAR(255),
    candidate_phone     VARCHAR(50),
    candidate_email     VARCHAR(255),
    job_title           VARCHAR(500) NOT NULL,
    job_description     TEXT,
    required_skills     JSONB DEFAULT '[]',
    transcript          TEXT,
    transcript_object   JSONB DEFAULT '[]',
    webhook_event       VARCHAR(100),
    webhook_payload     JSONB,
    processing_status   VARCHAR(50) DEFAULT 'pending',
    is_analyzed         BOOLEAN DEFAULT false,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),

    INDEX idx_voice_calls_candidate (candidate_id),
    INDEX idx_voice_calls_status (processing_status)
);

-- Análises de chamadas de voz (Canal E3)
CREATE TABLE voice_screening_analyses (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_call_id       UUID NOT NULL UNIQUE REFERENCES voice_screening_calls(id),
    analysis_model          VARCHAR(100),   -- claude-sonnet-4.5
    analysis_method         VARCHAR(100) DEFAULT 'lia_ai_deep_analysis',
    tech_skills_mentioned   JSONB DEFAULT '[]',
    tech_skills_matched     JSONB DEFAULT '[]',
    tech_skills_missing     JSONB DEFAULT '[]',
    tech_experience_years   VARCHAR(50),
    tech_score              INTEGER,        -- 0-100
    comm_clarity            VARCHAR(20),    -- baixa|média|alta
    comm_confidence         VARCHAR(20),
    comm_engagement         VARCHAR(20),
    comm_score              INTEGER,
    fit_motivation          TEXT,
    fit_red_flags           JSONB DEFAULT '[]',
    fit_green_flags         JSONB DEFAULT '[]',
    fit_score               INTEGER,
    overall_score           INTEGER NOT NULL,           -- 0-100
    overall_recommendation  VARCHAR(50) NOT NULL,       -- reject|maybe|interview|strong_yes
    overall_confidence      VARCHAR(20),
    key_strengths           JSONB DEFAULT '[]',
    key_concerns            JSONB DEFAULT '[]',
    next_steps              TEXT,
    summary                 TEXT,
    full_analysis_payload   JSONB,
    analysis_status         VARCHAR(50) DEFAULT 'completed',
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Perguntas padrão por empresa (pré-qualificação)
CREATE TABLE company_screening_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      VARCHAR(255) NOT NULL,
    question_text   TEXT NOT NULL,
    question_type   VARCHAR(50) DEFAULT 'text',
    options         JSONB,
    is_required     BOOLEAN DEFAULT true,
    is_eliminatory  BOOLEAN DEFAULT false,
    expected_answer VARCHAR(255),
    category        VARCHAR(100),  -- availability|salary|experience|language|legal|logistics
    "order"         INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    INDEX idx_company_questions_company (company_id)
);
```

**Checklist:**
- [ ] Criar tabela `voice_screening_calls`
- [ ] Criar tabela `voice_screening_analyses`
- [ ] Criar tabela `company_screening_questions`
- [ ] Verificar foreign keys e indexes

---

## 3. Constantes e Configurações

> **Arquivo:** `app/domains/cv_screening/constants/wsi_constants.py`

### 3.1 Distribuições de Perguntas (F5)

```python
SENIORITY_DISTRIBUTIONS = {
    "compact": {   # 7 perguntas total
        "estagiario": {"technical": 5, "behavioral": 2},
        "junior":     {"technical": 5, "behavioral": 2},
        "pleno":      {"technical": 5, "behavioral": 2},
        "senior":     {"technical": 4, "behavioral": 3},
        "lead":       {"technical": 3, "behavioral": 4},
        "principal":  {"technical": 4, "behavioral": 3},
        "diretor":    {"technical": 3, "behavioral": 4},
        "executive":  {"technical": 2, "behavioral": 5},
    },
    "full": {      # 12 perguntas total
        "estagiario": {"technical": 9,  "behavioral": 3},
        "junior":     {"technical": 9,  "behavioral": 3},
        "pleno":      {"technical": 8,  "behavioral": 4},
        "senior":     {"technical": 7,  "behavioral": 5},
        "lead":       {"technical": 7,  "behavioral": 5},
        "principal":  {"technical": 7,  "behavioral": 5},
        "diretor":    {"technical": 7,  "behavioral": 5},
        "executive":  {"technical": 7,  "behavioral": 5},
    }
}
```

### 3.2 Pesos por Senioridade (F9)

```python
SENIORITY_WEIGHTS = {
    "estagiario": {"technical": 0.6875, "behavioral": 0.3125},
    "junior":     {"technical": 0.625,  "behavioral": 0.375},
    "pleno":      {"technical": 0.6875, "behavioral": 0.3125},
    "senior":     {"technical": 0.5625, "behavioral": 0.4375},
    "lead":       {"technical": 0.4375, "behavioral": 0.5625},
    "principal":  {"technical": 0.50,   "behavioral": 0.50},
    "diretor":    {"technical": 0.3125, "behavioral": 0.6875},
    "vp_clevel":  {"technical": 0.25,   "behavioral": 0.75},
}
```

### 3.3 Top-N Traits Big Five por Senioridade (F3)

```python
SENIORITY_BIGFIVE_TOP_N = {
    "estagiario": 2,
    "junior":     2,
    "pleno":      3,
    "senior":     3,
    "lead":       4,
    "principal":  4,
    "diretor":    5,
    "vp_clevel":  5,
}
```

### 3.4 Pesos da Fórmula Tri-Componente (F8)

```python
# Perguntas TÉCNICAS
WSI_FORMULA_WEIGHTS_TECHNICAL = {
    "autodeclaracao":      0.35,
    "evidencias_tecnicas": 0.40,
    "bloom_alinhamento":   0.25,
}

# Perguntas COMPORTAMENTAIS
WSI_FORMULA_WEIGHTS_BEHAVIORAL = {
    "star_estrutura":    0.35,
    "sinais_trait":      0.40,
    "bloom_alinhamento": 0.25,
}
```

### 3.5 Pesos STAR

```python
STAR_COMPONENT_WEIGHTS = {
    "S": 0.20,  # Situação
    "T": 0.20,  # Tarefa
    "A": 0.40,  # Ação (maior peso)
    "R": 0.20,  # Resultado
}
```

### 3.6 Thresholds e Gates

```python
WSI_CUTOFFS = {
    "approved_auto":  3.75,   # ≥ 3.75 sem gates → APROVADO
    "review_min":     3.00,   # 3.0–3.74 → EM_AVALIACAO
    "rejected_below": 3.00,   # < 3.0 → REPROVADO (a menos que G3 ative antes)
}

GATE_G3_THRESHOLD = 2.0      # WSI < 2.0 → G3 ativa → REPROVADO imediato

# Penalidades automáticas (F8 Camada 1)
PENALTY_TRIGGERS = {
    "inflation": {
        "keywords": [
            "expert", "especialista", "domino completamente",
            "5 de 5", "perfeito nisso", "melhor do mercado"
        ],
        "penalty": -1.0,
    },
    "generic": {
        "keywords": ["trabalhei com isso", "tenho experiência", "já fiz"],
        "penalty": -0.5,
    },
    "no_context": {
        "min_words": 20,
        "penalty": -0.3,
    },
}

# Mínimos de qualidade do JD (F1.B)
MIN_TECHNICAL_SKILLS_FOR_WSI    = 9  # D3
MIN_BEHAVIORAL_COMPETENCIES_WSI = 5  # D4

JD_QUALITY_THRESHOLDS = {
    "critico":      (0,  29),   # bloqueio hard
    "insuficiente": (30, 49),   # aviso, prossegue com ressalvas
    "adequado":     (50, 69),
    "bom":          (70, 84),
    "excelente":    (85, 100),
}
```

### 3.7 Rótulos Canônicos

```python
WSI_CLASSIFICATION_LABELS = {
    (4.5, 5.0): ("excepcional", "Excepcional"),
    (4.0, 4.5): ("excelente",   "Excelente"),
    (3.5, 4.0): ("alto",        "Alto"),
    (3.0, 3.5): ("medio",       "Médio"),
    (2.25, 3.0):("abaixo_da_media", "Abaixo da média"),
    (0.0, 2.25):("regular",     "Regular / Baixo"),
}

BIG_FIVE_RECRUITER_LABELS = {
    "openness":          "Abertura a mudanças",
    "conscientiousness": "Organização e disciplina",
    "extraversion":      "Sociabilidade",
    "agreeableness":     "Cooperação",
    "stability":         "Estabilidade emocional",
}

WSI_BLOCK_NAMES = {
    0: "Abordagem Inicial",
    1: "Apresentação da Oportunidade",
    2: "Perguntas Padrão da Empresa",
    3: "Competências Técnicas",
    4: "Competências Comportamentais e Fit",
    5: "Resultado e Encerramento",
}
```

**Checklist:**
- [ ] Arquivo `wsi_constants.py` criado com TODOS os dicts acima
- [ ] `SENIORITY_DISTRIBUTIONS`: compact=7 total, full=12 total — verificar soma por senioridade
- [ ] `SENIORITY_WEIGHTS`: verificar que `technical + behavioral = 1.0` para cada nível
- [ ] `STAR_COMPONENT_WEIGHTS`: verificar soma = 1.0 (0.20+0.20+0.40+0.20)
- [ ] `WSI_FORMULA_WEIGHTS_*`: verificar soma = 1.0 para cada dict
- [ ] `SENIORITY_BIGFIVE_TOP_N`: estagiario=2, pleno=3, lead=4, diretor=5

---

## 4. Bloco A — F1: Análise de Qualidade do JD

> **Arquivo:** `wsi_service.py` (método `analyze_jd_quality`) + `wsi_endpoints.py` / `JDEvaluationPanel.tsx`

### 4.1 O que F1 faz

- Recebe JD em texto livre
- Extrai: skills técnicas, competências comportamentais, responsabilidades, contexto cultural
- Calcula JD Quality Score (0–100) baseado em dimensões D1-D6
- Valida mínimos D3 (≥9 skills técnicas) e D4 (≥5 comportamentais)
- Bloqueia pipeline se score < 30 (`ready_for_processing: false`)
- Retorna `enriched_jd` estruturado (JSON) para uso em F2–F6

### 4.2 Saída: estrutura `enriched_jd`

```python
{
    "titulo": str,
    "empresa": str,
    "senioridade": str,           # detectada pelo LLM
    "competencias_tecnicas": [
        {
            "nome": str,
            "nivel_bloom_esperado": int,    # 1-6
            "nivel_dreyfus_esperado": int,  # 1-5
            "is_critical": bool,
            "peso": float,                  # 0-1
        }
    ],
    "competencias_comportamentais": [
        {
            "nome": str,
            "big_five_mapping": str,        # openness|conscientiousness|extraversion|agreeableness|stability
            "peso": float,
        }
    ],
    "responsabilidades": [str],
    "cultura_organizacional": str,
    "jd_quality_score": int,               # 0-100
    "ready_for_processing": bool,
    "warnings": [str],                     # D3/D4 thresholds
}
```

### 4.3 LLM Call — F1.B

```
Modelo: Claude Sonnet 4.5
Temperature: 0.2
Max tokens: 4000
Saída: JSON estruturado conforme schema acima
```

**Checklist — F1:**
- [ ] Endpoint `POST /wsi/analyze-jd` ou `POST /wsi/jd-evaluate` implementado
- [ ] LLM extrai `competencias_tecnicas` com `nivel_bloom_esperado` e `nivel_dreyfus_esperado`
- [ ] LLM extrai `competencias_comportamentais` com `big_five_mapping` preenchido
- [ ] Validação D3: `len(competencias_tecnicas) < 9` → warning adicionado
- [ ] Validação D4: `len(competencias_comportamentais) < 5` → warning adicionado
- [ ] `ready_for_processing = False` quando `jd_quality_score < 30`
- [ ] `enriched_jd` persistido no banco associado à vaga
- [ ] Bridge F1→F6: `enriched_jd` passado como input para geração de perguntas

---

## 5. Bloco A — F2-F3: Big Five / OCEAN

> **Arquivo:** `wsi_service.py` → `WSIQuestionGenerator._extract_ocean_scores()` + `_select_traits_by_seniority()`

### 5.1 F2.5 — Extração OCEAN via LLM (Abordagem C)

```
Modelo: Claude Sonnet 4.5
Temperature: 0.1
Max tokens: 800
Input: JD completo (preferencialmente enriched_jd.cultura_organizacional + competencias_comportamentais)
Output: Lista de 5 OceanTraitScore
```

**Schema `OceanTraitScore`:**
```python
{
    "trait":      str,        # openness|conscientiousness|extraversion|agreeableness|stability
    "score":      int,        # 0-100 — intensidade exigida pela vaga
    "confidence": str,        # high|medium|low
    "evidence":   [str],      # citações literais do JD
}
```

**Prompt OCEAN — rubric NEO-PI-R:**
O prompt deve incluir a rubric descritiva de cada trait para calibração:
- **Openness:** curiosidade intelectual, criatividade, abertura à mudança, aprendizado contínuo
- **Conscientiousness:** disciplina, organização, orientação a resultados, confiabilidade
- **Extraversion:** sociabilidade, liderança, comunicação proativa, network building
- **Agreeableness:** cooperação, empatia, trabalho em equipe, flexibilidade interpessoal
- **Stability (Neuroticism invertido):** resiliência, equilíbrio emocional, tolerância à pressão

### 5.2 F3 — Ranking de Traits

```python
# Selecionar top-N traits conforme senioridade
N = SENIORITY_BIGFIVE_TOP_N[seniority]
top_traits = sorted(ocean_scores, key=lambda x: x.score, reverse=True)[:N]

# Normalizar pesos
soma_scores = sum(t.score for t in top_traits)
for trait in top_traits:
    trait.weight_normalized = trait.score / soma_scores

# RESULTADO: peso proporcional — trait com score 80 tem peso maior que trait com score 50
```

**Regra de fallback:** Se F3 indisponível (OCEAN não extraído), usar `weight_normalized = 1.0` para todos os traits.

**Checklist — F2/F3:**
- [ ] Método `_extract_ocean_scores(job_description, behavioral_competencies)` implementado
- [ ] Retorna exatamente 5 traits (um por dimensão OCEAN)
- [ ] Cada trait tem `score` (0-100), `confidence` (high|medium|low), `evidence` (lista)
- [ ] Método `_select_traits_by_seniority(ocean_scores, seniority, mode)` implementado
- [ ] Seleciona top-N conforme `SENIORITY_BIGFIVE_TOP_N`
- [ ] Normaliza pesos: `weight_i = score_i / soma_scores`
- [ ] Fallback para `weight = 1.0` quando F3 não disponível

---

## 6. Bloco A — F4: Resolução de Senioridade

> **Arquivo:** `seniority_resolver.py` → `resolve_seniority_full()`

### 6.1 Motor Multi-Sinal (5 fontes)

```
Sinal 1: Título do cargo (regex + ML)
Sinal 2: Anos de experiência (CV + JD)
Sinal 3: Faixa salarial (se disponível)
Sinal 4: Skills mencionadas (nível de complexidade)
Sinal 5: LLM como árbitro final (temp=0.0)

Resultado: seniority resolvido + confidence_score (0-1)
```

**Saídas válidas:** `estagiario | junior | pleno | senior | lead | principal | diretor | vp_clevel`

**Checklist — F4:**
- [ ] Função `resolve_seniority_full(titulo, anos_experiencia, salary, skills)` implementada
- [ ] Retorna seniority + confidence_score
- [ ] 100% determinístico quando confidence_score ≥ 0.8
- [ ] Fallback para `"pleno"` quando sinais conflitantes

---

## 7. Bloco A — F5: Distribuição Adaptativa de Perguntas

> **Arquivo:** `wsi_service.py` → `WSIQuestionGenerator.generate_all()`

### 7.1 Lógica

```python
distribution = SENIORITY_DISTRIBUTIONS[mode][seniority]
n_technical  = distribution["technical"]
n_behavioral = distribution["behavioral"]

# Exemplo: pleno + compact → 5 técnicas + 2 comportamentais = 7 total
# Exemplo: lead + full    → 7 técnicas + 5 comportamentais = 12 total
```

**Regra crítica:** O total de perguntas NUNCA pode exceder:
- `compact`: 7 perguntas
- `full`: 12 perguntas

**Checklist — F5:**
- [ ] `generate_all()` usa `SENIORITY_DISTRIBUTIONS` para definir n_technical e n_behavioral
- [ ] Total nunca excede 7 (compact) ou 12 (full)
- [ ] Distribuição validada para todos os 8 níveis de senioridade × 2 modos = 16 combinações

---

## 8. Bloco A — F6: Geração de Perguntas com Validação

> **Arquivo:** `wsi_service.py` → `WSIQuestionGenerator._generate_cbi_question()`, `_generate_bigfive_question()`, `_generate_with_validation()`

### 8.1 Schema `WSIQuestion`

```python
{
    "id":                 str,   # UUID
    "competency":         str,   # nome da competência
    "framework":          str,   # CBI|Bloom|Dreyfus|BigFive
    "question_type":      str,   # technical|behavioral|situational
    "question_text":      str,   # texto da pergunta
    "weight":             float, # peso na nota final
    "bloom_level":        int,   # 1-6 — nível esperado
    "dreyfus_level":      int,   # 1-5 — proficiência esperada
    "expected_signals":   [str], # sinais STAR esperados
    "scoring_criteria":   {      # rubric por banda
        "1-2": str,
        "3":   str,
        "4-5": str,
    },
    "is_critical":        bool,  # top 2 competências críticas recebem true
    "needs_manual_review": bool, # F6.8: marcado se falhou 3 tentativas
    "validation_flags":   dict,  # F6.8: flags de validação
}
```

### 8.2 F6.5 — Perguntas Técnicas (CBI)

```
Framework: CBI — pede situação real passada
Modelo: Claude Sonnet 4.5
Temperature: 0.7
Max tokens: 800
Input: competência, senioridade, Bloom esperado, Dreyfus esperado, contexto JD
```

**Regra `is_critical`:** As 2 primeiras competências técnicas recebem `is_critical=True` (top 2, não top 3).

### 8.3 F6.6 — Perguntas Comportamentais (Big Five + STAR)

```
Framework: Big Five + CBI + STAR
Modelo: Claude Sonnet 4.5
Temperature: 0.75
Max tokens: 800
Input: competência comportamental, trait OCEAN mapeado, senioridade, contexto JD
```

**Trait-Affinity (F6.6):**
```python
# Para cada trait selecionado em F3:
#   1. Buscar competência com big_five_mapping == trait (do enriched_jd)
#   2. Se match encontrado: usar essa competência
#   3. Fallback: usar primeira comportamental disponível
```

### 8.4 F6.8 — Validação Pós-Geração (Obrigatório)

**Estágio 1 — Determinístico (custo ~0ms):**
```python
def _validate_deterministic(question_text: str) -> list[str]:
    flags = []
    word_count = len(question_text.split())

    # Regra 1: comprimento 15-80 palavras
    if word_count < 15 or word_count > 80:
        flags.append(f"length_out_of_range:{word_count}_words")

    # Regra 2: sem hipotéticos ("imagine que", "como você faria se")
    _HYPOTHETICAL_RE = re.compile(
        r"\b(como você faria se|imagine que|suponha que|caso você tivesse|"
        r"se você fosse|o que você faria|como agiria se)\b", re.IGNORECASE
    )
    if _HYPOTHETICAL_RE.search(question_text):
        flags.append("hypothetical_phrasing")

    # Regra 3: sem marcadores de viés
    _BIAS_MARKERS_RE = re.compile(
        r"\b(homem|mulher|masculino|feminino|casado|solteiro|"
        r"filhos|gravidez|religião|etnia|raça|idade)\b", re.IGNORECASE
    )
    if _BIAS_MARKERS_RE.search(question_text):
        flags.append("bias_marker_detected")

    # Regra 4: deve ter verbo situacional (passado)
    _PAST_VERB_RE = re.compile(
        r"\b(conte|descreva|fale|compartilhe|explique|relate|"
        r"dê um exemplo|recorde|mencione)\b", re.IGNORECASE
    )
    if not _PAST_VERB_RE.search(question_text):
        flags.append("missing_situational_verb")

    return flags
```

**Estágio 2 — LLM JD Anchoring:**
```
Modelo: Claude Sonnet 4.5
Temperature: 0.0   ← OBRIGATÓRIO (determinístico)
Max tokens: 300
Input: pergunta gerada + JD original + skill/trait avaliado
Output: {is_anchored: bool, evidence_in_jd: str, anchor_type: str, confidence: str, suggestion: str}
```

**Loop de Retentativas:**
```
MAX_RETRIES = 3
Para cada tentativa:
    1. Gerar pergunta (LLM)
    2. Validação determinística → se flags: retry
    3. Validação JD anchor → se not is_anchored: retry
    4. Se passou: retornar pergunta válida
    5. Se esgotou retentativas: needs_manual_review = True
```

**Checklist — F6:**
- [ ] Método `_generate_cbi_question()` com CBI framework + STAR hints
- [ ] Método `_generate_bigfive_question()` com trait OCEAN como contexto
- [ ] `is_critical = (i < 2)` para primeiras 2 competências técnicas (não top 3)
- [ ] Método `_validate_deterministic()` com 4 regras (comprimento, hipotéticos, viés, verbo situacional)
- [ ] Método `_validate_jd_anchor()` com LLM temperature=0.0, max_tokens=300
- [ ] Método `_generate_with_validation()` com loop MAX_RETRIES=3
- [ ] Após 3 falhas: `question.needs_manual_review = True`, `question.validation_flags` preenchido
- [ ] `generate_all()` usa `_generate_with_validation()` para TODAS as perguntas

---

## 9. Bloco B — F7: Canais de Triagem (E1, E2, E3)

### Canal E1 — Assíncrono (Email/Link)

- Candidato recebe link único por email
- TTL: 72h (armazenado em Redis: `session:{id}:token`)
- Interface web para responder no próprio ritmo
- Callback webhook ao completar

**Checklist — E1:**
- [ ] Endpoint `POST /wsi/sessions/create-async` gera link + armazena token em Redis com TTL 72h
- [ ] Interface web de resposta funcional
- [ ] Expiração de token: 401 após 72h
- [ ] Webhook de callback ao completar

---

### Canal E2 — Síncrono Web (LangGraph Chat)

- Candidato responde via chat em tempo real
- Orquestrado por `WSIInterviewGraph` (LangGraph state machine)
- Persiste estado no PostgreSQL via `PostgresSaver`

**Checklist — E2:**
- [ ] `WSIInterviewGraph` implementado com todos os nós (ver Seção 15)
- [ ] Estado serializado/deserializado com `_wsi_state_to_dict()` / `_wsi_state_from_dict()`
- [ ] Persistência via `PostgresSaver` do LangGraph
- [ ] Campo `trait_weight` serializado corretamente em `WSIQuestionBlock`

---

### Canal E3 — Voz (OpenMic.ai)

- Candidato é contatado via ligação automática
- `WSIVoiceOrchestrator` gerencia o fluxo
- Callback de transcrição analisado por IA

**Checklist — E3:**
- [ ] `WSIVoiceOrchestrator.start_voice_screening()` implementado
- [ ] Aceita `enriched_jd` opcional para F6.6 trait-affinity
- [ ] Cria agente OpenMic com perguntas geradas
- [ ] Callback `process_call_completed()` processa transcrição
- [ ] Análise IA da transcrição persiste em `voice_screening_analyses`

---

## 10. Bloco B — F8: Scoring Tri-Componente

> **Arquivo:** `wsi_deterministic_scorer.py`

### 10.1 Camada 1 — STAR Determinístico

```python
def calculate_star_score(response_text: str) -> tuple[dict, float]:
    """
    Busca keywords STAR_INDICATORS em texto normalizado.
    Retorna (components, score).
    components = {"S": bool, "T": bool, "A": bool, "R": bool}
    score = weighted sum usando STAR_COMPONENT_WEIGHTS
    """
    text_lower = response_text.lower()
    components = {}
    for component, keywords in STAR_INDICATORS.items():
        components[component] = any(kw in text_lower for kw in keywords)

    score = sum(
        STAR_COMPONENT_WEIGHTS[c] for c, present in components.items() if present
    )
    return components, score  # score ∈ [0.0, 1.0]
```

### 10.2 Camada 2 — LLM Extrator (Bloom/Dreyfus/Sinais)

```
Modelo: Claude Sonnet 4.5
Temperature: 0.0   ← OBRIGATÓRIO
Max tokens: 400
Input: resposta do candidato + competência + framework
Output: {bloom_demonstrated, dreyfus_demonstrated, evidences, star_structure_found, trait_signals_found}

IMPORTANTE: O LLM EXTRAI sinais, não AVALIA. A decisão final é sempre determinística.
```

### 10.3 Camada 3 — Fórmula Tri-Componente

```python
def calculate_wsi_deterministic(
    response_text: str,
    question_type: str,   # "technical" | "behavioral"
    bloom_expected: int,
    dreyfus_expected: int,
    # + resultados das Camadas 1 e 2
) -> DeterministicWSIResult:

    if question_type == "technical":
        # Componente 1: autodeclaração (escala 1-5 declarada pelo candidato)
        autodeclaracao_score = detect_autodeclaration_scale(response_text)  # 1-5

        # Componente 2: evidências técnicas (sinais do LLM extrator)
        evidencias_score = calculate_evidence_quality(evidences, context)   # 1-5

        # Componente 3: alinhamento Bloom
        bloom_score = calculate_bloom_alignment(bloom_expected, bloom_demonstrated)  # 0-1 → ×5

        score_bruto = (
            0.35 × autodeclaracao_score
          + 0.40 × evidencias_score
          + 0.25 × (bloom_score × 5)
        )

    elif question_type == "behavioral":
        # Componente 1: estrutura STAR
        _, star_score = calculate_star_score(response_text)  # 0-1
        star_normalizado = star_score * 5  # escala 1-5

        # Componente 2: sinais de trait Big Five
        sinais_trait_score = calculate_trait_signals(trait_signals_found)  # 1-5

        # Componente 3: alinhamento Bloom
        bloom_score = calculate_bloom_alignment(bloom_expected, bloom_demonstrated)

        score_bruto = (
            0.35 × star_normalizado
          + 0.40 × sinais_trait_score
          + 0.25 × (bloom_score × 5)
        )

    # Aplicar penalidades (Camada 1)
    penalties = detect_penalties(response_text)
    score_final = max(1.0, min(5.0, score_bruto - penalties))

    return DeterministicWSIResult(
        score=score_final,
        autodeclaration_score=autodeclaracao_score,
        bloom_demonstrated=bloom_demonstrated,
        dreyfus_demonstrated=dreyfus_demonstrated,
        star_components=components,
        evidences=evidences,
        red_flags=red_flags,
        formula_version="v2",
    )
```

### 10.4 Penalidades

```python
def detect_penalties(response_text: str, score: float) -> float:
    """Retorna valor a subtrair do score."""
    text_lower = response_text.lower()
    total_penalty = 0.0

    for trigger_name, config in PENALTY_TRIGGERS.items():
        if trigger_name == "no_context":
            if len(response_text.split()) < config["min_words"]:
                total_penalty += config["penalty"]
        else:
            if any(kw in text_lower for kw in config["keywords"]):
                total_penalty += config["penalty"]

    return abs(total_penalty)
```

**Checklist — F8:**
- [ ] `calculate_star_score()` implementado com STAR_INDICATORS e STAR_COMPONENT_WEIGHTS
- [ ] LLM extrator temperature=0.0 (nunca temperatura alta nesta etapa)
- [ ] `calculate_wsi_deterministic()` com fórmula tri-componente separada por tipo
- [ ] Score final limitado ao intervalo [1.0, 5.0]
- [ ] `detect_red_flags()` aplicando PENALTY_TRIGGERS
- [ ] Campo `formula_version = "v2"` presente no resultado
- [ ] Penalidade de inflação: -1.0
- [ ] Penalidade de genérico: -0.5
- [ ] Penalidade de sem contexto (< 20 palavras): -0.3

---

## 11. Bloco B — F9: Composição WSI Final

> **Arquivo:** `wsi_interview_graph.py` → `generate_feedback()` + `wsi_deterministic_scorer.py`

### 11.1 Fórmula F9

```python
# WSI Técnico: média simples das perguntas técnicas
WSI_tecnico = sum(score_i for pergunta técnica_i) / count_tecnicas

# WSI Comportamental: média PONDERADA pelos trait_weights de F3
WSI_comportamental = (
    sum(score_i × trait_weight_i for pergunta comportamental_i)
    / sum(trait_weight_i)
)
# Fallback: se trait_weight não disponível → weight=1.0 (média simples)

# WSI Final: combinação ponderada por senioridade
WSI_final = (
    WSI_tecnico       × SENIORITY_WEIGHTS[seniority]["technical"]
  + WSI_comportamental × SENIORITY_WEIGHTS[seniority]["behavioral"]
)
WSI_final = max(0.0, min(5.0, WSI_final))  # clamp 0-5
```

### 11.2 Escala de Saída

| WSI Final (/5) | Classificação | Decisão base |
|---|---|---|
| ≥ 4.5 | Excepcional | APROVAR |
| 4.0–4.49 | Excelente | APROVAR |
| 3.5–3.99 | Alto | CONSIDERAR |
| 3.0–3.49 | Médio | REVISAR |
| 2.25–2.99 | Abaixo da média | REJEITAR |
| < 2.25 | Regular/Baixo | REJEITAR |

**Checklist — F9:**
- [ ] `WSI_tecnico` calculado como média simples
- [ ] `WSI_comportamental` calculado como média PONDERADA por `trait_weight` (F9-1)
- [ ] Fallback `trait_weight = 1.0` quando F3 não disponível
- [ ] `WSI_final` combina técnico + comportamental com `SENIORITY_WEIGHTS[seniority]`
- [ ] Score limitado a [0.0, 5.0]
- [ ] Persistência em `wsi_results` com `technical_wsi`, `behavioral_wsi`, `overall_wsi`

---

## 12. Bloco B — F10: Gates Absolutos e Decisão

> **Arquivo:** `wsi_deterministic_scorer.py` + `wsi.py` → `_compute_decision_confidence()`

### 12.1 Gates (Precedência Absoluta)

| Gate | Trigger | Consequência |
|------|---------|---|
| **G1** | Pergunta de elegibilidade binárias (pré-qualificação) respondida com "não" | REPROVADO imediato, antes do scoring |
| **G2** | Detecção de prompt injection em qualquer resposta | REPROVADO imediato |
| **G3** | `WSI_final < 2.0` | REPROVADO automático |
| **G4** | Skill com `is_critical=True` com `score < 1.5` | REPROVADO (mesmo com WSI alto) |
| **G5** | Reservado para uso futuro | — |
| **G6** | Respostas inflacionadas detectadas (autodeclara 5 sem evidências) | REPROVADO |

**Regra de ouro:** Um candidato com WSI 4.9 que ative qualquer gate é REPROVADO. Gates têm precedência ABSOLUTA.

### 12.2 Decisão Automática

```python
def compute_decision_result(
    overall_wsi: float,
    failed_gates: list[str],
) -> str:
    if failed_gates:
        return "REPROVADO"

    if overall_wsi >= 3.75:
        return "APROVADO"
    elif overall_wsi >= 3.0:
        return "EM_AVALIACAO"
    else:
        return "REPROVADO"
```

### 12.3 F10-6 — Confiança da Decisão

```python
def _compute_decision_confidence(
    overall_wsi: float,
    failed_gates: list[str],
    llm_fallback_count: int,
    score_variance: float,
) -> tuple[str, bool]:
    """
    Returns: (confidence: str, human_review_required: bool)
    """
    ambiguous_gates = {"G2", "G5", "G6"}
    clear_reject_gates = {"G1", "G3", "G4"}

    # BAIXA: sinal de incerteza alta
    if "G2" in failed_gates or llm_fallback_count >= 2 or score_variance > 2.0:
        return "baixa", True

    # ALTA: aprovação clara
    if overall_wsi >= 4.5 and not failed_gates:
        return "alta", False

    # ALTA: rejeição clara por gate definitivo
    if (failed_gates
        and clear_reject_gates.intersection(failed_gates)
        and not ambiguous_gates.intersection(failed_gates)):
        return "alta", False

    # MEDIA: zona de revisão por score
    if 3.0 <= overall_wsi < 3.75:
        return "media", True

    if 3.75 <= overall_wsi < 4.5 and not failed_gates:
        return "media", False

    # MEDIA: gates ambíguos
    if failed_gates and ambiguous_gates.issuperset(failed_gates):
        return "media", True

    # Default
    return "media", overall_wsi < 3.75
```

**Checklist — F10:**
- [ ] G1: Perguntas binárias eliminatórias verificadas ANTES do scoring
- [ ] G2: Regex/LLM detecção de injection em respostas brutas
- [ ] G3: `WSI_final < 2.0` → REPROVADO (verificado após scoring)
- [ ] G4: `is_critical=True` com `score < 1.5` → REPROVADO
- [ ] G6: Inflação detectada (keywords + score autodeclarado vs. evidências)
- [ ] `_compute_decision_confidence()` implementado com lógica exata acima
- [ ] `decision_confidence` e `human_review_required` persistidos em `wsi_results`
- [ ] Gates ativados listados em `failed_gates` (ex: `["G4"]`)

---

## 13. Bloco B — F11: Relatório e Feedback

> **Arquivo:** `personalized_feedback_service.py` + `wsi.py` → `get_f11_report()`

### 13.1 Estrutura do Relatório F11

```python
{
    "report_id": str,
    "candidate_id": str,
    "job_vacancy_id": str,
    "generated_at": datetime,
    "already_generated": bool,   # F11-3 cache

    "scores": {
        "wsi_final":      float,   # 0-5
        "wsi_technical":  float,
        "wsi_behavioral": float,
        "classification": str,
    },

    "decision": {
        "result":               str,    # APROVADO|EM_AVALIACAO|REPROVADO
        "confidence":           str,    # alta|media|baixa
        "human_review_required": bool,
        "failed_gates":         [str],
    },

    "report_sections": {
        "executive_summary":  str,        # 2-4 frases
        "strengths": [                    # máximo 4 itens
            {"competency": str, "evidence": str, "score": float}
        ],
        "gaps": [                         # máximo 4, ordenados ALTO→MEDIO→BAIXO
            {"competency": str, "gap_level": str, "recommendation": str}
        ],
        "key_evidence": [str],            # máximo 4
        "candidate_feedback": {           # único bloco compartilhável com candidato
            "intro":        str,
            "positivo":     str,          # BLOCO_POSITIVO
            "desenvolvimento": str,       # BLOCO_DESENVOLVIMENTO
            "nivel":        str,          # BLOCO_NIVEL
            "tip":          str,
        },
        "interview_questions": [str],     # F11-5: 3-5 perguntas para entrevista presencial
        "big_five_analysis": {
            "openness":          {"score": int, "gap": str, "evidence": str},
            "conscientiousness": {...},
            "extraversion":      {...},
            "agreeableness":     {...},
            "stability":         {...},
        },
        "dreyfus_comparison": [           # por competência técnica
            {
                "competency":          str,
                "dreyfus_expected":    int,
                "dreyfus_demonstrated": int,
                "gap":                 str,
            }
        ],
    }
}
```

### 13.2 F11-3 — Cache do Relatório

```python
async def get_f11_report(candidate_id, job_vacancy_id, db):
    # 1. Garantir coluna de cache (idempotente)
    await db.execute("""
        ALTER TABLE wsi_results
        ADD COLUMN IF NOT EXISTS f11_report_json JSONB
    """)

    # 2. Verificar cache
    cached = await db.fetchone("""
        SELECT f11_report_json FROM wsi_results
        WHERE candidate_id = $1 AND job_vacancy_id = $2
        AND f11_report_json IS NOT NULL
    """, candidate_id, job_vacancy_id)

    if cached:
        report = F11ReportResponse(**cached["f11_report_json"])
        report.already_generated = True
        return report

    # 3. Gerar relatório (LLM)
    report = await generate_f11_report(...)  # LLM call

    # 4. Salvar no cache
    await db.execute("""
        UPDATE wsi_results SET f11_report_json = $1
        WHERE candidate_id = $2 AND job_vacancy_id = $3
    """, report.model_dump(), candidate_id, job_vacancy_id)

    return report
```

### 13.3 F11-6 — Endpoints de Ranking

```python
# GET /api/v1/wsi/ranking/{job_vacancy_id}
# Response:
{
    "job_vacancy_id": str,
    "total_screened":  int,
    "averages": {
        "technical_avg":   float,
        "behavioral_avg":  float,
        "overall_avg":     float,
    },
    "ranking": [
        {
            "rank":          int,
            "candidate_id":  str,
            "candidate_name": str,
            "technical_wsi":  float,
            "behavioral_wsi": float,
            "overall_wsi":    float,
            "percentile":     int,
            "classification": str,
            "decision_result": str,
        }
    ]
}

# GET /api/v1/wsi/candidate/{candidate_id}/ranking/{job_vacancy_id}
# Response:
{
    "candidate_id":   str,
    "job_vacancy_id": str,
    "rank":           int,
    "total":          int,
    "overall_wsi":    float,
    "percentile":     int,
}
```

### 13.4 Regras do Feedback ao Candidato

**LGPD — Restrição crítica:** O bloco `candidate_feedback` é o ÚNICO bloco compartilhável externamente. Todos os outros (scores, gates, red_flags, scoring_criteria, expected_evidence) são exclusivos do recrutador.

**3 Templates por Decisão:**

| Decisão | Conteúdo principal |
|---------|---|
| APROVADO | Felicitações + pontos fortes + perguntas de aprofundamento para entrevista |
| EM_AVALIACAO | Pontos a esclarecer + próximos passos + prazo |
| REPROVADO | Gates ativados (em linguagem neutra) + sugestões de desenvolvimento + recursos |

```
Modelo: Claude Sonnet 4.5
Temperature: 0.7
Max tokens: 1200
```

**Checklist — F11:**
- [ ] Endpoint `GET /api/v1/wsi/report/{candidate_id}/{job_vacancy_id}` implementado
- [ ] F11-3: `f11_report_json JSONB` como cache — ler no início, salvar no final
- [ ] `already_generated: true` quando relatório vem do cache
- [ ] `report_sections.executive_summary` com 2-4 frases
- [ ] `report_sections.strengths` limitado a 4 itens, apenas scores ≥ 3.5
- [ ] `report_sections.gaps` ordenados ALTO→MEDIO→BAIXO, máximo 4 itens
- [ ] `report_sections.candidate_feedback` sem scores, sem gates, sem ranking
- [ ] F11-5: `interview_questions` com 3-5 sugestões de perguntas para entrevista presencial
- [ ] F11-6: `GET /ranking/{job_vacancy_id}` retorna pool ordenado por overall_wsi DESC
- [ ] F11-6: `GET /candidate/{id}/ranking/{job_vacancy_id}` retorna posição individual
- [ ] Feedback enviável por email/WhatsApp (separação frontend)

---

## 14. Endpoints REST

> **Arquivos:** `app/api/v1/wsi.py` (prefixo `/api/v1/wsi`) + `app/api/wsi_endpoints.py` (prefixo `/api/wsi`)

### 14.1 Tabela Completa de Endpoints

| Método | Path | Função | F. |
|--------|------|---------|---|
| POST | `/api/wsi/analyze-jd` | Analisa qualidade do JD, retorna `enriched_jd` | F1 |
| POST | `/api/v1/wsi/jd-evaluate` | Avaliação rápida de qualidade do JD (score + warnings) | F1.B |
| POST | `/api/wsi/generate-questions` | Gera perguntas (aceita `enriched_jd`) | F6 |
| POST | `/api/v1/wsi/generate-questions` | Variante v1 | F6 |
| POST | `/api/v1/wsi/analyze-response` | Analisa resposta individual | F8 |
| POST | `/api/v1/wsi/calculate-wsi` | Calcula WSI final | F9 |
| GET  | `/api/v1/wsi/report/{candidate_id}/{job_vacancy_id}` | Gera/recupera relatório F11 | F11 |
| POST | `/api/v1/wsi/generate-feedback` | Gera feedback personalizado | F11 |
| GET  | `/api/v1/wsi/ranking/{job_vacancy_id}` | Ranking de candidatos da vaga | F11-6 |
| GET  | `/api/v1/wsi/candidate/{id}/ranking/{job_vacancy_id}` | Posição do candidato no ranking | F11-6 |
| POST | `/api/wsi/voice/start-screening` | Inicia screening de voz (E3) | E3 |
| POST | `/api/wsi/voice/webhook` | Callback OpenMic.ai (E3) | E3 |

### 14.2 Schemas Principais

```python
class GenerateQuestionsRequest(BaseModel):
    session_id:       str
    candidate_id:     str
    job_vacancy_id:   str
    competencies:     List[Dict[str, Any]]
    mode:             str = "compact"       # compact|full
    enriched_jd:      Optional[Dict[str, Any]] = None   # WSI-7 bridge F1→F6

class GenerateQuestionsResponse(BaseModel):
    session_id:       str
    questions:        List[WSIQuestionOut]
    total_questions:  int
    distribution:     Dict[str, int]        # {technical: N, behavioral: M}
    seniority_used:   str
    mode_used:        str

class AnalyzeResponseRequest(BaseModel):
    session_id:      str
    question_id:     str
    candidate_id:    str
    job_vacancy_id:  str
    question_text:   str
    response_text:   str
    response_audio_url: Optional[str] = None
    competency:      str
    framework:       str   # CBI|Bloom|Dreyfus|BigFive

class AnalyzeResponseResponse(BaseModel):
    analysis_id:          str
    final_score:          float   # 1-5
    autodeclaration_score: Optional[float]
    bloom_demonstrated:   Optional[int]
    dreyfus_demonstrated: Optional[int]
    star_components:      Optional[Dict]
    evidences:            List[str]
    red_flags:            List[str]
    justification:        str
    needs_manual_review:  bool

class F11ReportResponse(BaseModel):
    report_id:          str
    candidate_id:       str
    job_vacancy_id:     str
    generated_at:       datetime
    already_generated:  bool = False
    human_review_required: bool = False
    scores:             Dict
    decision:           Dict
    report_sections:    Dict
```

**Checklist — Endpoints:**
- [ ] Todos os 12 endpoints implementados
- [ ] `enriched_jd` aceito em `GenerateQuestionsRequest`
- [ ] Resposta de análise inclui `star_components` e `needs_manual_review`
- [ ] F11 endpoint lê cache antes de gerar
- [ ] Ranking endpoints consultam `wsi_results` ordenado por `overall_wsi DESC`
- [ ] Scores convertidos: se armazenados /5, multiplicar ×2 para exibição /10 (ou manter /5 — escolher escala única)
- [ ] Autenticação: `company_id` validado em todos os endpoints multi-tenant

---

## 15. Pipeline LangGraph (Canal E2)

> **Arquivo:** `wsi_interview_graph.py`

### 15.1 Dataclasses

```python
@dataclass
class WSIQuestionBlock:
    block_id:       str
    block_type:     str       # "technical" | "behavioral" | "situational"
    question:       str
    competency:     str
    bloom_level:    int       # 1-6
    dreyfus_level:  int       # 1-5
    big_five_trait: Optional[str] = None   # F9-1: trait associado
    max_score:      float = 10.0
    trait_weight:   float = 1.0            # F9-1: peso normalizado F3

@dataclass
class WSIResponseRecord:
    question_block:     WSIQuestionBlock
    candidate_response: str
    score:              float    # 0-10
    bloom_achieved:     int      # 1-6
    dreyfus_achieved:   int      # 1-5
    reasoning:          str
    scored_at:          Optional[datetime] = None
```

### 15.2 Estado: `WSIInterviewState`

```python
@dataclass
class WSIInterviewState:
    session_id:              str
    company_id:              str
    candidate_id:            str
    job_id:                  str
    interview_level:         str         # quick|standard|full
    stage:                   WSIInterviewStage
    job_requirements:        Dict        # enriched_jd
    candidate_profile:       Dict        # CV parsed
    question_blocks:         List[WSIQuestionBlock]
    current_question_index:  int = 0
    responses:               List[WSIResponseRecord] = field(default_factory=list)
    technical_score:         float = 0.0
    behavioral_score:        float = 0.0
    technical_score_count:   int = 0
    behavioral_score_count:  int = 0
    wsi_final_score:         Optional[float] = None
    failed_gates:            List[str] = field(default_factory=list)
    execution_log:           List[Dict] = field(default_factory=list)
    awaiting_response:       bool = False
    completed_at:            Optional[datetime] = None
    error_message:           Optional[str] = None
```

### 15.3 Estágios

```python
class WSIInterviewStage(str, Enum):
    INIT             = "init"
    LOAD_CONTEXT     = "load_context"
    GENERATE_QUESTION = "generate_question"
    AWAIT_RESPONSE   = "await_response"
    VALIDATE_RESPONSE = "validate_response"
    SCORE_RESPONSE   = "score_response"
    ADVANCE          = "advance"
    GENERATE_FEEDBACK = "generate_feedback"
    COMPLETE         = "complete"
    ERROR            = "error"
```

### 15.4 Grafo de Transições

```
INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE
                                                 ↓
                              VALIDATE_RESPONSE (inválida → AWAIT_RESPONSE)
                                                 ↓
                                        SCORE_RESPONSE
                                                 ↓
                              ADVANCE (mais perguntas → GENERATE_QUESTION)
                                                 ↓
                                      GENERATE_FEEDBACK
                                                 ↓
                                            COMPLETE
```

### 15.5 Nó `generate_feedback` — F9 + F10

```python
async def generate_feedback(state: WSIInterviewState) -> WSIInterviewState:
    seniority = state.job_requirements.get("senioridade", "pleno")
    weights   = SENIORITY_WEIGHTS.get(seniority, SENIORITY_WEIGHTS["pleno"])

    # Scores técnicos (média simples)
    tech_responses = [r for r in state.responses if r.question_block.block_type == "technical"]
    if tech_responses:
        technical_final = sum(r.score for r in tech_responses) / len(tech_responses)
    else:
        technical_final = state.technical_score  # fallback

    # Scores comportamentais (média ponderada por trait_weight — F9-1)
    behav_responses = [
        r for r in state.responses
        if r.question_block.block_type in ("behavioral", "situational")
    ]
    if behav_responses:
        weighted_sum = sum(r.score × r.question_block.trait_weight for r in behav_responses)
        total_weight = sum(r.question_block.trait_weight for r in behav_responses)
        behavioral_final = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        behavioral_final = state.behavioral_score  # fallback

    # WSI final
    wsi_final = (
        technical_final   × weights["technical"]
      + behavioral_final  × weights["behavioral"]
    )
    state.wsi_final_score = max(0.0, min(10.0, wsi_final))  # E2 usa escala 0-10

    # Verificar gates F10
    # ... (aplicar G1-G6)

    # Gerar feedback F11
    # ... (LLM call temperature=0.7)

    state.stage = WSIInterviewStage.COMPLETE
    return state
```

### 15.6 Serialização PostgresSaver

```python
def _wsi_state_to_dict(state: WSIInterviewState) -> dict:
    return {
        "session_id":  state.session_id,
        "stage":       state.stage.value,
        "question_blocks": [
            {
                "block_id":       b.block_id,
                "block_type":     b.block_type,
                "question":       b.question,
                "competency":     b.competency,
                "bloom_level":    b.bloom_level,
                "dreyfus_level":  b.dreyfus_level,
                "big_five_trait": b.big_five_trait,
                "max_score":      b.max_score,
                "trait_weight":   b.trait_weight,   # F9-1 — OBRIGATÓRIO
            }
            for b in state.question_blocks
        ],
        # ... demais campos
    }

def _wsi_state_from_dict(data: dict) -> WSIInterviewState:
    question_blocks = [
        WSIQuestionBlock(
            **{k: v for k, v in qb.items()},
        )
        for qb in data.get("question_blocks", [])
    ]
    # ... reconstrução completa
```

**Checklist — LangGraph:**
- [ ] `WSIQuestionBlock.trait_weight` implementado (float, default=1.0)
- [ ] `WSIInterviewState` com todos os campos listados
- [ ] Todos os 9 estágios implementados
- [ ] Serialização inclui `trait_weight` (crítico para F9-1)
- [ ] `generate_feedback()` usa média ponderada para comportamental
- [ ] `PostgresSaver` configurado para persistência entre requests
- [ ] LGPD: verificação de consentimento no nó `load_context` (SEG-4)
- [ ] EU AI Act: `response_hash` SHA-256 armazenado em cada resposta

---

## 16. Canal de Voz — OpenMic.ai (E3)

> **Arquivo:** `wsi_voice_orchestrator.py`

### 16.1 Fluxo

```
1. `start_voice_screening()`:
   a. Gera perguntas via wsi_service (F6) com enriched_jd
   b. Cria sessão WSI com screening_type="voice"
   c. Chama API OpenMic.ai para criar agente com as perguntas
   d. Inicia chamada para candidate_phone
   e. Retorna VoiceScreeningResult com session_id + call_id

2. Callback Webhook (OpenMic → LIA):
   POST /api/wsi/voice/webhook
   Body: {call_id, status, transcript, transcript_object}

3. `process_call_completed()`:
   a. Persiste transcript em voice_screening_calls
   b. Análise IA do transcript (Claude Sonnet 4.5, temp=0.1)
   c. Extrai skills mencionados, scores comunicação, red/green flags
   d. Persiste em voice_screening_analyses
   e. Calcula WSI e persiste em wsi_results
```

**Checklist — E3:**
- [ ] `VoiceScreeningRequest` com campos: candidate_id, job_vacancy_id, competencies, candidate_phone, candidate_name, mode, enriched_jd (opcional)
- [ ] Criação de agente OpenMic.ai com perguntas formatadas
- [ ] Webhook receiver implementado
- [ ] `process_call_completed()` com análise IA e cálculo WSI
- [ ] Celery task para processamento assíncrono do callback

---

## 17. Frontend — Modal de Detalhes WSI

> **Arquivo:** `triagem-details-modal.tsx`

### 17.1 Estrutura de Tabs

**Tab 1 — Visão Geral (Resultado WSI)**
- Header: badge de decisão (APROVADO/EM_AVALIACAO/REPROVADO) + badge de confiança
- Cards de scores: WSI Técnico, WSI Comportamental, WSI Final (barras de progresso)
- Seção de gates ativados (se houver)
- Seção de red flags

**Tab 2 — Análise Detalhada**
- Big Five Profile (5 traits com scores)
- Análise STAR por resposta
- Comparativo Dreyfus esperado vs. demonstrado
- Perguntas respondidas com scores individuais

**Tab 3 — Ranking e Comparativo (F11-6)**
- 3 cards: Média Técnica Pool / Média Comportamental Pool / Média Geral Pool
- Tabela de ranking:
  - Coluna: Posição (badge 🥇🥈🥉 para top 3)
  - Coluna: Nome (candidato atual marcado com "(você)")
  - Coluna: WSI Técnico
  - Coluna: WSI Comportamental
  - Coluna: WSI Final
  - Candidato atual: `bg-gray-900 text-white dark:bg-gray-700`
- Fallback: mensagem placeholder quando `total_screened = 0`

### 17.2 Funções Utilitárias

```typescript
const WSI_CLASSIFICATION_COLORS = {
    excepcional:       { bg: 'rgba(5, 150, 105, 0.12)',  text: '#065F46', label: 'Excepcional' },
    excelente:         { bg: 'rgba(34, 197, 94, 0.12)',  text: '#166534', label: 'Excelente' },
    alto:              { bg: 'rgba(59, 130, 246, 0.12)', text: '#1D4ED8', label: 'Alto' },
    medio:             { bg: 'rgba(234, 179, 8, 0.12)',  text: '#854D0E', label: 'Médio' },
    abaixo_da_media:   { bg: 'rgba(249, 115, 22, 0.12)', text: '#9A3412', label: 'Abaixo da média' },
    regular:           { bg: 'rgba(239, 68, 68, 0.12)',  text: '#991B1B', label: 'Regular / Baixo' },
}

const getDecisionDisplay = (decision?: string) => {
    const normalized = (decision ?? '').toUpperCase()
        .replace('NAO_APROVADO', 'REPROVADO')
        .replace('AGUARDANDO', 'EM_AVALIACAO')
    switch (normalized) {
        case 'APROVADO':    return { label: 'Aprovado', color: '#166534', bg: 'rgba(34, 197, 94, 0.12)' }
        case 'EM_AVALIACAO': return { label: 'Em Avaliação', color: '#854D0E', bg: 'rgba(234, 179, 8, 0.12)' }
        case 'REPROVADO':   return { label: 'Não Aprovado', color: '#991B1B', bg: 'rgba(239, 68, 68, 0.12)' }
        default:            return { label: 'Pendente', color: '#6B7280', bg: '#F3F4F6' }
    }
}

const wsiToPercent  = (score: number) => Math.round((score / 5) * 100)
const bloomLabel    = (n: number) => ["","Recordar","Compreender","Aplicar","Analisar","Avaliar","Criar"][n]
const dreyfusLabel  = (n: number) => ["","Iniciante","Básico","Intermediário","Avançado","Especialista"][n]
```

### 17.3 Chamadas API do Modal

```typescript
// Resultado WSI principal
const result = await fetch(`/api/backend-proxy/wsi/report/${candidateId}/${jobVacancyId}`)

// Ranking da vaga (Tab 3)
const ranking = await fetch(`/api/backend-proxy/wsi/ranking/${jobVacancyId}`)

// Posição do candidato
const candidateRank = await fetch(`/api/backend-proxy/wsi/candidate/${candidateId}/ranking/${jobVacancyId}`)
```

**Checklist — Modal:**
- [ ] Tab 1: badges de decisão com cores corretas (emerald/âmbar/vermelho)
- [ ] Tab 1: badge de confiança: "Alta confiança" (emerald) / "Revisão recomendada" (âmbar para media e baixa)
- [ ] Tab 1: barras de progresso WSI técnico, comportamental, final
- [ ] Tab 2: Big Five com 5 traits + labels em português
- [ ] Tab 2: componentes STAR (S/T/A/R) por resposta
- [ ] Tab 2: comparativo Dreyfus com ícone e cor por gap
- [ ] Tab 3: 3 cards de médias do pool
- [ ] Tab 3: tabela com rank badges (🥇🥈🥉), highlight do candidato atual
- [ ] Tab 3: fallback quando sem candidatos
- [ ] Dark mode em todos os elementos
- [ ] Normalização de strings de decisão: `NAO_APROVADO` → `REPROVADO`

---

## 18. Frontend — Painel de Avaliação do JD

> **Arquivo:** `JDEvaluationPanel.tsx`

### 18.1 Lógica de Validação D3/D4

```typescript
// D3 — Skills Técnicas (mínimo: 9)
const evaluateTechSkills = (count: number) => {
    if (count >= 9)  return { status: "sufficient",    points: 30 }
    if (count >= 3)  return { status: "partial",       points: 15 }
    return                  { status: "insufficient",  points: 0  }
}

// D4 — Competências Comportamentais (mínimo: 5)
const evaluateBehavioral = (count: number) => {
    if (count >= 5)  return { status: "sufficient" }
    if (count >= 2)  return { status: "partial"    }
    return                  { status: "insufficient" }
}

// Bloqueio hard
if (jdQualityScore < 30) {
    readyForProcessing = false
    blockingMessage = "JD insuficiente para gerar triagem WSI"
}
```

**Checklist — JDEvaluationPanel:**
- [ ] D3: mínimo 9 skills técnicas (not 3, not 5)
- [ ] D4: mínimo 5 competências comportamentais
- [ ] `ready_for_processing = false` quando score < 30
- [ ] Status visual: sufficient (verde) / partial (âmbar) / insufficient (vermelho)
- [ ] Bloqueio de botão "Gerar Perguntas" quando `ready_for_processing = false`

---

## 19. Testes Automatizados

> **Arquivos:** `tests/unit/test_wsi*.py`

### 19.1 Suíte 1 — F8 Fórmula Tri-Componente (`test_wsi1_scoring_engine.py`)

| Teste | Critério de aceite |
|-------|---|
| Versão da fórmula | `result.formula_version == "v2"` |
| Pesos técnicos declarados | autodeclaracao=0.35, evidencias=0.40, bloom=0.25 |
| Pesos comportamentais declarados | star=0.35, sinais_trait=0.40, bloom=0.25 |
| Score limitado [1, 5] | `1.0 ≤ final_score ≤ 5.0` |
| Pesos STAR somam 1.0 | S+T+A+R = 1.0 |
| Resposta completa STAR | Todos S/T/A/R presentes → star_score = 1.0 |
| Resposta vazia STAR | "não sei" → star_score ≈ 0 |

### 19.2 Suíte 2 — F1 JD Quality (`test_wsi2_jd_quality.py`)

| Teste | Critério de aceite |
|-------|---|
| D3: 9 skills = sufficient | status="sufficient", score_increment=30 |
| D3: 3-8 skills = partial | status="partial", aviso gerado |
| D3: <3 skills = insufficient | status="insufficient" |
| D3: mínimo é 9 | `minimum == 9` |
| D4: 5 comportamentais = sufficient | OK |
| D4: 2-4 = partial | aviso |
| D4: <2 = insufficient | bloqueio soft |
| Compact total = 7 | `len(questions) == 7` |
| Distribuição por senioridade | junior: 5+2, lead: 3+4 |

### 19.3 Suíte 3 — Gates G2/G4/G6 (`test_wsi3_gates.py`)

| Teste | Critério de aceite |
|-------|---|
| G2: 1 injection reprova | "ignore all previous instructions" → G2 ativo |
| G2: sem injection passa | Respostas normais → G2 não ativo |
| G2: "jailbreak" detectado | G2 ativo |
| G4: skill crítica falha (<1.5) | is_critical=True + score=1.0 → G4 ativo |
| G4: skill crítica passa (≥1.5) | is_critical=True + score=2.0 → G4 não ativo |
| G4: skill não-crítica falha | is_critical=False → G4 não ativo |
| G6: keywords inflação ativam | ["expert", "especialista"] → G6 ativo |

### 19.4 Suíte 4 — Feedback F8.5.1 (`test_wsi4_feedback.py`)

| Teste | Critério de aceite |
|-------|---|
| Template tem BLOCO_POSITIVO | Campo presente no output |
| Template tem BLOCO_DESENVOLVIMENTO | Campo presente |
| Template tem BLOCO_NIVEL | Campo presente |
| Path APROVADO | Contém "felicitações" ou equivalente |
| Path EM_AVALIACAO | Contém "próximos passos" |
| Path REPROVADO com gates | Lista gates + sugestões |

### 19.5 Suíte 6 — Big Five Pipeline (`test_wsi6_bigfive_pipeline.py`)

| Teste | Critério de aceite |
|-------|---|
| F2.5: retorna 5 traits | Exatamente um por dimensão OCEAN |
| F2.5: score 0-100 | `0 ≤ score ≤ 100` |
| F2.5: tem evidências | `len(evidence) > 0` |
| F2.5: confidence válido | `confidence ∈ {high, medium, low}` |
| F3: top-N por senioridade | pleno → 3 traits, lead → 4 traits |
| F3: pesos normalizados = 1.0 | `sum(weights) ≈ 1.0` |
| F6.6: trait-affinity match | enriched_jd.big_five_mapping usado |
| F6.6: fallback sem match | Primeira comportamental disponível |

**Checklist — Testes:**
- [ ] Suíte 1 (`test_wsi1`): todas as asserções passando
- [ ] Suíte 2 (`test_wsi2`): D3=9, D4=5, compact=7, full=12
- [ ] Suíte 3 (`test_wsi3`): G2/G4/G6 todos passando
- [ ] Suíte 4 (`test_wsi4`): 3 blocos + 3 decision paths
- [ ] Suíte 6 (`test_wsi6`): F2.5→F3→F6.6 pipeline completo
- [ ] Coverage mínima: ≥ 30% (gate de CI)
- [ ] Testes de integração: pelo menos 1 fluxo E2E por canal (E1, E2, E3)

---

## 20. Compliance e Segurança

### 20.1 LGPD

- [ ] Consentimento do candidato verificado antes de iniciar triagem (SEG-4)
- [ ] `candidate_feedback` é o ÚNICO bloco compartilhável com o candidato
- [ ] Dados de triagem não exportáveis sem anonimização
- [ ] Direito ao esquecimento: endpoint de deleção de dados WSI por candidato
- [ ] Granular consent: candidato pode recusar canal de voz

### 20.2 EU AI Act / Auditoria

- [ ] `response_hash` SHA-256 armazenado para cada resposta bruta
- [ ] `execution_log` completo em `WSIInterviewState` (cada nó do grafo)
- [ ] `audit_trail`: quem gerou perguntas, quando, com qual versão do modelo
- [ ] `questions_hash` SHA-256 no `screening_question_sets`
- [ ] FairnessGuard: validação de feedback antes de envio (`fairness_guard.py`)

### 20.3 Multi-Tenant

- [ ] `company_id` presente em TODAS as tabelas WSI
- [ ] Queries filtradas por `company_id` em todos os endpoints
- [ ] Dados de uma empresa nunca visíveis para outra

### 20.4 Detecção de Viés (FairnessGuard)

- [ ] Bias markers no texto de perguntas bloqueiam envio (F6.8)
- [ ] Feedback ao candidato validado pelo FairnessGuard antes de envio
- [ ] Four-Fifths Rule aplicada em relatórios de ranking por vaga

---

## 21. Itens Futuros (não implementar agora)

Estes itens estão documentados mas NÃO devem ser implementados no escopo desta reprodução:

| Item | Descrição | Motivo do adiamento |
|------|-----------|---|
| **F2.1** | Extração OCEAN por análise léxica (LIWC) | Menor precisão que LLM (F2.5) |
| **F2.2** | Prior O\*NET por cargo | Requer F3 fórmula completa |
| **F3 Completo** | Combinar F2.5 (40%) + F2.2 (35%) + boost_senioridade (25%) | Depende de F2.2 |
| **F5 Boost** | Ajuste de pesos de traits por senioridade | Depende de F3 completo |
| **G5** | Gate reservado | A definir |
| **E1 Tests** | Testes unitários Canal Async | Escopo pós-lançamento |
| **Análise de Tom** | Análise de cadência/sotaque em voz (E3) | Requer capacidade ML adicional |

---

## 22. Checklist Final de Entrega

Use este checklist como critério de aceite para o ambiente completo estar pronto.

### Banco de Dados
- [ ] `wsi_results` com todos os campos + `f11_report_json JSONB`
- [ ] `wsi_sessions` com TTL para E1
- [ ] `screening_question_sets` com `questions_hash` e versionamento
- [ ] `wsi_responses` com `response_hash` e `trait_weight`
- [ ] `voice_screening_calls` + `voice_screening_analyses`
- [ ] `company_screening_questions`
- [ ] Todos os índices criados

### Constantes
- [ ] `SENIORITY_DISTRIBUTIONS`: compact=7, full=12 — validado
- [ ] `SENIORITY_WEIGHTS`: técnico+comportamental=1.0 — validado
- [ ] `SENIORITY_BIGFIVE_TOP_N`: 8 níveis definidos
- [ ] `STAR_COMPONENT_WEIGHTS`: soma=1.0 — validado
- [ ] `WSI_FORMULA_WEIGHTS_*`: soma=1.0 — validado
- [ ] `PENALTY_TRIGGERS`: inflação=-1.0, genérico=-0.5, curto=-0.3

### Bloco A (por vaga)
- [ ] F1: `analyze_jd_quality()` com enriched_jd estruturado
- [ ] F1.B: D3≥9 e D4≥5, bloqueio hard <30 pontos
- [ ] F2.5: extração OCEAN 5 traits (score 0-100, confidence, evidence)
- [ ] F3: ranking top-N + pesos normalizados
- [ ] F4: `resolve_seniority_full()` com 5 sinais
- [ ] F5: distribuição adaptativa por senioridade × modo
- [ ] F6.5: perguntas técnicas CBI (is_critical top 2)
- [ ] F6.6: perguntas comportamentais Big Five + trait-affinity
- [ ] F6.8: validação pós-geração (determinística + LLM anchor, 3 retentativas)

### Bloco B (por candidato)
- [ ] F7/E1: canal assíncrono com link TTL 72h
- [ ] F7/E2: LangGraph state machine com 9 estágios
- [ ] F7/E3: OpenMic.ai + webhook + análise transcript
- [ ] F8: scoring tri-componente (STAR + extrator LLM + fórmula)
- [ ] F9: composição WSI final com ponderação por senioridade e trait_weight
- [ ] F10: 6 gates com precedência absoluta
- [ ] F10-6: `_compute_decision_confidence()` com lógica completa
- [ ] F11: relatório estruturado + cache f11_report_json
- [ ] F11-3: `already_generated` retornado quando cache disponível
- [ ] F11-5: `interview_questions` com 3-5 sugestões
- [ ] F11-6: endpoints de ranking por vaga e por candidato

### Endpoints REST
- [ ] 12 endpoints implementados e documentados
- [ ] Autenticação multi-tenant em todos
- [ ] `enriched_jd` aceito em geração de perguntas

### Frontend
- [ ] Modal Tab 1: badges decisão + confiança + scores
- [ ] Modal Tab 2: Big Five + STAR + Dreyfus
- [ ] Modal Tab 3: ranking com pool averages + tabela + highlight
- [ ] JDEvaluationPanel: D3/D4 validation + bloqueio hard
- [ ] Dark mode em todos os componentes
- [ ] Normalização de strings de decisão

### Testes
- [ ] 5 suítes de testes passando (test_wsi1 a test_wsi6)
- [ ] Coverage ≥ 30%

### Compliance
- [ ] LGPD: consentimento + separação feedback candidato
- [ ] EU AI Act: hashes SHA-256 + audit trail
- [ ] Multi-tenant: company_id em tudo
- [ ] FairnessGuard: validação de feedback

---

> **Documento gerado em:** 25/03/2026
> **Fonte:** `docs/WSI_FLOW_PONTA_A_PONTA.md` + `docs/WSI_METHODOLOGY_COMPLETE_v2.md` + código validado
> **Próxima revisão:** Após implementação de F2.2 + F3 completo (sem data definida)
