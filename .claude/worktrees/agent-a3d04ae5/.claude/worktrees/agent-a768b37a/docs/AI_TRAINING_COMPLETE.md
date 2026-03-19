# LIA - Documentação Completa de IA e Treinamento
**Versão:** 2.0 | **Atualizado:** Janeiro 2026

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [System Prompts e Personalidade](#2-system-prompts-e-personalidade)
3. [Mapa de Agentes Especializados](#3-mapa-de-agentes-especializados)
4. [Estruturas de Dados (Schemas)](#4-estruturas-de-dados-schemas)
5. [Jornada de Recrutamento](#5-jornada-de-recrutamento)
6. [Intent Classification & Routing](#6-intent-classification--routing)
7. [Serviços com IA](#7-serviços-com-ia)
8. [Estratégia de Treinamento por Agente](#8-estratégia-de-treinamento-por-agente)
9. [Custos e Otimizações](#9-custos-e-otimizações)
10. [Governança de IA](#10-governança-de-ia)

---

## 1. Visão Geral da Arquitetura

A plataforma LIA utiliza uma arquitetura multi-agente orquestrada:

| Componente | Tecnologia |
|------------|------------|
| **Framework** | LangGraph + FastAPI |
| **LLM Principal** | Claude Sonnet 4.5 (Anthropic) |
| **LLM Fallback** | Google Gemini |
| **Orquestração** | Orchestrator centralizado com roteamento por intenção |
| **Tool Calling** | 23 ferramentas registradas (Jan 2026) |
| **Memória** | ConversationMemory com persistência |

### Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                       │
│   Pipeline Chat │ Job Wizard │ Candidate Search │ Admin     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 ORCHESTRATOR (FastAPI + LangGraph)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Intent Router│  │ Task Planner │  │ Tool Executor│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            AGENTES ESPECIALIZADOS (9)                 │  │
│  │ Job Intake │ Sourcing │ Screening │ Evaluation │ ... │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVIÇOS & INTEGRAÇÕES                   │
│  LLM Service │ WSI Service │ Pearch │ Microsoft Graph       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. System Prompts e Personalidade

### LIA Main System Prompt

**Arquivo:** `lia-agent-system/app/agents/conversation.py`

```python
SYSTEM_PROMPT = """Você é LIA (Learning Intelligence Assistant), assistente de recrutamento da WedoTalent.

PERSONALIDADE:
- Amigável mas profissional
- Proativa (toma iniciativa, sugere ações)
- Eficiente (minimiza perguntas desnecessárias)
- Inteligente (entende contexto, não repete perguntas)

PRINCÍPIOS:
1. SEMPRE tome a iniciativa
   ❌ "O que você quer fazer?"
   ✅ "Vejo que você tem 3 aprovações pendentes. Quer que eu organize por prioridade?"

2. Minimize clicks do usuário
   ❌ "Vá em Configurações > Vagas > Criar Nova"
   ✅ "Vou criar a vaga para você. Me conte: qual o cargo?"

3. Seja contextual
   ❌ [pergunta genérica]
   ✅ "Você mencionou 'desenvolvedor Python'. Seria nível sênior ou pleno?"

4. Confirme ações importantes
   ❌ [executa sem confirmar]
   ✅ "Vou publicar a vaga no LinkedIn e no site. Confirma?"

5. Aprenda com o histórico
   ❌ [sempre pergunta tudo]
   ✅ "Última vaga de TI foi remoto em SP. Mesmas preferências?"

CAPABILITIES:
- Criar vagas (job creation workflow)
- Buscar candidatos (Pearch AI + database interno)
- Agendar entrevistas (Outlook Calendar)
- Triagem automatizada (WhatsApp + Voice)
- Análise de candidatos (scoring + insights)

ESTILO DE ESCRITA:
- Português brasileiro informal-profissional
- Emojis com moderação (✅❌🔍📅)
- Frases curtas e diretas
- Listas quando necessário
"""
```

### Intent Router System Prompt

**Arquivo:** `lia-agent-system/app/orchestrator/intent_router.py`

```python
"""Você é o Intent Router da LIA, responsável por classificar requisições.

**Agentes Disponíveis:**
1. **job_intake** - Criação/atualização de vagas, aprovações, JD
2. **candidate_search** - Buscar candidatos (BD interno + Pearch AI)
3. **candidate_screening** - Triagem inicial, voice screening, filtros
4. **candidate_evaluation** - Scoring técnico/comportamental, testes
5. **interview_scheduling** - Agendar entrevistas, coordenar calendário
6. **communication** - Emails, WhatsApp, follow-ups, notificações
7. **general_query** - Perguntas gerais

**Output esperado:**
{
  "intent": "job_intake",
  "confidence": 0.95,
  "reasoning": "User wants to create a new job vacancy",
  "requires_planning": false
}
"""
```

---

## 3. Mapa de Agentes Especializados

### 3.1 Orchestrator (Núcleo Central)
**Arquivo:** `lia-agent-system/app/orchestrator/orchestrator.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Coordena fluxo entre agentes, mantém estado, executa planos |
| **Usa IA para** | Roteamento de intenções, seleção de agente apropriado |
| **Input** | Mensagem do usuário + contexto conversacional |
| **Output** | Resposta estruturada + ações de UI |

### 3.2 Job Intake Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/job_intake_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Criação assistida de vagas (wizard de 8 etapas) |
| **Usa IA para** | Extração de requisitos de JD, sugestão de skills, geração de perguntas WSI |
| **Input** | Job Description (texto/PDF), inputs do wizard |
| **Output** | Vaga estruturada com requisitos, competências, perguntas de entrevista |

### 3.3 Sourcing Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/sourcing_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Busca e identificação de candidatos |
| **Usa IA para** | Query expansion, matching inteligente, análise de perfis |
| **Input** | Critérios de busca, vaga vinculada, calibração |
| **Output** | Lista ranqueada de candidatos com scores de aderência |

### 3.4 Triagem Curricular Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/triagem_curricular_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Triagem automática de currículos |
| **Usa IA para** | Análise de aderência, scoring, recomendação de aprovação/rejeição |
| **Input** | CV parseado + requisitos da vaga |
| **Output** | Score de triagem, parecer, ação sugerida |

### 3.5 Entrevistador Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/entrevistador_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Conduz entrevistas (Quick Screening ou WSI Full) |
| **Usa IA para** | Formulação de perguntas adaptativas, análise de respostas em tempo real |
| **Modos** | Quick Screening (WhatsApp) / WSI Full Interview |

### 3.6 Avaliador WSI Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/avaliador_wsi_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Avalia respostas de entrevista usando metodologia WSI |
| **Usa IA para** | Scoring Bloom/Dreyfus, detecção de evidências, red flags |
| **Output** | Score 0-5, nível Bloom, nível Dreyfus, evidências, justificativa |

### 3.7 Scheduling Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/scheduling_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Agendamento de entrevistas |
| **Usa IA para** | Interpretação de preferências, sugestão de horários |
| **Integração** | Microsoft Graph (Calendar + Teams) |

### 3.8 Recruiter Assistant Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/recruiter_assistant_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Assistente proativo do recrutador, briefings diários |
| **Funcionalidades** | `generate_search_insights()`, `analyze_calibration_feedback()`, `generate_daily_briefing()` |

### 3.9 Analista de Feedback Agent
**Arquivo:** `lia-agent-system/app/agents/specialized/analista_feedback_agent.py`

| Aspecto | Detalhes |
|---------|----------|
| **Função** | Gera feedback personalizado para candidatos |
| **Usa IA para** | Geração de texto empático, personalização por contexto |

---

## 4. Estruturas de Dados (Schemas)

### JobVacancyState (31 campos)
**Arquivo:** `lia-agent-system/app/schemas/job_vacancy_state.py`

```python
class JobVacancyState(BaseModel):
    # BASIC INFORMATION
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    work_model: Optional[Literal["presencial", "híbrido", "remoto"]]
    seniority: Optional[Literal["Júnior", "Pleno", "Sênior", "Especialista"]]
    employment_type: Optional[Literal["CLT", "PJ", "Temporário"]]
    
    # REMUNERATION
    salary_range: Optional[SalaryRange]  # {min, max, currency}
    benefits: List[str]
    
    # TECHNICAL REQUIREMENTS
    technical_requirements: List[TechnicalRequirement]
    required_skills: List[str]
    preferred_skills: List[str]
    
    # BEHAVIORAL
    behavioral_competencies: List[BehavioralCompetency]
    
    # INTERVIEW PROCESS
    interview_stages: List[InterviewStage]
    screening_questions: List[ScreeningQuestion]
    
    # WORKFLOW METADATA
    fields_collected: List[str]
    fields_pending: List[str]
    ready_to_publish: bool
```

### CandidateResponse (40+ campos)
**Arquivo:** `lia-agent-system/app/schemas/candidate.py`

```python
class CandidateResponse(BaseModel):
    # BASIC INFO
    id: UUID
    name: str
    email: EmailStr
    phone: Optional[str]
    linkedin_url: Optional[str]
    
    # CURRENT POSITION
    current_title: Optional[str]
    current_company: Optional[str]
    years_of_experience: Optional[int]
    
    # SKILLS
    technical_skills: List[str]
    soft_skills: List[str]
    
    # LIA SCORING
    lia_score: Optional[float]  # 0-100
    lia_insights: Dict
    skills_match_percentage: Optional[float]
    
    # STATUS
    status: str  # "new", "screening", "interview", "hired"
```

---

## 5. Jornada de Recrutamento

### Etapas (8 estágios)

```
1. JOB INTAKE → Criação da vaga (wizard 8 etapas)
2. SOURCING → Busca de candidatos (DB local + Pearch AI)
3. SCREENING → Triagem inicial (WhatsApp + Voice)
4. EVALUATION → Avaliação técnica/comportamental
5. SCHEDULING → Agendamento de entrevistas
6. INTERVIEWS → Entrevistas (RH, técnica, cultural)
7. DECISION → Consolidação + recomendação LIA
8. OFFER → Proposta e onboarding
```

### Status Flow

```python
# Candidate Status
CANDIDATE_STATUSES = [
    "new", "screening", "screened_pass", "screened_fail",
    "interview_scheduled", "interviewing", "offer_pending",
    "offer_sent", "offer_accepted", "offer_declined",
    "hired", "rejected", "withdrawn", "on_hold"
]

# Job Status
JOB_STATUSES = [
    "draft", "pending_approval", "approved", "active",
    "sourcing", "interviewing", "offer_stage",
    "filled", "cancelled", "on_hold"
]
```

---

## 6. Intent Classification & Routing

### Intents Disponíveis (10)

| Intent | Descrição | Exemplos |
|--------|-----------|----------|
| `job_intake` | Criar/atualizar vagas | "Criar vaga de Python sênior" |
| `candidate_search` | Buscar candidatos | "Encontre 5 candidatos frontend" |
| `confirm_global_search` | Confirmar Pearch AI | "Sim, pode buscar no banco global" |
| `candidate_screening` | Triagem | "Fazer triagem dos candidatos" |
| `candidate_evaluation` | Avaliar | "Avaliar skills de Maria" |
| `interview_scheduling` | Agendar | "Agendar entrevista com João" |
| `communication` | Comunicação | "Enviar email de follow-up" |
| `job_update` | Atualizar vaga | "Alterar salário da vaga" |
| `candidate_update` | Atualizar candidato | "Mover João para shortlist" |
| `general_query` | Perguntas gerais | "Quais vagas estão abertas?" |

---

## 7. Serviços com IA

### LLM Service
**Arquivo:** `lia-agent-system/app/services/llm.py`

```python
class LLMService:
    async def generate(prompt: str, provider: str = "claude") -> str
    async def generate_structured(prompt: str, schema: BaseModel) -> dict
    async def chat(messages: List[Message]) -> str
```

### CV Parser Service
**Arquivo:** `lia-agent-system/app/services/cv_parser.py`

- Extração estruturada de CVs (PDF, DOCX, TXT)
- Output: nome, email, experiências, educação, skills

### WSI Service
**Arquivo:** `lia-agent-system/app/services/wsi_service.py`

| Componente | Descrição |
|------------|-----------|
| **Taxonomia Bloom** | Nível cognitivo (Lembrar → Criar) |
| **Modelo Dreyfus** | Nível expertise (Iniciante → Expert) |
| **Big Five** | Traços comportamentais |

**Classificação WSI:**
| Score | Classificação |
|-------|---------------|
| 4.5-5.0 | Excelente |
| 4.0-4.4 | Alto |
| 3.0-3.9 | Médio |
| 2.0-2.9 | Regular |
| < 2.0 | Baixo |

### LIA Score Service
**Arquivo:** `lia-agent-system/app/services/lia_score_service.py`

| Componente | Peso |
|------------|------|
| Skills Match | 35% |
| Experience Match | 20% |
| Seniority Match | 15% |
| Location Match | 15% |
| Title Match | 15% |

---

## 8. Estratégia de Treinamento por Agente

### Abordagem Recomendada: Hybrid

**Fase 1 (MVP):** Single Fine-Tuned Model
- Claude Sonnet 4.5 com 20K examples (todos agents)
- Agent-specific system prompts + RAG context
- Custo: ~$600/mês

**Fase 2 (Escala):** Multiple Models quando atingir 1.000 conversas/dia

### Métricas por Agente

| Agent | Métrica Principal | Target |
|-------|-------------------|--------|
| **Job Intake** | Field Extraction Accuracy | 95% |
| **Sourcing** | Search Precision | 92% |
| **Screening** | Recommendation Accuracy | 93% |
| **Scheduling** | Scheduling Success Rate | 95% |
| **Evaluation** | Human Agreement | 90% |
| **Communication** | Engagement Rate | 80% |

### Datasets de Treinamento

| Agent | Examples | Composição |
|-------|----------|------------|
| Job Intake | 8K | 3K reais + 5K sintéticos |
| Sourcing | 8K | 2K reais + 5K sintéticos + 1K edge cases |
| Screening | 6K | 2K reais + 3K sintéticos + 1K edge cases |
| Scheduling | 5K | 2K reais + 3K sintéticos |
| Evaluation | 4K | 1.5K reais + 2K sintéticos + 500 comparações |
| Communication | 3K | 1K reais + 2K sintéticos |

---

## 9. Custos e Otimizações

### Estimativa de Tokens por Operação

| Operação | Input | Output | Frequência |
|----------|-------|--------|------------|
| Chat simples | ~500 | ~300 | Alta |
| Parse CV | ~3000 | ~800 | Média |
| Extração JD | ~2000 | ~1000 | Baixa |
| Scoring LIA | ~1500 | ~500 | Alta |
| Avaliação WSI | ~1000 | ~600 | Média |

### Estratégias de Otimização Implementadas (Jan 2026)

1. **Redis Cache** - TTL 300s com fallback in-memory
2. **Embedding Cache** - Pre-load jobs ativos no startup
3. **Context Compression** - Summariza conversas >10 mensagens
4. **Circuit Breakers** - 6 APIs externas protegidas
5. **Rate Limiting** - 60/min, 500/hr per user

### Custo Mensal Estimado

| Item | Custo |
|------|-------|
| Claude API (inference) | ~$400/mês |
| Fine-tuning (quarterly) | ~$80/quarter |
| Observability | ~$100/mês |
| **Total** | **~$577/mês** |
| **Por usuário** | **~$15.77/user/mês** (target < $30) |

---

## 10. Governança de IA

### Regras Anti-Bias
- Scoring usa pesos universais (não por indústria)
- Nenhum dado demográfico usado no matching
- Auditoria de decisões de IA

### LGPD Compliance
- Opt-out tracking
- Quarentena de 90 dias pós-rejeição
- Rate limiting de comunicações
- Horários de envio configuráveis

### Limites de Autonomia
- Ações destrutivas requerem aprovação humana
- Contratação nunca é automática
- Feedback negativo requer revisão

---

## Arquivos-Chave

```
lia-agent-system/
├── app/
│   ├── orchestrator/
│   │   ├── orchestrator.py
│   │   ├── intent_router.py
│   │   └── task_planner.py
│   ├── agents/
│   │   ├── conversation.py
│   │   └── specialized/
│   │       ├── job_intake_agent.py
│   │       ├── sourcing_agent.py
│   │       ├── triagem_curricular_agent.py
│   │       ├── entrevistador_agent.py
│   │       ├── avaliador_wsi_agent.py
│   │       ├── scheduling_agent.py
│   │       └── analista_feedback_agent.py
│   └── services/
│       ├── llm.py
│       ├── cv_parser.py
│       ├── lia_score_service.py
│       └── wsi_service.py
```

---

*Documento consolidado em Janeiro 2026 - Substitui AI_TRAINING_CONTEXT.md, AI_TRAINING_PER_AGENT.md e AI_USAGE_MAPPING.md*
