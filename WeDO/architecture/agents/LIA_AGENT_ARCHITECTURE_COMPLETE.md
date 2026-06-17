# Arquitetura Completa dos Agentes LIA

**Data:** Janeiro 2026  
**Versão:** 3.0  
**Status:** Documento de Referência para Replicação  
**Stack:** LangGraph + LangChain + Claude Sonnet + FastAPI + Redis + RabbitMQ

> **Documentos Relacionados:**
> - [NLP Clustering Strategic Analysis](./NLP_CLUSTERING_STRATEGIC_ANALYSIS.md) - Análise de aplicação de Sentence Transformers + UMAP + HDBSCAN para matching semântico e Talent Map
> - [Job Wizard Enhancement Plan](./proposals/job-wizard-enhancement-plan.md) - Plano detalhado do Wizard v3.0

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Detalhamento dos Agentes](#2-detalhamento-dos-agentes)
3. [Fluxo de Delegação entre Agentes](#3-fluxo-de-delegação-entre-agentes)
4. [Pontos de Interação do Recrutador](#4-pontos-de-interação-do-recrutador)
5. [Módulo de Robustez](#5-módulo-de-robustez)
6. [Compliance, Governança e Auditoria](#6-compliance-governança-e-auditoria)
7. [Pontos de Melhoria e Riscos](#7-pontos-de-melhoria-e-riscos)
8. [Especificação para Replicação](#8-especificação-para-replicação-langgraph)
9. [Checklist de Replicação](#9-checklist-de-replicação)
10. [Camada de Serviços Inteligentes](#10-camada-de-serviços-inteligentes)
11. [Fluxo de Inscrição via WhatsApp](#11-fluxo-de-inscrição-de-candidato-via-link-público--whatsapp)
12. [Changelog](#changelog)

---

## 1. Visão Geral da Arquitetura

### 1.1 Diagrama de Arquitetura Multi-Agente

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                 │
│                              🧠 WEDO TALENT - ARQUITETURA MULTI-AGENTE LIA v3.0                                 │
│                                    (1 Orquestrador + 9 Agentes Especializados)                                  │
│                                                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                     AG.0: ORCHESTRATOR                                                   │   │
│   │                           (Roteamento, Memória, Delegação, Fallback)                                    │   │
│   │                                                                                                         │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │  Intent Classifier  │  Agent Registry  │  Context Manager  │  Fallback Chains  │  Telemetry    │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                                             │
│                                                    ▼                                                             │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                                        ENHANCED AGENT REGISTRY                                            │  │
│   │                          (Roteamento por Confiança + Fallback + Telemetria)                              │  │
│   └───────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                    │                                                             │
│        ┌───────────────┬───────────────┬──────────┴────────┬───────────────┬───────────────┬─────────────────┐   │
│        ▼               ▼               ▼                   ▼               ▼               ▼                 │   │
│   ┌─────────┐    ┌─────────┐    ┌─────────────┐     ┌─────────────┐  ┌─────────┐    ┌─────────────────┐       │   │
│   │  AG.1   │    │  AG.2   │    │    AG.3     │     │    AG.4     │  │  AG.5   │    │      AG.6       │       │   │
│   │  Job    │    │Sourcing │    │   Triagem   │     │Entrevistador│  │Avaliador│    │   Scheduling    │       │   │
│   │ Planner │    │         │    │  Curricular │     │ (WhatsApp/  │  │   WSI   │    │                 │       │   │
│   │  v3.0   │    │         │    │             │     │    Voz)     │  │         │    │                 │       │   │
│   └─────────┘    └─────────┘    └─────────────┘     └─────────────┘  └─────────┘    └─────────────────┘       │   │
│        │               │               │                   │               │               │                 │   │
│        └───────────────┴───────────────┴───────────────────┴───────────────┴───────────────┘                 │   │
│                                                    │                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                      ROBUSTNESS MODULE                                                   │   │
│   │  Intent Schemas │ Error Handling │ Input Validation │ Context Management │ Defensive Prompts            │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                 │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐                                │
│   │       AG.7          │    │       AG.8          │    │   Recruiter         │                                │
│   │  Analyst & Feedback │    │  ATS Integrator     │    │   Assistant         │                                │
│   │  (Comunicação +     │    │  (Gupy, Pandapé,    │    │   (Assistente       │                                │
│   │   Analytics)        │    │   Merge.dev)        │    │    Pessoal)         │                                │
│   └─────────────────────┘    └─────────────────────┘    └─────────────────────┘                                │
│                                                                                                                 │
│   ═══════════════════════════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                  🆕 INTELLIGENT SERVICES LAYER (v3.0)                                    │   │
│   │                                                                                                         │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │   │
│   │   │ Intelligence  │  │  Recruiter    │  │  Confidence   │  │    Skills     │  │  Feedback     │         │   │
│   │   │    Layer      │  │Personalization│  │    Policy     │  │   Catalog     │  │  Learning     │         │   │
│   │   │   Service     │  │   Service     │  │   Service     │  │   Service     │  │   Service     │         │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘         │   │
│   │                                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                         SERVICES LAYER                                                   │   │
│   │                                                                                                         │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │   │
│   │   │ WSI Determin. │  │ Rubric Eval   │  │ Pipeline Stage│  │   Audit       │  │ Communication │         │   │
│   │   │   Scorer      │  │   Service     │  │   Service     │  │   Service     │  │   Service     │         │   │
│   │   │ (100% determi-│  │               │  │               │  │ (LGPD Logs)   │  │ (WhatsApp,    │         │   │
│   │   │  nístico)     │  │               │  │               │  │               │  │  Email)       │         │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘         │   │
│   │                                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                       INFRASTRUCTURE                                                     │   │
│   │                                                                                                         │   │
│   │   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐  │   │
│   │   │ PostgreSQL│  │   Redis   │  │ RabbitMQ  │  │ LangSmith │  │  Claude   │  │        Gemini         │  │   │
│   │   │           │  │  (Cache)  │  │  (Queue)  │  │ (Traces)  │  │(Anthropic)│  │       (Fallback)      │  │   │
│   │   └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────────────────┘  │   │
│   │                                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento dos Agentes

### 2.1 AG.0: Orchestrator (Orquestrador Central)

**Localização:** `app/agents/agent_registry.py`, `app/agents/robustness/enhanced_registry.py`

**Responsabilidades:**
- Roteamento de intenções para agentes especializados
- Gerenciamento de memória e contexto de conversação
- Delegação de tarefas entre agentes
- Fallback chains quando agente primário falha
- Telemetria de roteamento

**Mecanismo de Roteamento:**
```python
1. Intent Classifier detecta intenção do usuário
2. Agent Registry consulta intent_mapping
3. Se mapeamento existe → retorna agente com 95% confiança
4. Se não → consulta todos agentes por confidence scoring
5. Seleciona agente com maior confiança (> threshold)
6. Se nenhum atinge threshold → usa fallback chain
```

**Fallback Chains:**
```python
FALLBACK_CHAINS = {
    "job_planner": ["analyst_feedback", "recruiter_assistant"],
    "sourcing": ["cv_screening", "recruiter_assistant"],
    "cv_screening": ["wsi_evaluator", "analyst_feedback"],
    "interviewer": ["wsi_evaluator", "analyst_feedback"],
    "wsi_evaluator": ["analyst_feedback", "recruiter_assistant"],
    "scheduling": ["analyst_feedback", "recruiter_assistant"],
    "analyst_feedback": ["recruiter_assistant"],
    "ats_integrator": ["analyst_feedback", "recruiter_assistant"],
}
```

---

### 2.2 AG.1: Job Planner (Planejador de Vaga) - 🆕 v3.0

**Localização:** `app/agents/specialized/job_intake_agent.py`

**Responsabilidades:**
- Criação de vagas via conversação (Wizard Inteligente)
- Extração de requisitos de job descriptions
- Geração de perguntas WSI
- Monitoramento de saúde da vaga
- Sugestão de mudanças estratégicas
- Integração com dados da empresa (benefícios, tech stack, cultura)
- 🆕 **Integração com Intelligence Layer** para sugestões data-driven
- 🆕 **Personalização por Recrutador** com thresholds adaptativos
- 🆕 **Gerenciamento de JobDraft** (estado intermediário antes de publicação)

**Intents Mapeados:**
| Intent | Descrição |
|--------|-----------|
| `create_job_vacancy` | Criar nova vaga |
| `create_job` | Criar nova vaga |
| `update_job` | Atualizar vaga existente |
| `close_job` | Fechar/pausar vaga |
| `clone_job` | Duplicar vaga |
| `define_job_profile` | Definir perfil do cargo |
| `generate_wsi_questions` | Gerar perguntas WSI |
| `extract_job_description` | Extrair requisitos de JD |

**Stages do Wizard:**
```
1. criteria_detection    → Critérios Detectados
2. basic_info           → Informações Básicas
3. technical_requirements → Requisitos Técnicos
4. behavioral_competencies → Competências Comportamentais
5. salary_benefits       → Salário e Benefícios
6. screening_questions   → Perguntas de Triagem WSI
7. pipeline_config       → Configuração do Pipeline
8. review_publish        → Resumo da Vaga
```

#### 2.2.1 🆕 Integração com Serviços Inteligentes (v3.0)

O Job Planner agora integra três serviços inteligentes que enriquecem a experiência:

```python
# Fluxo de processamento no job_intake_agent.py

async def process_message(self, message: str, context: Dict) -> AgentResponse:
    # 1. Extração via LLM
    extracted_data = await self._extract_criteria(message)
    
    # 2. 🆕 Enriquecimento com Intelligence Layer
    if self.intelligence_layer:
        extracted_data = await self._enrich_with_intelligence(
            extracted_data,
            company_id=context["company_id"],
            recruiter_id=context["recruiter_id"]
        )
    
    # 3. 🆕 Aplicar personalização do recrutador
    if self.personalization_service:
        thresholds = await self.personalization_service.get_personalized_thresholds(
            recruiter_id=context["recruiter_id"]
        )
        extracted_data["_field_thresholds"] = thresholds.field_overrides
    
    # 4. 🆕 Calcular confiança determinística
    confidence_map = await self.confidence_policy.calculate_all_confidences(
        extracted_data,
        sources={"text_extraction": extracted_data, "company_defaults": context.get("company_defaults")}
    )
    
    # 5. 🆕 Criar/atualizar JobDraft
    draft = await self._create_or_update_draft(extracted_data, confidence_map)
    
    return AgentResponse(
        message=self._generate_response(draft),
        data={"draft": draft, "confidence_map": confidence_map}
    )
```

#### 2.2.2 🆕 Tipologia de Campos (FieldTypology)

Cada campo do wizard é classificado em uma tipologia que define seu comportamento:

```python
class FieldTypology(str, Enum):
    IMPLICIT = "implicit"       # Inferidos silenciosamente (currency, country)
    PROBABLE = "probable"       # Auto-preenchidos via defaults
    CONDITIONAL = "conditional" # Ativados por gatilhos (hybrid_days se work_model=hybrid)
    CRITICAL = "critical"       # Obrigatórios (job_title, seniority)
    OPERATIONAL = "operational" # Uso interno (created_by, timestamps)
    DERIVED = "derived"         # Calculados automaticamente (job_complexity)
```

**Mapeamento de Campos:**
| Campo | Tipologia | Comportamento |
|-------|-----------|---------------|
| `job_title` | CRITICAL | Sempre perguntar se não informado |
| `seniority` | CRITICAL | Inferir + confirmar se confiança < 80% |
| `department` | PROBABLE | Usar default se disponível |
| `location` | PROBABLE | Usar default da empresa |
| `work_model` | PROBABLE | Usar default da empresa |
| `hybrid_days` | CONDITIONAL | Só mostra se work_model = hybrid |
| `salary_min/max` | CRITICAL | Sugerir benchmark + confirmar |
| `currency` | IMPLICIT | Sempre BRL, nunca perguntar |
| `skills` | PROBABLE | Inferir + permitir edição |
| `screening_questions` | DERIVED | Gerar baseado em WSI |

#### 2.2.3 🆕 JobDraft - Estado Intermediário

**Localização:** `app/models/job_draft.py`

O JobDraft rastreia o estado da vaga antes da publicação:

```python
class JobDraftStatus(str, Enum):
    DRAFT = "draft"           # Rascunho inicial
    STRUCTURED = "structured" # Campos estruturados
    REVIEWED = "reviewed"     # Revisado pelo recrutador
    CONFIRMED = "confirmed"   # Confirmado para publicação
    PUBLISHED = "published"   # Publicado (JobVacancy criada)
    CANCELLED = "cancelled"   # Cancelado

class JobDraft(Base):
    __tablename__ = "job_drafts"
    
    id = Column(UUID, primary_key=True)
    company_id = Column(UUID, nullable=False)
    recruiter_id = Column(String, nullable=False)
    status = Column(Enum(JobDraftStatus), default=JobDraftStatus.DRAFT)
    current_step = Column(Integer, default=1)
    
    # Campos da vaga
    job_title = Column(String(200))
    department = Column(String(100))
    seniority = Column(String(50))
    # ... outros campos
    
    # 🆕 Rastreamento de origem
    inferred_fields = Column(JSON, default={})
    # {"seniority": {"value": "Senior", "confidence": 0.85, "source": "text_analysis"}}
    
    confirmed_fields = Column(JSON, default={})
    # {"seniority": {"value": "Senior", "confirmed_at": "2026-01-24T10:00:00"}}
    
    company_defaults_used = Column(JSON, default={})
    
    # 🆕 Mapa de confiança
    confidence_map = Column(JSON, default={})
    # {"job_title": 0.95, "seniority": 0.85, "salary_min": 0.65}
    
    # Referência à vaga publicada
    published_job_id = Column(UUID, nullable=True)
```

**Histórico de Mudanças:**
```python
class DraftFieldHistory(Base):
    __tablename__ = "draft_field_history"
    
    draft_id = Column(UUID, ForeignKey("job_drafts.id"))
    field_name = Column(String(100))
    old_value = Column(JSON)
    new_value = Column(JSON)
    change_type = Column(String(50))  # "inferred", "confirmed", "edited", "reverted"
    confidence_at_change = Column(Float)
```

---

### 2.3 AG.2: Sourcing (Busca e Atração)

**Localização:** `app/agents/specialized/sourcing_agent.py`

**Responsabilidades:**
- Busca de candidatos na base interna
- Busca global (Pearch AI, Apify/LinkedIn)
- Geração de Boolean strings para busca
- Enriquecimento de perfis
- Sugestões proativas de candidatos
- Outreach via WhatsApp

**Intents Mapeados:**
| Intent | Descrição |
|--------|-----------|
| `search_candidates` | Buscar candidatos |
| `add_candidate` | Adicionar candidato à vaga |
| `confirm_global_search` | Confirmar busca global |
| `enrich_profile` | Enriquecer perfil do candidato |
| `suggest_candidates` | Sugestões proativas |
| `generate_boolean_string` | Gerar string de busca |
| `outreach_whatsapp` | Outreach via WhatsApp |
| `pearch_search` | Busca no Pearch AI |

**Quando Atua:**
- Após criação/publicação de vaga
- Quando recrutador solicita candidatos
- Proativamente ao detectar vaga com poucos candidatos

**Impacto da v3.0:**
- AG.1 (Job Planner) agora dispara o Sourcing Agent automaticamente após publicação
- Sourcing Agent recebe dados enriquecidos do JobDraft incluindo skills inferidas

---

### 2.4 AG.3: Triagem Curricular (CV Screening)

**Localização:** `app/agents/specialized/triagem_curricular_agent.py`

**Responsabilidades:**
- Parsing de CVs (PDF, DOCX)
- Triagem automática contra requisitos da vaga
- Cálculo de score inicial WSI (70% técnico, 30% comportamental)
- Ranking de candidatos
- Cutoff dinâmico (top 25% após 30-50 triagens)
- Saturação inteligente (pausa se >20 aprovados)
- Detecção de red flags

**Red Flags Detectados:**
- **Gaps de Emprego:** >6 meses sem trabalho
- **Job Hopping:** <1 ano em cada posição
- **Inconsistências:** Datas sobrepostas
- **Falta de Progressão:** Carreira estagnada
- **Informações Vagas:** Sem resultados mensuráveis

**Severidades:**
- `critical`: Elimina candidato
- `high`: Requer investigação imediata
- `medium`: Questionar na entrevista
- `low`: Observação apenas

---

### 2.5 AG.4: Entrevistador (WhatsApp/Voz WSI)

**Localização:** `app/agents/specialized/entrevistador_agent.py`

**Responsabilidades:**
- Condução de entrevistas via WhatsApp
- Voice screening (integração OpenMic/Deepgram)
- Aplicação de perguntas WSI
- Análise de respostas em tempo real
- Transcrição de áudio
- Completude de entrevistas

**Fluxo de Entrevista:**
```
1. LIA envia pergunta via WhatsApp/Voz
2. Candidato responde (texto/áudio)
3. Transcrição automática (se áudio)
4. Análise de resposta em tempo real
5. Próxima pergunta (adaptativa)
6. Ao final → encaminha para AG.5 (Avaliador WSI)
```

---

### 2.6 AG.5: Avaliador WSI (WSI Evaluator)

**Localização:** `app/agents/specialized/avaliador_wsi_agent.py`

**Responsabilidades:**
- Cálculo final de score WSI (100% DETERMINÍSTICO)
- Classificação Bloom Taxonomy (Lembrar → Criar)
- Classificação Dreyfus Model (Novato → Especialista)
- Mapeamento Big Five
- Validação CBI (Competency-Based Interview)
- Ranking e comparação de candidatos
- Cutoff dinâmico com aprendizado
- Calibration loop (aprende do feedback do recrutador)
- Geração de parecer/relatório

**IMPORTANTE - Score Determinístico:**
```python
# O CÁLCULO É 100% DETERMINÍSTICO - NÃO USA LLM!
# Localização: app/services/wsi_deterministic_scorer.py

WSI_FORMULA_WEIGHTS = {
    "autodeclaracao": 0.60,  # O que candidato declara saber
    "contexto": 0.40         # Evidências do contexto
}

# Fórmula:
Score = (0.6 × Autodec) + (0.4 × Context) - Penalty + Bonus

# Score Final Técnico/Comportamental:
WSI_final = (0.7 × Tech) + (0.3 × Behavioral)

# Cutoffs:
≥4.2: Auto-aprovado
3.8-4.1: Revisão manual
3.0-3.7: Aguardando comparação
<3.0: Rejeitado
```

**Bloom Taxonomy (6 níveis):**
| Nível | Nome | Descrição |
|-------|------|-----------|
| 1 | Lembrar | Recordar fatos e conceitos básicos |
| 2 | Compreender | Explicar ideias ou conceitos |
| 3 | Aplicar | Usar conhecimento na prática |
| 4 | Analisar | Fazer conexões entre ideias |
| 5 | Avaliar | Justificar decisões |
| 6 | Criar | Produzir trabalho original |

**Dreyfus Model (5 estágios):**
| Estágio | Nome | Anos | Descrição |
|---------|------|------|-----------|
| 1 | Novato | 0-1 | Segue regras rígidas |
| 2 | Iniciante Avançado | 1-2 | Reconhece aspectos situacionais |
| 3 | Competente | 2-3 | Planeja e prioriza |
| 4 | Proficiente | 3-5 | Visão holística |
| 5 | Especialista | 5+ | Intuição transcende análise |

---

### 2.7 AG.6: Scheduling (Agendamento)

**Localização:** `app/agents/specialized/scheduling_agent.py`

**Responsabilidades:**
- Agendamento de entrevistas
- Integração com calendários (Google, Outlook/Microsoft Graph)
- Disponibilidade de entrevistadores
- Confirmações automáticas
- Reagendamentos
- Reminders

---

### 2.8 AG.7: Analyst & Feedback (Analista)

**Localização:** `app/agents/specialized/analista_feedback_agent.py`

**Responsabilidades:**
- Geração de relatórios e KPIs
- Análise de funil de recrutamento
- Comunicação bulk
- Gerenciamento de templates
- Envio de feedback para candidatos
- Relatórios para gestores

---

### 2.9 AG.8: ATS Integrator

**Localização:** `app/agents/specialized/integrador_ats_agent.py`

**Responsabilidades:**
- Sincronização de candidatos com ATS externos
- Sincronização de vagas
- Atualização de status
- Envio de parecer para ATS
- Importação de candidatos
- Verificação de duplicatas
- Configuração de integrações
- Anonimização LGPD
- Visualização de audit log

**ATS Suportados:**
- Gupy (Brasil)
- Pandapé (Brasil)
- Merge.dev (180+ ATS/HRIS)

---

### 2.10 Recruiter Assistant (Assistente Pessoal)

**Localização:** `app/agents/specialized/recruiter_assistant_agent.py`

**Responsabilidades:**
- Briefing diário
- Verificação de tarefas pendentes
- Planejamento do dia
- Perguntas rápidas
- Chitchat
- Perguntas gerais
- Fallback para intents não mapeados

---

## 3. Fluxo de Delegação entre Agentes

### 3.1 Fluxo Principal de Recrutamento

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      FLUXO PRINCIPAL DE RECRUTAMENTO                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│   │    AG.1     │     │    AG.2     │     │    AG.3     │     │    AG.4     │     │    AG.5     │              │
│   │ Job Planner │────▶│  Sourcing   │────▶│  Triagem    │────▶│Entrevistador│────▶│  Avaliador  │              │
│   │    v3.0     │     │             │     │  Curricular │     │             │     │    WSI      │              │
│   └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘              │
│         │                   │                   │                   │                   │                       │
│         │                   │                   │                   │                   │                       │
│         ▼                   ▼                   ▼                   ▼                   ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    🆕 INTELLIGENT SERVICES LAYER (v3.0)                                                  │   │
│   │                                                                                                         │   │
│   │   ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐ │   │
│   │   │  Intelligence Layer  │  Recruiter Personalization  │  Confidence Policy  │  Feedback Learning   │ │   │
│   │   └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │   │
│   │                                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                                             │
│                                                    ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                          GATES DE APROVAÇÃO                                              │   │
│   │                                                                                                         │   │
│   │   ┌───────────────┐                    ┌───────────────┐                    ┌───────────────┐           │   │
│   │   │   GATE 1      │                    │   GATE 2      │                    │   GATE 3      │           │   │
│   │   │  Aprovar      │                    │  Aprovar      │                    │  Decisão      │           │   │
│   │   │  Mapeados     │                    │  Triados      │                    │  Final        │           │   │
│   │   │ (Recrutador)  │                    │ (Recrutador)  │                    │ (Recrutador)  │           │   │
│   │   └───────────────┘                    └───────────────┘                    └───────────────┘           │   │
│   │                                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                                             │
│                                                    ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                          PASSO FINAL                                                     │   │
│   │                                                                                                         │   │
│   │   ┌───────────────┐              ┌───────────────┐              ┌───────────────┐                       │   │
│   │   │     AG.6      │              │     AG.7      │              │     AG.8      │                       │   │
│   │   │  Scheduling   │◀────────────▶│   Analyst &   │◀────────────▶│     ATS       │                       │   │
│   │   │  (Agendar     │              │   Feedback    │              │  Integrator   │                       │   │
│   │   │   Entrevista) │              │  (Relatórios) │              │  (Sync ATS)   │                       │   │
│   │   └───────────────┘              └───────────────┘              └───────────────┘                       │   │
│   │                                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Delegação de Tarefas

Os agentes podem delegar tarefas uns aos outros via `AgentTask`:

```python
@dataclass
class AgentTask:
    id: str
    title: str
    description: str
    created_by_agent: AgentType      # Quem criou
    assigned_to_agent: AgentType     # Para quem delegou
    priority: TaskPriority
    status: TaskStatus
    due_date: Optional[datetime]
    context: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime]
```

**Exemplos de Delegação:**
- AG.1 → AG.2: "Buscar candidatos para nova vaga publicada" (automático após publicação)
- AG.3 (Triagem) → AG.5 (Avaliador): "Calcular score WSI detalhado"
- AG.4 (Entrevistador) → AG.5 (Avaliador): "Avaliar respostas da entrevista"
- AG.5 (Avaliador) → AG.7 (Analyst): "Gerar parecer para candidato"
- AG.1 (Job Planner) → AG.7 (Analyst): "Sugerir melhorias na vaga"

---

## 10. Camada de Serviços Inteligentes 🆕

A versão 3.0 introduz uma nova camada de serviços inteligentes que potencializam os agentes.

### 10.1 Intelligence Layer Service

**Localização:** `app/services/intelligence_layer_service.py`

**Responsabilidades:**
- Detecção de padrões em correções e comportamentos
- Correlação de outcomes (time-to-fill, qualidade de contratação)
- Ajuste dinâmico de confiança
- Sugestões data-driven para o wizard

**Componentes:**

```python
class IntelligenceLayerService:
    """
    Camada de inteligência centralizada que alimenta todos os agentes.
    """
    
    async def detect_patterns(
        self,
        company_id: str,
        pattern_type: str,  # "correction", "success", "timing"
        context: Optional[Dict] = None
    ) -> List[DetectedPattern]:
        """
        Detecta padrões em correções, comportamentos e outcomes.
        """
        pass
    
    async def analyze_correlations(
        self,
        company_id: str,
        outcome_metric: str = "time_to_fill"
    ) -> CorrelationAnalysis:
        """
        Correlaciona características de vagas com resultados.
        """
        pass
    
    async def get_adjusted_threshold(
        self,
        company_id: str,
        recruiter_id: str,
        field: str
    ) -> Dict[str, float]:
        """
        Retorna thresholds ajustados para este recrutador/campo.
        """
        pass
```

**Modelos de Dados:**
| Modelo | Tabela | Propósito |
|--------|--------|-----------|
| `IntelligenceInsight` | `intelligence_insights` | Log de insights gerados |
| `PatternCache` | `pattern_caches` | Cache de padrões calculados |
| `SuccessProfile` | `success_profiles` | Perfil de sucesso por tipo de vaga |
| `OutcomeCorrelation` | `outcome_correlations` | Correlações características-outcomes |

**API Endpoints:**
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/intelligence/data-quality` | GET | Avalia qualidade de dados |
| `/api/v1/intelligence/context` | POST | Contexto de inteligência para campo |
| `/api/v1/intelligence/adjust-field` | POST | Ajusta sugestão de campo |
| `/api/v1/intelligence/wizard-enhancements` | GET | Melhorias do wizard |
| `/api/v1/intelligence/success-profile` | GET | Perfil de sucesso |
| `/api/v1/intelligence/correlations` | GET | Correlações de outcomes |

**Requisitos de Dados:**
| Requisito | Volume Mínimo | Propósito |
|-----------|---------------|-----------|
| Total de vagas | 50+ | Detecção de padrões |
| Outcomes registrados | 30+ | Análise de correlações |
| Meses de dados | 3+ | Insights temporais |

---

### 10.2 Recruiter Personalization Service

**Localização:** `app/services/recruiter_personalization_service.py`

**Responsabilidades:**
- Personalização da experiência do wizard por recrutador
- Ajuste de thresholds baseado em histórico
- Detecção de preferências e padrões de correção
- Adaptação do fluxo (quick/detailed)

**Modelo RecruiterProfile:**
```python
class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"
    
    recruiter_id = Column(String(255), nullable=False, unique=True)
    company_id = Column(String(255), nullable=False)
    
    # Estatísticas de uso
    total_jobs_created = Column(Integer, default=0)
    total_corrections_made = Column(Integer, default=0)
    avg_completion_time_seconds = Column(Float, nullable=True)
    
    # Preferências detectadas
    preferred_seniorities = Column(JSON, default=list)
    preferred_departments = Column(JSON, default=list)
    correction_patterns = Column(JSON, default=dict)
    
    # Ajustes personalizados
    confidence_threshold_adjustment = Column(Float, default=0.0)
    wizard_mode = Column(String(50))  # "quick", "detailed", "standard"
    experience_level = Column(String(50))  # "beginner", "intermediate", "expert"
```

**API Endpoints:**
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/recruiter-profiles/me` | GET | Perfil do recrutador atual |
| `/api/v1/recruiter-profiles/me/settings` | GET | Configurações de personalização |
| `/api/v1/recruiter-profiles/me/field-preferences` | GET | Preferências por campo |
| `/api/v1/recruiter-profiles/me/thresholds` | GET | Thresholds personalizados |
| `/api/v1/recruiter-profiles/me/events` | POST | Registrar evento |
| `/api/v1/recruiter-profiles/me/recalculate` | POST | Forçar recálculo |

**Casos de Uso:**

| Perfil | Comportamento Adaptado |
|--------|------------------------|
| Recrutador Tech (frequente) | Fluxo rápido, salário ajustado +15%, sem explicações longas |
| Recrutador Novo | Modo explicativo completo, thresholds padrão |
| Recrutador Executivo | Tom formal, detalhista, confirma competências |

---

### 10.3 Confidence Policy Service

**Localização:** `app/services/confidence_policy_service.py`

**Responsabilidades:**
- Cálculo determinístico de confiança por campo
- Determinação de ação baseada em nível de confiança
- Aplicação de thresholds personalizados

```python
class ConfidenceAction(str, Enum):
    APPLY_SILENT = "apply_silent"      # Aplica sem avisar (≥85%)
    APPLY_NOTIFY = "apply_notify"      # Aplica e mostra badge (70-84%)
    ASK_USER = "ask_user"              # Pergunta ao usuário (50-69%)
    ALERT_CONFLICT = "alert_conflict"  # Alerta de conflito (<50%)

class ConfidencePolicyService:
    def calculate_field_confidence(
        self,
        field: str,
        value: Any,
        sources: Dict[str, Any]
    ) -> float:
        """
        Calcula confiança de forma DETERMINÍSTICA (não usa LLM).
        
        Sources:
        - text_extraction: valor extraído do texto
        - company_default: valor default da empresa
        - benchmark: valor de benchmark de mercado
        - similar_jobs: valor de vagas similares
        - correction_history: histórico de correções
        """
        pass
```

---

### 10.4 Skills Catalog Service

**Localização:** `app/services/skills_catalog_service.py`

**Responsabilidades:**
- Catálogo de skills por área (Tech, Finance, HR, Marketing, Sales)
- Sugestão automática de skills por cargo
- Competências comportamentais por senioridade

```python
SKILLS_BY_AREA = {
    "technology": {
        "backend": ["Python", "Java", "Node.js", "Go", "Rust"],
        "frontend": ["React", "Vue.js", "Angular", "TypeScript"],
        "data": ["SQL", "Python", "Spark", "Airflow", "dbt"],
        "devops": ["Docker", "Kubernetes", "AWS", "GCP", "Terraform"],
    },
    "finance": {
        "contabilidade": ["SAP", "Excel Avançado", "Power BI", "IFRS"],
        "financeiro": ["Modelagem Financeira", "Valuation", "M&A"],
    },
    "hr": {
        "recrutamento": ["ATS", "Sourcing", "Employer Branding"],
        "dp": ["Folha de Pagamento", "eSocial", "Legislação Trabalhista"],
    },
    # ...
}
```

---

### 10.5 Feedback Learning Service

**Localização:** `app/services/feedback_learning_service.py`

**Responsabilidades:**
- Registro de feedbacks do wizard (correções, aceitações, skips)
- Registro de outcomes de vagas (contratação, cancelamento)
- Alimenta Intelligence Layer e Personalization

**Modelos:**
```python
class WizardFeedback(Base):
    __tablename__ = "wizard_feedbacks"
    
    user_id = Column(String(255), nullable=False)
    job_id = Column(UUID, nullable=True)
    company_id = Column(String(255), nullable=False)
    
    feedback_type = Column(String(50))  # "correction", "acceptance", "skip"
    field_name = Column(String(100))
    
    original_value = Column(JSON)
    final_value = Column(JSON)
    
    response_time_ms = Column(Integer)
    confidence_at_suggestion = Column(Float)

class JobOutcome(Base):
    __tablename__ = "job_outcomes"
    
    job_id = Column(UUID, nullable=False, unique=True)
    company_id = Column(String(255), nullable=False)
    
    outcome_type = Column(String(50))  # "filled", "cancelled", "expired"
    
    time_to_fill_days = Column(Integer)
    candidates_received = Column(Integer)
    candidates_qualified = Column(Integer)
    
    hire_quality_score = Column(Float)  # 1-5
    recruiter_satisfaction = Column(Float)  # 1-5
```

---

### 10.6 Diagrama de Interação entre Serviços

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           INTERAÇÃO ENTRE SERVIÇOS v3.0                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│   │                              JOB INTAKE AGENT (AG.1)                               │ │
│   └───────────────────────────────────────────────────────────────────────────────────┘ │
│            │                    │                    │                    │              │
│            ▼                    ▼                    ▼                    ▼              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│   │  Intelligence   │  │   Recruiter     │  │   Confidence    │  │     Skills      │   │
│   │     Layer       │  │ Personalization │  │     Policy      │  │    Catalog      │   │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│            │                    │                    │                    │              │
│            │                    │                    │                    │              │
│            └────────────────────┼────────────────────┼────────────────────┘              │
│                                 │                    │                                   │
│                                 ▼                    ▼                                   │
│                        ┌─────────────────────────────────────┐                          │
│                        │        FEEDBACK LEARNING            │                          │
│                        │  (WizardFeedback + JobOutcome)      │                          │
│                        └─────────────────────────────────────┘                          │
│                                         │                                                │
│                                         ▼                                                │
│                        ┌─────────────────────────────────────┐                          │
│                        │         DATABASE (PostgreSQL)        │                          │
│                        │                                      │                          │
│                        │  job_drafts, recruiter_profiles,    │                          │
│                        │  intelligence_insights,              │                          │
│                        │  wizard_feedbacks, job_outcomes      │                          │
│                        └─────────────────────────────────────┘                          │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Pontos de Interação do Recrutador

### 4.1 Chat LIA (Interface Principal)

O recrutador interage com LIA via chat. O Orchestrator detecta a intenção e roteia para o agente correto. Cada agente retorna sugestões clicáveis e próximas ações.

### 4.2 Kanban/Pipeline View

Interações disponíveis na view de pipeline:

| Ação | Agente Acionado | Descrição |
|------|-----------------|-----------|
| Arrastar candidato | AG.3/AG.5 | Move estágio, recalcula scores |
| Aprovar/Rejeitar | AG.5 + Audit | Registra decisão com auditoria |
| Ver parecer | AG.5 | Exibe parecer WSI |
| Agendar entrevista | AG.6 | Abre modal de agendamento |
| Enviar feedback | AG.7 | Prepara template de feedback |

### 4.3 Gates de Aprovação

```
GATE 1: Aprovar Mapeados
├── Candidatos sourcing → Aprovados para triagem
├── Recrutador avalia fit inicial
└── AG.3 assume para triagem curricular

GATE 2: Aprovar Triados  
├── Candidatos triados → Aprovados para entrevista WSI
├── Recrutador valida scores e red flags
└── AG.4 assume para entrevista

GATE 3: Decisão Final
├── Candidatos entrevistados → Contratação
├── Recrutador decide com base no parecer
└── AG.8 sincroniza com ATS
```

---

## 5. Módulo de Robustez

### 5.1 Componentes do Módulo

**Localização:** `app/agents/robustness/`

| Arquivo | Função |
|---------|--------|
| `intent_schemas.py` | Schemas de entidades por intent |
| `error_handling.py` | Tratamento padronizado de erros |
| `input_validation.py` | Validação com Pydantic |
| `context_management.py` | Gerenciamento de contexto |
| `defensive_prompts.py` | Prompts defensivos |
| `enhanced_base.py` | Base agent melhorada |
| `enhanced_registry.py` | Registry com fallback/telemetria |

### 5.2 Error Handling

```python
class AgentErrorCode(str, Enum):
    MISSING_ENTITY = "missing_entity"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
```

### 5.3 Context Management

```python
class CancellationHandler:
    """Detecta quando usuário quer cancelar/recomeçar."""
    
CANCELLATION_KEYWORDS = ["cancelar", "parar", "desistir", "encerrar"]
RESTART_KEYWORDS = ["recomeçar", "começar de novo", "reiniciar"]
CONFIRMATION_KEYWORDS = ["sim", "confirmo", "ok", "pode", "aceito"]
```

---

## 6. Compliance, Governança e Auditoria

### 6.1 Arquitetura de Compliance - 3 Pilares

| Pilar | Componentes | Status |
|-------|-------------|--------|
| **LGPD** | DPO Registry, Breach Notification, Consent Management, Data Subject Requests, Anonymization | Implementado |
| **SOC 2/ISO** | Vanta/Drata Integration, Access Controls, Audit Trails, Encryption, Backup/Recovery | A integrar |
| **AI Governance** | Warden AI (Bias Audit), EU AI Act Compliance, Explainability, Human Review Workflow, Calibration Loop | Parcial |

### 6.2 Serviço de Auditoria

**Localização:** `app/services/audit_service.py`

```python
RETENTION_PERIODS = {
    "score_candidate": 730,      # 2 anos
    "approve_candidate": 730,    # 2 anos
    "reject_candidate": 730,     # 2 anos
    "move_stage": 730,           # 2 anos
    "send_message": 1825,        # 5 anos
    "schedule_interview": 365,   # 1 ano
    "generate_feedback": 730,    # 2 anos
}
```

**Critérios Protegidos (Anti-Bias):**
```python
PROTECTED_CRITERIA = [
    "age", "gender", "ethnicity", "marital_status", "photo",
    "institution", "address", "religion", "disability", "cv_gaps"
]
```

### 6.3 LGPD Compliance

**Endpoints:** `app/api/v1/lgpd_compliance.py`

- `/lgpd/stats` - Estatísticas de compliance
- `/lgpd/dpo` - Registry do DPO
- `/lgpd/breaches` - Notificações de vazamento (48h)
- `/lgpd/decisions` - Explicações de decisões automatizadas (Art. 20)

---

## 7. Pontos de Melhoria e Riscos

### 7.1 Pontos de Melhoria

| Área | Situação Atual | Melhoria Proposta | Prioridade |
|------|----------------|-------------------|------------|
| Observabilidade | Logs básicos | LangSmith traces completos | Alta |
| Fallback LLM | Gemini como fallback | Implementar circuit breaker | Alta |
| Cache | Sem cache central | Redis para respostas frequentes | Média |
| Rate Limiting | Básico por IP | Rate limiting por agente/tenant | Média |
| Métricas de Agente | Limitadas | Dashboard de performance por agente | Média |

### 7.2 Riscos Identificados

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| LLM Indisponível | Alto | Fallback Gemini + Cache |
| Score Inconsistente | Alto | 100% determinístico (não usa LLM) |
| Bias em Triagem | Alto | Protected criteria + Warden AI |
| Vazamento de Dados | Crítico | Encryption + LGPD compliance |
| Token Expiration | Médio | Refresh automático + retry |

### 7.3 Gaps de Compliance

| Requisito | Status |
|-----------|--------|
| LGPD Artigo 20 | Implementado |
| DPO Registry | Implementado |
| Breach Notification 48h | Implementado |
| Audit Trail 2+ anos | Implementado |
| Consent Versioning | Implementado |
| SOC 2 Type II | Não implementado |
| EU AI Act | Parcial |

---

## 8. Especificação para Replicação (LangGraph)

### 8.1 Estrutura de Diretórios

```
lia-agent-system/
├── app/
│   ├── agents/
│   │   ├── base_agent.py              # BaseAgent, AgentType, AgentResponse
│   │   ├── agent_registry.py          # AgentRegistry, intent mapping
│   │   ├── prompts/
│   │   │   └── agent_prompts.py       # Prompts de cada agente
│   │   ├── robustness/
│   │   │   ├── intent_schemas.py
│   │   │   ├── error_handling.py
│   │   │   ├── input_validation.py
│   │   │   ├── context_management.py
│   │   │   ├── defensive_prompts.py
│   │   │   ├── enhanced_base.py
│   │   │   └── enhanced_registry.py
│   │   └── specialized/
│   │       ├── job_intake_agent.py     # 🆕 Integração com Intelligence Layer
│   │       ├── sourcing_agent.py
│   │       ├── triagem_curricular_agent.py
│   │       ├── entrevistador_agent.py
│   │       ├── avaliador_wsi_agent.py
│   │       ├── scheduling_agent.py
│   │       ├── analista_feedback_agent.py
│   │       ├── integrador_ats_agent.py
│   │       └── recruiter_assistant_agent.py
│   ├── models/
│   │   ├── job_draft.py                # 🆕 JobDraft, DraftFieldHistory
│   │   ├── recruiter_profile.py        # 🆕 RecruiterProfile, PersonalizationSettings
│   │   ├── intelligence_layer.py       # 🆕 IntelligenceInsight, PatternCache, etc.
│   │   └── feedback_learning.py        # 🆕 WizardFeedback, JobOutcome
│   ├── schemas/
│   │   └── field_typology.py           # 🆕 FieldTypology enum
│   ├── services/
│   │   ├── wsi_deterministic_scorer.py # Score 100% determinístico
│   │   ├── audit_service.py            # Auditoria LGPD
│   │   ├── llm.py                      # LLM Service (Claude + Gemini)
│   │   ├── intelligence_layer_service.py    # 🆕 Intelligence Layer
│   │   ├── recruiter_personalization_service.py  # 🆕 Personalização
│   │   ├── confidence_policy_service.py     # 🆕 Cálculo de confiança
│   │   ├── skills_catalog_service.py        # 🆕 Catálogo de skills
│   │   └── feedback_learning_service.py     # 🆕 Feedback learning
│   └── api/v1/
│       ├── lgpd_compliance.py
│       ├── consent_management.py
│       ├── job_drafts.py               # 🆕 Endpoints de drafts
│       ├── intelligence.py             # 🆕 Endpoints de intelligence
│       └── recruiter_profiles.py       # 🆕 Endpoints de personalização
```

### 8.2 Dependências Principais

```python
langchain>=0.1.0
langgraph>=0.0.20
langchain-anthropic>=0.1.0
langchain-google-genai>=0.0.10
langsmith>=0.0.50
fastapi>=0.104.0
pydantic>=2.0.0
sqlalchemy[asyncio]>=2.0.0
redis>=5.0.0
aio-pika>=9.0.0  # RabbitMQ
```

### 8.3 Variáveis de Ambiente

```bash
# LLMs
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Database
DATABASE_URL=postgresql://...

# Cache
REDIS_URL=redis://localhost:6379

# Queue
RABBITMQ_URL=amqp://localhost:5672

# Observability
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=lia-production

# Auth
WORKOS_API_KEY=...
WORKOS_CLIENT_ID=...

# Communication
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
MAILGUN_API_KEY=...

# ATS
MERGE_API_KEY=...
```

---

## 9. Checklist de Replicação

### Infraestrutura
- [ ] PostgreSQL configurado
- [ ] Redis configurado
- [ ] RabbitMQ configurado
- [ ] LangSmith account configurada

### LLMs
- [ ] Anthropic API Key
- [ ] Gemini API Key (fallback)
- [ ] Rate limiting configurado

### Agentes
- [ ] BaseAgent implementado
- [ ] AgentRegistry implementado
- [ ] 9 agentes especializados implementados
- [ ] Robustness module implementado

### Services Core
- [ ] WSI Deterministic Scorer (CRITICO - 100% determinístico)
- [ ] Rubric Evaluation Service (Híbrido LLM + fórmula, com calibração)
- [ ] Audit Service
- [ ] LLM Service com fallback

### 🆕 Services v3.0 (Intelligent Layer)
- [ ] Intelligence Layer Service
- [ ] Recruiter Personalization Service
- [ ] Confidence Policy Service
- [ ] Skills Catalog Service
- [ ] Feedback Learning Service

### 🆕 Models v3.0
- [ ] JobDraft + DraftFieldHistory
- [ ] RecruiterProfile + RecruiterFieldPreference + PersonalizationSettings
- [ ] IntelligenceInsight + PatternCache + SuccessProfile + OutcomeCorrelation
- [ ] WizardFeedback + JobOutcome

### 🆕 API Endpoints v3.0
- [ ] `/api/v1/job-drafts/*`
- [ ] `/api/v1/intelligence/*`
- [ ] `/api/v1/recruiter-profiles/*`

### Compliance
- [ ] Audit logging funcionando
- [ ] LGPD endpoints implementados
- [ ] Consent management implementado
- [ ] Protected criteria configurados

---

## 11. Fluxo de Inscrição de Candidato via Link Público + WhatsApp

### 11.1 Visão Geral do Fluxo

O candidato pode se inscrever em uma vaga através de um link público que inicia uma conversa no WhatsApp com a LIA.

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLUXO COMPLETO DE INSCRIÇÃO VIA WHATSAPP                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Link Público → WhatsApp → LGPD → CV → Pré-Qualificação → Triagem  │
│                                                                      │
│  1. Candidato acessa link público da vaga                           │
│  2. Clica em "Se inscrever via WhatsApp"                            │
│  3. LIA inicia conversa (estado: INITIAL)                           │
│  4. Candidato aceita LGPD (estado: WAITING_CV)                      │
│  5. CV recebido (estado: CONFIRMING_CV)                             │
│  6. Pré-qualificação (estado: PRE_QUALIFICATION)                    │
│  7. Triagem WSI (estado: SCREENING)                                 │
│  8. Dados adicionais (estado: ADDITIONAL_INFO)                      │
│  9. Conclusão (estado: COMPLETED)                                   │
│  10. Feedback (estado: FEEDBACK_SENT)                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 Estados do WhatsAppConversation

| Estado | Descrição | Próximo Estado |
|--------|-----------|----------------|
| `INITIAL` | Conversa iniciada | `WAITING_LGPD` |
| `WAITING_LGPD` | Aguardando aceite LGPD | `WAITING_CV` |
| `WAITING_CV` | Aguardando CV | `CONFIRMING_CV` |
| `CONFIRMING_CV` | Confirmando dados extraídos | `PRE_QUALIFICATION` |
| `PRE_QUALIFICATION` | Avaliando aderência | `SCREENING` ou `COMPLETED` |
| `SCREENING` | Perguntas WSI | `ADDITIONAL_INFO` |
| `ADDITIONAL_INFO` | Dados complementares | `COMPLETED` |
| `COMPLETED` | Finalizado | `FEEDBACK_SENT` |
| `FEEDBACK_SENT` | Feedback enviado | - (terminal) |

### 11.3 Sistema de Pré-Qualificação Inteligente

| Faixa | Score Interno | Comportamento |
|-------|---------------|---------------|
| **Alinhado** | ≥70% | Avança direto para triagem |
| **Parcial** | 50-69% | Mostra gaps + pergunta se quer continuar |
| **Distante** | 30-49% | Alerta transparente + alternativas |
| **Muito Distante** | <30% | Desencoraja + oferece banco de talentos |

---

## Changelog

| Versão | Data | Mudanças |
|--------|------|----------|
| **3.0** | **Jan 2026** | **🆕 Intelligence Layer, Recruiter Personalization, JobDraft, FieldTypology, Confidence Policy, Skills Catalog, Feedback Learning. Refatoração completa do job_intake_agent.py com integração de serviços inteligentes. APIs novas: /intelligence/*, /recruiter-profiles/*, /job-drafts/*** |
| 2.4 | Jan 2026 | Fluxo de inscrição via WhatsApp, Pré-qualificação inteligente, verificação de duplicidade |
| 2.3 | Jan 2026 | Documentação de riscos do sistema híbrido de Rubricas, calibração com feedback loop |
| 2.2 | Jan 2026 | Robustness module, fallback chains, WSI determinístico |
| 2.1 | Dez 2025 | Integração WorkOS, compliance LGPD |
| 2.0 | Nov 2025 | Arquitetura multi-agente com LangGraph |

---

## Conclusão

A arquitetura LIA v3.0 é composta por:

- **1 Orquestrador** com roteamento inteligente e fallback chains
- **9 Agentes Especializados** cobrindo todo o ciclo de recrutamento
- **Módulo de Robustez** para tratamento de erros e validação
- **Score WSI 100% Determinístico** (diferencial competitivo - sem LLM)
- **Rubric Evaluation Híbrida** (LLM para análise + fórmula para score + calibração)
- **Compliance LGPD** com auditoria completa
- 🆕 **Intelligence Layer** para detecção de padrões e correlações data-driven
- 🆕 **Personalização por Recrutador** com thresholds adaptativos e fluxo personalizado
- 🆕 **JobDraft** como estado intermediário com rastreamento de origem e confiança
- 🆕 **Field Typology** para tratamento diferenciado de campos
- 🆕 **Feedback Learning** para aprendizado contínuo

A documentação está pronta para replicação em ambiente separado usando LangGraph, LangChain, Redis, RabbitMQ e PostgreSQL.

---

> **Documentação mantida por**: Equipe LIA  
> **Última revisão**: 25 de Janeiro de 2026  
> **Documentos relacionados**: [job-wizard-enhancement-plan.md](./proposals/job-wizard-enhancement-plan.md)
