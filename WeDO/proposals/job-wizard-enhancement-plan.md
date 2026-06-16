# Plano de Implementação: Aprimoramento do Wizard de Criação de Vagas

> **Versão**: 7.2 (Orquestração Inteligente)  
> **Data**: Fevereiro 2026  
> **Status**: Em Produção  
> **Última Atualização**: 04 de Fevereiro de 2026
> **Documentos Consolidados Nesta Versão**: PLANO_FAST_TRACK_WIZARD.md, PLANO_IMPLEMENTACAO_WIZARD.md  
> **Documentos Consolidados**: FLUXO_WIZARD_VAGA_COMPLETO.md, LIA_PROACTIVE_ANALYSIS_SYSTEM.md, SETTINGS_MENU_MAPPING_FOR_WIZARD.md (v3.0), clustering-embeddings-proposal.md, TAXONOMIA_TEMPLATES.md, prompts/README.md  
> **Documento Relacionado**: O mapeamento Menu Configurações → Wizard foi revisado em `docs/SETTINGS_MENU_MAPPING_FOR_WIZARD.md` (v3.0)
> **Templates Curados**: 361 templates validados em 10 categorias (ver Seção 12)
> **Arquitetura**: 9 agentes especializados (v2.2), 26+ tools, 177+ serviços (ver Seções 22-27)
> **Integrações ATS**: 4 (Gupy, Pandapé, StackOne, Merge)

---

## Índice Geral

### PARTE 1: VISÃO GERAL E CONTEXTO
1. [Resumo Executivo](#1-resumo-executivo)
2. [Status de Implementação](#status-de-implementação-)
3. [Métricas de Sucesso](#métricas-de-sucesso)
4. [Arquitetura Alto Nível](#2-arquitetura-atual-vs-implementada)

### PARTE 2: MODELO DE DADOS E ESTRUTURAS
5. [Tipologia de Campos](#3-tipologia-de-campos)
6. [JobDraft - Estado Intermediário](#4-jobdraft---estado-intermediário)
7. [Níveis de Confiança](#5-níveis-de-confiança)
8. [Catálogo de Skills e Competências](#6-catálogo-de-skills-e-competências)
9. [Mapeamento de Configurações da Empresa](#25-mapeamento-de-configurações-da-empresa)

### PARTE 3: WIZARD DE CRIAÇÃO DE VAGAS
10. [Estrutura do Wizard (3 Fases, 7 Etapas)](#24-estrutura-completa-do-wizard-3-fases-7-etapas)
11. [Modos de Criação (Completo vs Fast Track)](#30-modos-de-criação-de-vagas-completo-vs-fast-track)
12. [Fast Track e Templates Curados](#29-fast-track-e-templates-curados)
13. [Serviços e Hooks Existentes (NÃO REIMPLEMENTAR)](#305-serviços-backend-existentes-não-reimplementar)
14. [Fases de Implementação do Wizard (9 Fases)](#306-fases-de-implementação-do-wizard-status)
15. [Sistema de Geração de Job Description](#22-sistema-de-geração-de-job-description)
16. [Sistema de Análise Proativa da LIA](#26-sistema-de-análise-proativa-da-lia)
17. [Fluxos Conversacionais Detalhados](#36-fluxos-conversacionais-detalhados)

### PARTE 4: LEARNING LOOP
18. [Intelligence Layer - Camada Centralizada](#18-intelligence-layer---camada-de-inteligência-centralizada)
19. [Personalização por Recrutador](#19-personalização-por-recrutador)
20. [Feedback Learning e Loop de Aprendizagem](#20-loop-de-aprendizagem-da-ia-feedback-learning)
21. [Sistema de Aprendizagem com Histórico](#28-sistema-de-aprendizagem-com-histórico-do-cliente)
22. [Learning Loop - Fase 1B: Importação de JDs](#37-learning-loop---fase-1b-importação-de-jds-do-ats)
23. [Próximos Passos: Clustering e Embeddings](#27-próximos-passos-clustering-e-embeddings)

### PARTE 5: ARQUITETURA TÉCNICA
24. [Arquitetura Multi-Agente (9 agentes)](#31-arquitetura-multi-agente)
25. [Sistema de Prompts](#32-sistema-de-prompts)
26. [Integrações LLM e Provedores de IA](#33-integrações-llm-e-provedores-de-ia)
27. [Cache e Otimização de Tokens](#335-cache-e-otimização-de-tokens)
28. [Serviços Principais (160+)](#34-serviços-principais)
29. [Arquivos Críticos para Reconstrução](#35-arquivos-críticos-para-reconstrução)

### APÊNDICES
A. [Sistema de Interação via Chat](#23-sistema-de-interação-com-sugestões-via-chat)
B. [Histórico de Mudanças](#21-histórico-de-mudanças)
C. [Conclusão das Fases 1-6](#conclusão-das-fases-1-6-janeiro-2026)

---

# PARTE 1: VISÃO GERAL E CONTEXTO

---

## Status de Implementação ✅

### Integrações Completas
- [x] **Pearch AI Integrado** - Substituídas funções mock por chamadas reais (liaApi.searchCandidatesLocal e liaApi.searchCandidates)
- [x] **Market Benchmark** - Endpoint backend `/job-wizard/salary-benchmark` + método frontend `getSalaryBenchmark` com UI mostrando dados internos + mercado
- [x] **Auto-save de Rascunho** - Hook `useWizardAutoSave` com salvamento dual (localStorage + backend) a cada 30s
- [x] **Restauração de Drafts entre Sessões** - Sistema completo com `wizardDraftId` persistido em localStorage, flags `hasAttemptedRestore` e `hasRestoredDraft` para controle preciso, reset automático ao sair do wizard, funciona corretamente para sessões novas e com drafts existentes
- [x] **UI de Progresso de Competências** - Contador visual "X/3 Técnicas" e "X/3 Comportamentais" com checkmarks
- [x] **Auto-preenchimento do Menu Configurações** - `fetchCompanyConfig` preenche automaticamente work_model, tech_stack, departments, benefits
- [x] **Calibração Flexível** - Slider para escolher 1-5 candidatos ideais
- [x] **Acessibilidade Aprimorada** - aria-labels, roles e aria-live adicionados em componentes críticos

### Funcionalidades Concluídas
- [x] Divisão do arquivo monolítico em componentes menores ✅ (Fevereiro 2026)
- [x] Integração de feedback learning em tempo real ✅ (Janeiro 2026)
- [x] Dashboard de analytics do wizard ✅ (Fevereiro 2026) - `wizard_analytics_service.py`
- [x] Outcome Learning (aprender com fechamento de vagas) ✅ (Janeiro 2026) - `record_outcome()` em `FeedbackLearningService`

### Fast Track e Templates (Fevereiro 2026)
- [x] **361 Templates Curados** - Expandido de 60 para 361 templates validados (10 categorias)
- [x] **10 Categorias** - tecnologia, comercial, rh, financas, administrativo, customer_success, saude, marketing, operacoes, jurídico
- [x] **WSI Quality Gates** - 100% dos templates com 5+ skills, 3+ behavioral, 5+ responsibilities
- [x] **Script de Validação** - `scripts/validate_templates.py` para CI integration
- [x] **Taxonomia Documentada** - `docs/templates/TAXONOMIA_TEMPLATES.md`
- [x] **Normalização de Categorias** - Aliases para vendas→comercial, recursos_humanos→rh
- [x] **Importação de JDs do Cliente** - Fase 1B do Learning Loop ✅ (02/Fev/2026)

---

## 1. Resumo Executivo

### 1.1 Objetivo
Aprimorar o wizard de criação de vagas para:
- Melhorar a experiência do recrutador com defaults mais inteligentes
- Classificar campos por tipologia para tratamento diferenciado
- Implementar estado intermediário (JobDraft) antes da publicação
- Expandir catálogo de skills para além de tecnologia
- Implementar Intelligence Layer para detecção de padrões e correlações
- Personalizar experiência por recrutador baseado em histórico
- Preparar infraestrutura para learning contínuo

### 1.2 Princípios Orientadores

| Princípio | Descrição |
|-----------|-----------|
| **Flexibilidade** | Manter estrutura atual do wizard, fazer melhorias incrementais |
| **Não-Disruptivo** | Evitar mudanças radicais na dinâmica existente |
| **Conversacional + Formulário** | Equilibrar conversa com campos estruturados |
| **Incremental** | Implementar em fases, validar cada uma |
| **Data-Driven** | Decisões baseadas em dados históricos e outcomes |
| **Personalizado** | Adaptar experiência por recrutador |

### 1.3 Status de Implementação

| Feature | Status | Data |
|---------|--------|------|
| Tipologia de Campos | ✅ Implementado | Jan 2026 |
| JobDraft | ✅ Implementado | Jan 2026 |
| Níveis de Confiança | ✅ Implementado | Jan 2026 |
| Catálogo de Skills | ✅ Implementado | Jan 2026 |
| Intelligence Layer | ✅ Implementado | Jan 2026 |
| Personalização por Recrutador | ✅ Implementado | Jan 2026 |
| API Endpoints | ✅ Implementado | Jan 2026 |
| Feedback Learning | ✅ Implementado | Jan 2026 |
| JD Generation (v1/v2) | ✅ Implementado | Jan 2026 |
| Suggestion Interaction via Chat | ✅ Implementado | Jan 2026 |
| **Fast Track Mode** | ✅ Implementado | Fev 2026 |
| **326 Templates Curados** | ✅ Implementado | Fev 2026 |
| **Taxonomia de Templates** | ✅ Implementado | Fev 2026 |
| **WSI Quality Gates** | ✅ Implementado | Fev 2026 |
| **Wizard Analytics Dashboard** | ✅ Implementado | Fev 2026 |
| **Outcome Learning** | ✅ Implementado | Jan 2026 |
| **Learning Loop (Seção 28)** | ✅ Implementado | Fev 2026 |
| **Importação de JDs (Fase 1B)** | ✅ Implementado | 02/Fev/2026 |

---

## 2. Arquitetura Atual vs. Implementada

### 2.1 Arquitetura Anterior

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  job-creation-wizard.tsx (3138 linhas)                      │
│  ├── 11 steps fixos                                         │
│  ├── Painéis por step (básico, técnico, comportamental...)  │
│  ├── Chat com LIA à esquerda                                │
│  └── buildContextPrompt() → envia contexto da empresa       │
│                                                              │
│  use-company-lia-instructions.ts                            │
│  ├── 19 campos configuráveis                                │
│  ├── Toggles por campo (admin configura)                    │
│  └── Filtra o que LIA recebe como contexto                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  job_intake_agent.py (2385 linhas)                          │
│  ├── 8 stages definidos                                     │
│  ├── CRITERIA_DETECTION_PROMPT (extrai campos)              │
│  ├── Prompts por stage (LIA_STAGE_MESSAGES)                 │
│  └── Cria JobVacancy diretamente                            │
│                                                              │
│  Services Existentes:                                        │
│  ├── feedback_learning_service.py (grava correções)         │
│  ├── job_insights_service.py (benchmarks internos)          │
│  ├── market_benchmark_service.py (dados de mercado)         │
│  └── jd_generator_service.py (gera JD)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  job-creation-wizard.tsx (melhorado)                        │
│  ├── 11 steps (mantidos)                                    │
│  ├── ✅ Indicadores de confiança por campo                  │
│  ├── ✅ Badges "Inferido" / "Confirmado" / "Default"        │
│  └── ✅ Painéis adaptam baseado em tipologia                │
│                                                              │
│  ✅ use-job-draft.ts                                        │
│  ├── Estado local do draft                                  │
│  ├── Rastreia inferred_fields vs confirmed_fields           │
│  └── Sincroniza com backend                                 │
│                                                              │
│  ✅ field-confidence-indicator.tsx                          │
│  └── Mostra nível de confiança visual                       │
│                                                              │
│  ✅ field-origin-badge.tsx                                  │
│  └── Mostra origem do valor (inferido, default, benchmark)  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ models/job_draft.py                                     │
│  └── JobDraft (estado intermediário antes de JobVacancy)    │
│                                                              │
│  ✅ schemas/field_typology.py                               │
│  └── FieldTypology enum + mapeamento de campos              │
│                                                              │
│  ✅ services/confidence_policy_service.py                   │
│  └── Cálculo determinístico de confiança                    │
│                                                              │
│  ✅ services/skills_catalog_service.py                      │
│  └── Catálogo de skills por área                            │
│                                                              │
│  ✅ services/intelligence_layer_service.py                  │
│  └── Pattern Detection, Outcome Correlation, Suggestions    │
│                                                              │
│  ✅ services/recruiter_personalization_service.py           │
│  └── Personalização por recrutador                          │
│                                                              │
│  job_intake_agent.py (refatorado)                           │
│  ├── Usa tipologia para decidir comportamento               │
│  ├── Retorna confidence_map no response                     │
│  ├── ✅ Integra Intelligence Layer para enriquecimento      │
│  ├── ✅ Integra Personalização por Recrutador               │
│  └── Cria JobDraft em vez de JobVacancy                     │
│                                                              │
│  ✅ api/v1/intelligence.py                                  │
│  └── Endpoints de inteligência (data-quality, context, etc) │
│                                                              │
│  ✅ api/v1/recruiter_profiles.py                            │
│  └── Endpoints de perfil do recrutador                      │
│                                                              │
│  Services Existentes (aprimorados):                          │
│  ├── feedback_learning_service.py + instrumentação          │
│  └── job_insights_service.py + mais categorias              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

# PARTE 2: MODELO DE DADOS E ESTRUTURAS

---

## 3. Tipologia de Campos

### 3.1 Classificação de Campos

Cada campo do wizard é classificado em uma tipologia que define seu comportamento:

```python
class FieldTypology(str, Enum):
    """Tipologia de campos para tratamento diferenciado"""
    
    IMPLICIT = "implicit"
    # Inferidos silenciosamente, não interrompem o fluxo
    # Ex: currency (sempre BRL), country (sempre Brasil)
    
    PROBABLE = "probable"
    # Auto-preenchidos via defaults da empresa
    # Mostrados mas não perguntados ativamente
    # Ex: work_model, employment_type, benefits
    
    CONDITIONAL = "conditional"
    # Ativados por gatilhos semânticos
    # Ex: hybrid_days (só se work_model = hybrid)
    
    CRITICAL = "critical"
    # Obrigatórios, bloqueiam avanço sem validação
    # Ex: job_title, seniority
    
    OPERATIONAL = "operational"
    # Uso interno, não interrompem fluxo
    # Ex: created_by, company_id, timestamps
    
    DERIVED = "derived"
    # Calculados automaticamente
    # Ex: job_complexity, estimated_ttf
```

### 3.2 Mapeamento Completo de Campos

| Campo | Tipologia | Comportamento |
|-------|-----------|---------------|
| `job_title` | CRITICAL | Sempre perguntar se não informado |
| `seniority` | CRITICAL | Inferir + confirmar se confiança < 80% |
| `department` | PROBABLE | Usar default se disponível |
| `location` | PROBABLE | Usar default da empresa |
| `work_model` | PROBABLE | Usar default da empresa |
| `hybrid_days` | CONDITIONAL | Só mostra se work_model = hybrid |
| `employment_type` | PROBABLE | Usar default da empresa |
| `salary_min` | CRITICAL | Sugerir benchmark + confirmar |
| `salary_max` | CRITICAL | Sugerir benchmark + confirmar |
| `currency` | IMPLICIT | Sempre BRL, nunca perguntar |
| `skills` | PROBABLE | Inferir + permitir edição |
| `behavioral_competencies` | PROBABLE | Sugerir baseado em role |
| `benefits` | PROBABLE | Usar defaults da empresa |
| `manager_id` | PROBABLE | Sugerir se detectado no contexto |
| `pipeline_stages` | PROBABLE | Usar template da empresa |
| `screening_questions` | DERIVED | Gerar baseado em WSI |
| `job_description` | DERIVED | Gerar baseado em dados |
| `estimated_ttf` | DERIVED | Calcular baseado em histórico |
| `job_complexity` | DERIVED | Calcular baseado em requisitos |
| `created_by` | OPERATIONAL | Automático, não mostrar |
| `company_id` | OPERATIONAL | Automático, não mostrar |

### 3.3 Implementação da Tipologia

**Arquivo**: `lia-agent-system/app/schemas/field_typology.py`

```python
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class FieldTypology(str, Enum):
    IMPLICIT = "implicit"
    PROBABLE = "probable"
    CONDITIONAL = "conditional"
    CRITICAL = "critical"
    OPERATIONAL = "operational"
    DERIVED = "derived"

@dataclass
class FieldDefinition:
    name: str
    typology: FieldTypology
    required: bool = False
    default_source: Optional[str] = None  # "company", "benchmark", "inference"
    condition: Optional[str] = None  # Para CONDITIONAL
    confidence_threshold: float = 0.7  # Threshold para auto-aplicar

FIELD_DEFINITIONS: Dict[str, FieldDefinition] = {
    "job_title": FieldDefinition(
        name="job_title",
        typology=FieldTypology.CRITICAL,
        required=True,
        confidence_threshold=0.9
    ),
    "seniority": FieldDefinition(
        name="seniority",
        typology=FieldTypology.CRITICAL,
        required=True,
        default_source="inference",
        confidence_threshold=0.8
    ),
    # ... demais campos
}
```

### 3.4 Hierarquia de Fontes de Dados

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      HIERARQUIA DE FONTES DE DADOS                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  PRECISÃO 100% ─────► USER_INPUT / COMPANY_DATA                                 │
│       │               Configurações da empresa + input direto                   │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 95% ──────► HISTORICAL                                                │
│       │               Histórico de vagas criadas na LIA                         │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 85% ──────► ATS_IMPORT                                                │
│       │               JDs importados via Gupy, Pandapé, StackOne, Merge         │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 80% ──────► MARKET_BENCHMARK                                          │
│       │               Dados de mercado, pesquisas salariais                     │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 70% ──────► TEMPLATE                                                  │
│       │               361 templates curados (fallback)                          │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 60% ──────► AI_INFERRED                                               │
│                       Inferido por IA quando não há outras fontes               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Campos por Etapa do Wizard

| Etapa | Campos Críticos | Fonte Primária | Fontes Secundárias |
|-------|-----------------|----------------|-------------------|
| **1. Input & Evaluation** | cargo, senioridade, modelo_trabalho, localização | COMPANY_DATA | HISTORICAL, ATS_IMPORT, TEMPLATE |
| **2. Remuneração** | faixa_salarial, bônus, benefícios | MARKET_BENCHMARK | ATS_IMPORT, HISTORICAL, COMPANY_DATA |
| **3. Competências** | skills_tecnicas, competencias_comportamentais, idiomas | HISTORICAL | ATS_IMPORT, COMPANY_DATA, TEMPLATE |
| **4. Perguntas WSI** | perguntas_triagem, perguntas_eliminatórias | TEMPLATE | ATS_IMPORT, HISTORICAL, AI_INFERRED |
| **5. Revisão e Publicação** | descricao_completa, canais_publicação | AI_INFERRED | ATS_IMPORT, COMPANY_DATA, USER_INPUT |
| **6. Busca e Calibração** | cutoffs, preferencias, filtros | HISTORICAL | ATS_IMPORT, USER_INPUT |

### 3.6 Impacto das Fontes por Etapa

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 FONTES DE DADOS POR ETAPA DO WIZARD                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Etapa                    Company  Historical  ATS     Template  AI            │
│                           Settings LIA         Import  Curado    Inferred      │
│  ──────────────────────── ──────── ────────── ─────── ──────── ──────          │
│  1. Input & Evaluation    ████████ ██████     █████   ███      ██              │
│  2. Remuneração           ████     ███████    ██████  ██       ███             │
│  3. Competências          ██████   ████████   ██████  ████     ██              │
│  4. Perguntas WSI         ██       ██████     █████   ███████  ████            │
│  5. Revisão e Publicação  █████    ████       █████   ██       ██████          │
│  6. Busca e Calibração    ██       ████████   ██████  █        ███             │
│                                                                                  │
│  Legenda: ████████ = Alta influência    ██ = Baixa influência                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. JobDraft - Estado Intermediário

### 4.1 Por que JobDraft?

Benefícios do estado intermediário:
- Rastrear quais campos foram inferidos vs confirmados
- Estado de "rascunho" antes de publicar
- Rastrear confiança por campo
- Permitir rollback de campos individuais
- Histórico completo de mudanças

### 4.2 Modelo JobDraft Implementado

**Arquivo**: `lia-agent-system/app/models/job_draft.py`

```python
class JobDraftStatus(str, Enum):
    DRAFT = "draft"           # Rascunho inicial
    STRUCTURED = "structured" # Campos estruturados
    REVIEWED = "reviewed"     # Revisado pelo recrutador
    CONFIRMED = "confirmed"   # Confirmado para publicação
    PUBLISHED = "published"   # Publicado (JobVacancy criada)
    CANCELLED = "cancelled"   # Cancelado

class JobDraft(Base):
    """
    Estado intermediário da vaga antes de publicação.
    Permite rastrear inferências, confirmações e confiança.
    """
    __tablename__ = "job_drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    recruiter_id = Column(String, nullable=False)
    conversation_id = Column(String, nullable=True)
    
    # Status do draft
    status = Column(SQLEnum(JobDraftStatus), default=JobDraftStatus.DRAFT)
    current_step = Column(Integer, default=1)
    
    # Input original
    raw_input = Column(Text)
    imported_jd = Column(Text)
    
    # Campos da vaga (estruturados)
    job_title = Column(String(200))
    department = Column(String(100))
    seniority = Column(String(50))
    location = Column(String(200))
    work_model = Column(String(50))
    employment_type = Column(String(50))
    salary_min = Column(Float)
    salary_max = Column(Float)
    currency = Column(String(10), default="BRL")
    
    # Listas estruturadas
    skills = Column(ARRAY(String))
    behavioral_competencies = Column(JSON)
    benefits = Column(ARRAY(String))
    languages = Column(ARRAY(String))
    
    # Campos derivados
    generated_jd = Column(Text)
    screening_questions = Column(JSON)
    pipeline_stages = Column(JSON)
    
    # Rastreamento de origem dos campos
    inferred_fields = Column(JSON, default={})
    # {"seniority": {"value": "Senior", "confidence": 0.85, "source": "text_analysis"}}
    
    confirmed_fields = Column(JSON, default={})
    # {"seniority": {"value": "Senior", "confirmed_at": "2026-01-24T10:00:00"}}
    
    company_defaults_used = Column(JSON, default={})
    # {"work_model": "hybrid", "benefits": [...]}
    
    confidence_map = Column(JSON, default={})
    # {"job_title": 0.95, "seniority": 0.85, "salary_min": 0.65}
    
    # Insights e alertas
    insights = Column(JSON, default=[])
    warnings = Column(JSON, default=[])
    
    # Referência à vaga publicada
    published_job_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    structured_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    published_at = Column(DateTime)
```

### 4.3 DraftFieldHistory - Histórico de Mudanças

```python
class DraftFieldHistory(Base):
    """Histórico de mudanças em campos do draft"""
    __tablename__ = "draft_field_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("job_drafts.id"), nullable=False)
    
    field_name = Column(String(100), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    
    change_type = Column(String(50))  # "inferred", "confirmed", "edited", "reverted"
    confidence_at_change = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)  # recruiter_id ou "system"
```

---

## 5. Níveis de Confiança

### 5.1 Sistema de Confiança Determinístico

**Arquivo**: `lia-agent-system/app/services/confidence_policy_service.py`

```python
class ConfidenceAction(str, Enum):
    APPLY_SILENT = "apply_silent"      # Aplica sem avisar
    APPLY_NOTIFY = "apply_notify"      # Aplica e mostra badge
    ASK_USER = "ask_user"              # Pergunta ao usuário
    ALERT_CONFLICT = "alert_conflict"  # Alerta de conflito

@dataclass
class ConfidenceThresholds:
    """Thresholds configuráveis"""
    silent_apply: float = 0.85   # Aplica silenciosamente
    apply_notify: float = 0.70   # Aplica com notificação
    ask_user: float = 0.50       # Pergunta ao usuário
    # Abaixo de 0.50 = alert_conflict

class ConfidencePolicyService:
    """
    Serviço para cálculo determinístico de confiança.
    NÃO usa LLM - apenas regras e histórico.
    """
    
    def calculate_field_confidence(
        self,
        field: str,
        value: Any,
        sources: Dict[str, Any]
    ) -> float:
        """
        Calcula confiança para um campo de forma determinística.
        
        Sources podem incluir:
        - text_extraction: valor extraído do texto do recrutador
        - company_default: valor default da empresa
        - benchmark: valor de benchmark de mercado
        - similar_jobs: valor de vagas similares
        - correction_history: histórico de correções
        """
        base_confidence = 0.0
        
        # 1. Confiança base por fonte
        source_weights = {
            "text_extraction": 0.7,
            "company_default": 0.85,
            "benchmark": 0.6,
            "similar_jobs": 0.75,
        }
        
        for source, source_value in sources.items():
            if source_value is not None:
                weight = source_weights.get(source, 0.5)
                base_confidence = max(base_confidence, weight)
        
        # 2. Ajuste por histórico de correções
        if "correction_history" in sources:
            history = sources["correction_history"]
            if history.get("acceptance_rate", 0) > 0.8:
                base_confidence *= 1.1
            elif history.get("acceptance_rate", 1) < 0.4:
                base_confidence *= 0.8
        
        # 3. Ajuste por consistência de fontes
        if len([s for s in sources.values() if s is not None]) >= 2:
            if self._sources_agree(sources):
                base_confidence *= 1.05
        
        return min(0.95, max(0.1, base_confidence))
    
    def determine_action(
        self,
        confidence: float,
        thresholds: ConfidenceThresholds = None
    ) -> ConfidenceAction:
        """Determina ação baseada no nível de confiança."""
        t = thresholds or ConfidenceThresholds()
        
        if confidence >= t.silent_apply:
            return ConfidenceAction.APPLY_SILENT
        elif confidence >= t.apply_notify:
            return ConfidenceAction.APPLY_NOTIFY
        elif confidence >= t.ask_user:
            return ConfidenceAction.ASK_USER
        else:
            return ConfidenceAction.ALERT_CONFLICT
```

---

## 6. Catálogo de Skills e Competências

### 6.1 SkillsCatalogService Implementado

**Arquivo**: `lia-agent-system/app/services/skills_catalog_service.py`

```python
class SkillsCatalogService:
    """
    Catálogo expandido de skills por área.
    """
    
    SKILLS_BY_AREA = {
        "technology": {
            "backend": ["Python", "Java", "Node.js", "Go", "Rust", "C#", "Ruby"],
            "frontend": ["React", "Vue.js", "Angular", "TypeScript", "JavaScript"],
            "data": ["SQL", "Python", "Spark", "Airflow", "dbt", "Pandas"],
            "devops": ["Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform"],
            "mobile": ["Swift", "Kotlin", "React Native", "Flutter"],
        },
        "finance": {
            "contabilidade": ["SAP", "Excel Avançado", "Power BI", "Contabilidade IFRS"],
            "financeiro": ["Modelagem Financeira", "Valuation", "M&A", "Bloomberg"],
            "auditoria": ["SOX", "Controles Internos", "Normas IFRS"],
        },
        "hr": {
            "recrutamento": ["ATS", "Sourcing", "Employer Branding", "Entrevistas"],
            "dp": ["Folha de Pagamento", "eSocial", "Legislação Trabalhista"],
            "dhp": ["Treinamento", "Avaliação de Desempenho", "Clima Organizacional"],
        },
        "marketing": {
            "digital": ["SEO", "SEM", "Google Ads", "Facebook Ads", "Analytics"],
            "conteudo": ["Copywriting", "Content Marketing", "Social Media"],
            "produto": ["Product Marketing", "Go-to-Market", "Pricing"],
        },
        "sales": {
            "vendas": ["CRM", "Salesforce", "HubSpot", "Negociação", "Closing"],
            "cs": ["Customer Success", "Onboarding", "Churn Prevention"],
        },
    }
    
    BEHAVIORAL_COMPETENCIES = {
        "leadership": ["Liderança", "Gestão de Equipes", "Tomada de Decisão"],
        "communication": ["Comunicação", "Apresentação", "Negociação"],
        "analytical": ["Pensamento Analítico", "Resolução de Problemas"],
        "interpersonal": ["Trabalho em Equipe", "Colaboração", "Empatia"],
        "execution": ["Orientação a Resultados", "Proatividade", "Autonomia"],
    }
    
    def get_skills_for_role(
        self,
        role: str,
        area: str,
        seniority: str
    ) -> Dict[str, List[str]]:
        """
        Retorna skills sugeridas para uma combinação role/area/seniority.
        """
        suggested = {
            "must_have": [],
            "nice_to_have": [],
            "behavioral": [],
        }
        
        # Detectar área principal
        detected_area = self._detect_area(role, area)
        
        # Buscar skills técnicas
        if detected_area in self.SKILLS_BY_AREA:
            all_skills = []
            for category, skills in self.SKILLS_BY_AREA[detected_area].items():
                if self._category_matches_role(category, role):
                    all_skills.extend(skills)
            
            # Dividir por senioridade
            if seniority in ["senior", "specialist", "lead"]:
                suggested["must_have"] = all_skills[:5]
                suggested["nice_to_have"] = all_skills[5:10]
            else:
                suggested["must_have"] = all_skills[:3]
                suggested["nice_to_have"] = all_skills[3:8]
        
        # Adicionar competências comportamentais
        suggested["behavioral"] = self._get_behavioral_for_seniority(seniority)
        
        return suggested
```

---

# PARTE 4: LEARNING LOOP

---

## 18. Intelligence Layer - Camada de Inteligência Centralizada

### 18.1 Visão Geral

A Intelligence Layer é uma camada de inteligência que centraliza todo conhecimento acumulado e decisões baseadas em dados, funcionando como o "cérebro" que alimenta todos os agentes e serviços.

```
┌─────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Pattern    │  │   Outcome    │  │  Confidence  │       │
│  │   Detector   │  │  Correlator  │  │   Adjuster   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│  ┌─────────────────────────▼─────────────────────────────┐  │
│  │              Knowledge Repository                      │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │  │
│  │  │ Padrões │ │ Regras  │ │Histórico│ │Benchmark│      │  │
│  │  │ Sucesso │ │ Ajuste  │ │Correções│ │ Mercado │      │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Decision Engine                       │  │
│  │  • Qual sugestão mostrar?                             │  │
│  │  • Qual confiança aplicar?                            │  │
│  │  • Quando interromper vs. assumir?                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  ┌──────────┐         ┌──────────┐         ┌──────────┐
  │  Wizard  │         │ Sourcing │         │   WSI    │
  │  Agent   │         │  Agent   │         │ Evaluator│
  └──────────┘         └──────────┘         └──────────┘
```

### 18.2 Componentes Implementados

#### 18.2.1 Pattern Detector

**Arquivo**: `lia-agent-system/app/services/intelligence_layer_service.py`

```python
async def detect_patterns(
    self,
    company_id: str,
    pattern_type: str,
    context: Optional[Dict[str, Any]] = None
) -> List[DetectedPattern]:
    """
    Detecta padrões em correções, comportamentos e outcomes.
    
    pattern_type:
    - "correction": Padrões de correção por campo
    - "success": Características de vagas bem-sucedidas
    - "timing": Padrões temporais (horários, dias)
    """
    patterns = []
    
    if pattern_type == "correction":
        # Analisar correções por campo
        corrections = await self._get_corrections(company_id, context)
        
        for field, field_corrections in corrections.items():
            if len(field_corrections) >= 5:
                direction = self._analyze_direction(field_corrections)
                avg_adjustment = self._calculate_avg_adjustment(field_corrections)
                
                patterns.append(DetectedPattern(
                    pattern_type="correction",
                    field=field,
                    direction=direction,
                    avg_adjustment=avg_adjustment,
                    confidence=min(1.0, len(field_corrections) / 20),
                    sample_size=len(field_corrections),
                    context=context
                ))
    
    elif pattern_type == "success":
        # Analisar vagas bem-sucedidas
        successful_jobs = await self._get_successful_jobs(company_id, context)
        
        if len(successful_jobs) >= 10:
            patterns.append(DetectedPattern(
                pattern_type="success_profile",
                characteristics=self._extract_common_characteristics(successful_jobs),
                confidence=min(1.0, len(successful_jobs) / 30),
                sample_size=len(successful_jobs)
            ))
    
    return patterns
```

#### 18.2.2 Outcome Correlator

```python
async def analyze_correlations(
    self,
    company_id: str,
    outcome_metric: str = "time_to_fill"
) -> CorrelationAnalysis:
    """
    Correlaciona características de vagas com resultados.
    
    Returns:
        {
            "positive_correlations": [
                {"factor": "salary_at_p75", "correlation": 0.72},
                {"factor": "detailed_jd", "correlation": 0.65},
            ],
            "negative_correlations": [
                {"factor": "many_required_skills", "correlation": -0.45},
            ],
            "recommendations": [...]
        }
    """
    jobs_with_outcomes = await self._get_jobs_with_outcomes(company_id)
    
    if len(jobs_with_outcomes) < 30:
        return CorrelationAnalysis(
            ready=False,
            message="Dados insuficientes para análise de correlação"
        )
    
    factors = self._extract_factors(jobs_with_outcomes)
    outcomes = self._extract_outcomes(jobs_with_outcomes, outcome_metric)
    
    correlations = []
    for factor_name, factor_values in factors.items():
        corr = self._calculate_correlation(factor_values, outcomes)
        if abs(corr) > 0.3:
            correlations.append({
                "factor": factor_name,
                "correlation": corr,
                "significance": self._calculate_significance(len(jobs_with_outcomes), corr)
            })
    
    return CorrelationAnalysis(
        ready=True,
        positive=[c for c in correlations if c["correlation"] > 0],
        negative=[c for c in correlations if c["correlation"] < 0],
        recommendations=self._generate_recommendations(correlations)
    )
```

#### 18.2.3 Confidence Adjuster Dinâmico

```python
async def get_adjusted_threshold(
    self,
    company_id: str,
    recruiter_id: str,
    field: str
) -> Dict[str, float]:
    """
    Retorna thresholds ajustados para este recrutador/campo.
    
    Lógica:
    - Se recrutador sempre aceita sugestões → aumentar threshold
    - Se recrutador sempre corrige → diminuir threshold
    - Se empresa tem padrão diferente → ajustar para empresa
    """
    # 1. Buscar taxa de aceitação do recrutador para este campo
    acceptance_rate = await self._get_field_acceptance_rate(recruiter_id, field)
    
    # 2. Buscar taxa de aceitação da empresa
    company_rate = await self._get_company_acceptance_rate(company_id, field)
    
    # 3. Combinar (peso maior para recrutador individual)
    combined_rate = acceptance_rate * 0.7 + company_rate * 0.3
    
    # 4. Ajustar thresholds
    adjustment = 1.0 + (combined_rate - 0.5) * 0.3
    
    base = {
        "silent_apply": 0.85,
        "apply_with_notice": 0.70,
        "ask_user": 0.50,
        "alert_conflict": 0.30,
    }
    
    return {
        key: min(0.95, max(0.3, value * adjustment))
        for key, value in base.items()
    }
```

### 18.3 Modelos de Dados da Intelligence Layer

**Arquivo**: `lia-agent-system/app/models/intelligence_layer.py`

```python
class IntelligenceInsight(Base):
    """Log de insights gerados pela Intelligence Layer"""
    __tablename__ = "intelligence_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    recruiter_id = Column(String(255), nullable=True)
    
    insight_type = Column(String(50))  # pattern, prediction, correlation, adjustment
    field = Column(String(100))
    
    original_value = Column(JSON)
    suggested_value = Column(JSON)
    confidence = Column(Float)
    source = Column(String(50))
    reasoning = Column(Text)
    
    was_applied = Column(Boolean, nullable=True)
    was_accepted = Column(Boolean, nullable=True)
    final_value = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PatternCache(Base):
    """Cache de padrões calculados"""
    __tablename__ = "pattern_caches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(50))
    pattern_key = Column(String(200))  # ex: "salary_range:dev_senior"
    
    pattern_data = Column(JSON)
    sample_size = Column(Integer)
    confidence = Column(Float)
    
    calculated_at = Column(DateTime)
    expires_at = Column(DateTime)


class SuccessProfile(Base):
    """Perfil de sucesso por tipo de vaga"""
    __tablename__ = "success_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    role_pattern = Column(String(200))
    seniority_pattern = Column(String(50))
    department_pattern = Column(String(100))
    
    optimal_salary_percentile = Column(Integer)
    optimal_skills_count = Column(Integer)
    optimal_screening_questions = Column(Integer)
    avg_time_to_fill = Column(Integer)
    avg_pipeline_length = Column(Integer)
    
    characteristics = Column(JSON)
    sample_size = Column(Integer)
    confidence = Column(Float)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)


class OutcomeCorrelation(Base):
    """Correlações entre características e outcomes"""
    __tablename__ = "outcome_correlations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    factor_name = Column(String(100))
    outcome_metric = Column(String(50))
    
    correlation_value = Column(Float)
    significance = Column(Float)
    sample_size = Column(Integer)
    
    recommendation = Column(Text)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
```

### 18.4 API Endpoints da Intelligence Layer

**Arquivo**: `lia-agent-system/app/api/v1/intelligence.py`

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/intelligence/data-quality` | GET | Avalia qualidade de dados para inteligência |
| `/api/v1/intelligence/context` | POST | Retorna contexto de inteligência para um campo |
| `/api/v1/intelligence/adjust-field` | POST | Ajusta sugestão de campo com inteligência |
| `/api/v1/intelligence/wizard-enhancements` | GET | Melhorias do wizard baseadas em padrões |
| `/api/v1/intelligence/success-profile` | GET | Perfil de sucesso para role/seniority |
| `/api/v1/intelligence/correlations` | GET | Correlações de outcomes |

### 18.5 Requisitos de Dados

| Requisito | Volume Mínimo | Propósito |
|-----------|---------------|-----------|
| Total de vagas | 50+ | Detecção de padrões |
| Outcomes registrados | 30+ | Análise de correlações |
| Meses de dados | 3+ | Insights de correlação temporal |
| Vagas por recrutador | 10+ | Personalização individual |

### 18.6 Integração com job_intake_agent.py

**Arquivo**: `lia-agent-system/app/agents/specialized/job_intake_agent.py`

```python
# Imports adicionados
from app.services.intelligence_layer_service import intelligence_layer_service
from app.services.recruiter_personalization_service import recruiter_personalization_service

# Enriquecimento após extração LLM
async def _enrich_with_intelligence(
    self,
    extracted_data: Dict[str, Any],
    company_id: str,
    recruiter_id: str
) -> Dict[str, Any]:
    """
    Enriquece dados extraídos com Intelligence Layer.
    """
    # 1. Verificar qualidade de dados
    data_quality = await intelligence_layer_service.assess_data_quality(
        company_id=company_id
    )
    
    # 2. Se dados suficientes, buscar contexto de inteligência
    if data_quality.get("pattern_detection_ready"):
        context = await intelligence_layer_service.build_intelligence_context(
            company_id=company_id,
            recruiter_id=recruiter_id,
            role=extracted_data.get("job_title"),
            seniority=extracted_data.get("seniority"),
            department=extracted_data.get("department")
        )
        
        # Aplicar ajustes de padrões de correção
        if context.get("correction_patterns"):
            for field, pattern in context["correction_patterns"].items():
                if field in extracted_data and pattern.get("adjustment_factor"):
                    extracted_data[field] *= pattern["adjustment_factor"]
        
        # Adicionar predição de time-to-fill
        if context.get("time_to_fill_prediction"):
            extracted_data["estimated_ttf"] = context["time_to_fill_prediction"]
    
    # 3. Aplicar personalização do recrutador
    personalization = await recruiter_personalization_service.get_personalized_thresholds(
        recruiter_id=recruiter_id,
        company_id=company_id
    )
    
    if personalization.field_overrides:
        for field, override in personalization.field_overrides.items():
            if "threshold" in override:
                # Ajustar threshold de confiança para este campo
                extracted_data.setdefault("_field_thresholds", {})[field] = override["threshold"]
    
    return extracted_data
```

---

## 19. Personalização por Recrutador

### 19.1 Visão Geral

Personalização da experiência do wizard para cada recrutador baseado em:
- Suas preferências históricas
- Seu padrão de correções
- Seus tipos de vagas mais comuns
- Seu estilo de interação

### 19.2 Modelo RecruiterProfile Implementado

**Arquivo**: `lia-agent-system/app/models/recruiter_profile.py`

```python
class RecruiterProfile(Base):
    """
    Perfil de personalização para cada recrutador.
    
    Tracks:
    - Usage statistics (jobs created, avg completion time)
    - Detected preferences (seniorities, departments)
    - Correction patterns (which fields are often corrected)
    - Interaction preferences (quick flow, detailed explanations)
    """
    __tablename__ = "recruiter_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, unique=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
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
    wizard_mode = Column(String(50), nullable=True)  # "quick", "detailed", "standard"
    experience_level = Column(String(50), nullable=True)  # "beginner", "intermediate", "expert"
    profile_version = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Propriedades derivadas
    @property
    def prefers_quick_flow(self) -> bool:
        return self.wizard_mode == "quick"
    
    @property
    def prefers_detailed_explanations(self) -> bool:
        return self.wizard_mode == "detailed"
    
    @property
    def fields_often_corrected(self) -> dict:
        return self.correction_patterns or {}


class RecruiterFieldPreference(Base):
    """
    Preferências por campo para cada recrutador.
    """
    __tablename__ = "recruiter_field_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, index=True)
    recruiter_profile_id = Column(UUID(as_uuid=True), nullable=True)
    field_name = Column(String(100), nullable=False)
    
    # Estatísticas
    correction_count = Column(Integer, default=0)
    total_encounters = Column(Integer, default=0)
    correction_rate = Column(Float, default=0.0)
    
    # Padrões
    typical_corrections = Column(JSON, default=list)
    preferred_values = Column(JSON, default=list)
    value_range = Column(JSON, nullable=True)
    
    # Threshold personalizado
    custom_threshold = Column(Float, nullable=True)
    always_ask = Column(Boolean, default=False)
    
    last_correction_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PersonalizationSettings(Base):
    """
    Configurações de privacidade controladas pelo usuário.
    """
    __tablename__ = "personalization_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Opt-in/out
    enable_personalization = Column(Boolean, default=True)
    use_correction_history = Column(Boolean, default=True)
    use_preference_detection = Column(Boolean, default=True)
    use_outcome_data = Column(Boolean, default=True)
    
    # Transparência
    show_confidence_indicators = Column(Boolean, default=True)
    explain_suggestions = Column(Boolean, default=True)
    
    # Auto-aprovação
    auto_approve_high_confidence = Column(Boolean, default=True)
    high_confidence_threshold = Column(Float, default=0.90)
    
    # Retenção
    data_retention_months = Column(Integer, default=24)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProfileCalculationLog(Base):
    """
    Log de recálculos de perfil.
    """
    __tablename__ = "profile_calculation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_profile_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    trigger = Column(String(50), nullable=False)
    jobs_analyzed = Column(Integer, default=0)
    corrections_analyzed = Column(Integer, default=0)
    outcomes_analyzed = Column(Integer, default=0)
    
    changes_detected = Column(JSON, default=list)
    
    previous_profile_snapshot = Column(JSON, nullable=True)
    new_profile_snapshot = Column(JSON, nullable=True)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_time_ms = Column(Integer, nullable=True)
```

### 19.3 RecruiterPersonalizationService Implementado

**Arquivo**: `lia-agent-system/app/services/recruiter_personalization_service.py`

```python
class RecruiterPersonalizationService:
    """
    Serviço de personalização baseado em perfil do recrutador.
    """
    
    async def get_personalized_thresholds(
        self,
        recruiter_id: str,
        company_id: str
    ) -> PersonalizedThresholds:
        """
        Retorna thresholds personalizados para este recrutador.
        """
        async with get_session() as db:
            profile = await self._get_or_create_profile(db, recruiter_id, company_id)
            settings = await self._get_settings(db, recruiter_id)
            
            if not settings or not settings.enable_personalization:
                return PersonalizedThresholds()  # Defaults
            
            # Ajustar thresholds baseado no perfil
            adjustment = profile.confidence_threshold_adjustment or 0.0
            
            thresholds = PersonalizedThresholds(
                silent_apply=min(0.95, 0.85 + adjustment),
                apply_notify=min(0.90, 0.70 + adjustment),
                ask_user=min(0.80, 0.50 + adjustment),
            )
            
            # Aplicar overrides por campo
            field_overrides = {}
            preferences = await self._get_field_preferences(db, recruiter_id)
            
            for pref in preferences:
                if pref.custom_threshold:
                    field_overrides[pref.field_name] = {
                        "threshold": pref.custom_threshold,
                        "always_ask": pref.always_ask
                    }
            
            thresholds.field_overrides = field_overrides
            
            return thresholds
    
    async def get_personalized_defaults(
        self,
        recruiter_id: str,
        company_id: str,
        job_context: Dict[str, Any]
    ) -> PersonalizedDefaults:
        """
        Retorna defaults personalizados para este recrutador.
        """
        async with get_session() as db:
            profile = await self._get_profile(db, recruiter_id)
            
            if not profile or profile.total_jobs_created < MIN_JOBS_FOR_PERSONALIZATION:
                return PersonalizedDefaults()
            
            defaults = PersonalizedDefaults()
            
            # Senioridade mais comum
            if profile.preferred_seniorities and len(profile.preferred_seniorities) > 0:
                defaults.seniority = profile.preferred_seniorities[0]
            
            # Departamento mais comum
            if profile.preferred_departments and len(profile.preferred_departments) > 0:
                defaults.department = profile.preferred_departments[0]
            
            # Ajustar salário baseado em padrões de correção
            if "salary" in profile.correction_patterns:
                pattern = profile.correction_patterns["salary"]
                if pattern.get("direction") == "increase":
                    defaults.salary_adjustment = 1.0 + pattern.get("avg_adjustment", 0.1)
                elif pattern.get("direction") == "decrease":
                    defaults.salary_adjustment = 0.9
            
            return defaults
    
    async def record_event(
        self,
        db: AsyncSession,
        recruiter_id: str,
        company_id: str,
        event_type: str,
        field_name: Optional[str] = None,
        job_id: Optional[UUID] = None,
        suggested_value: Any = None,
        final_value: Any = None,
        context: Optional[Dict[str, Any]] = None,
        time_to_decision_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Registra evento de personalização para aprendizado.
        
        Event types:
        - field_suggested: A field suggestion was shown
        - field_accepted: Suggestion was accepted without change
        - field_corrected: Suggestion was corrected
        - step_skipped: Optional step was skipped
        - explanation_dismissed: Explanation was closed quickly
        - jd_imported: JD import feature was used
        """
        event_data = {
            "recruiter_id": recruiter_id,
            "company_id": company_id,
            "job_id": str(job_id) if job_id else None,
            "event_type": event_type,
            "field_name": field_name,
            "suggested_value": suggested_value,
            "final_value": final_value,
            "context": context or {},
            "time_to_decision_ms": time_to_decision_ms,
        }
        
        if field_name and event_type in ["field_accepted", "field_corrected"]:
            await self._update_field_preference(
                db, recruiter_id, field_name,
                accepted=(event_type == "field_accepted"),
                suggested_value=suggested_value,
                final_value=final_value
            )
        
        return event_data
    
    async def recalculate_profile(
        self,
        recruiter_id: str
    ) -> Optional[RecruiterProfile]:
        """
        Recalcula perfil do recrutador baseado em WizardFeedback.
        """
        async with get_session() as db:
            profile = await self._get_profile(db, recruiter_id)
            
            if not profile:
                return None
            
            # Buscar feedbacks para análise
            feedback_query = select(WizardFeedback).where(
                WizardFeedback.user_id == recruiter_id
            )
            feedback_result = await db.execute(feedback_query)
            feedbacks = list(feedback_result.scalars().all())
            
            # Análise de padrões
            job_ids = set()
            seniorities: Dict[str, int] = {}
            departments: Dict[str, int] = {}
            field_corrections: Dict[str, int] = {}
            field_totals: Dict[str, int] = {}
            creation_times = []
            
            for fb in feedbacks:
                if fb.job_id:
                    job_ids.add(fb.job_id)
                
                ctx = fb.context or {}
                
                if ctx.get("seniority"):
                    sen = ctx["seniority"]
                    seniorities[sen] = seniorities.get(sen, 0) + 1
                
                if ctx.get("department"):
                    dep = ctx["department"]
                    departments[dep] = departments.get(dep, 0) + 1
                
                field_name = fb.field_name
                if field_name:
                    field_totals[field_name] = field_totals.get(field_name, 0) + 1
                    if fb.feedback_type == "correction":
                        field_corrections[field_name] = field_corrections.get(field_name, 0) + 1
                
                if fb.response_time_ms:
                    creation_times.append(fb.response_time_ms)
            
            # Atualizar perfil
            profile.total_jobs_created = len(job_ids)
            
            if creation_times:
                profile.avg_completion_time_seconds = statistics.mean(creation_times) / 1000
            
            top_seniorities = sorted(seniorities.items(), key=lambda x: -x[1])[:3]
            profile.preferred_seniorities = [s[0] for s in top_seniorities]
            
            top_departments = sorted(departments.items(), key=lambda x: -x[1])[:3]
            profile.preferred_departments = [d[0] for d in top_departments]
            
            correction_rates = {}
            for field, total in field_totals.items():
                corrections = field_corrections.get(field, 0)
                rate = corrections / total if total > 0 else 0
                if rate > 0.1:
                    correction_rates[field] = rate
            
            profile.correction_patterns = correction_rates
            profile.total_corrections_made = sum(field_corrections.values())
            
            # Determinar wizard_mode
            quick_decisions = sum(
                1 for fb in feedbacks
                if fb.response_time_ms and fb.response_time_ms < 3000
            )
            if feedbacks and quick_decisions > len(feedbacks) * 0.6:
                profile.wizard_mode = "quick"
            else:
                profile.wizard_mode = "detailed"
            
            profile.last_activity_at = datetime.utcnow()
            
            await db.flush()
            
            return profile
```

### 19.4 API Endpoints de Personalização

**Arquivo**: `lia-agent-system/app/api/v1/recruiter_profiles.py`

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/recruiter-profiles/me` | GET | Retorna perfil do recrutador atual |
| `/api/v1/recruiter-profiles/me/settings` | GET | Retorna configurações de personalização |
| `/api/v1/recruiter-profiles/me/field-preferences` | GET | Retorna preferências por campo |
| `/api/v1/recruiter-profiles/me/thresholds` | GET | Retorna thresholds personalizados |
| `/api/v1/recruiter-profiles/me/events` | POST | Registra evento de personalização |
| `/api/v1/recruiter-profiles/me/recalculate` | POST | Força recálculo do perfil |

### 19.5 Casos de Uso de Personalização

#### Recrutador de Tech (Maria)
**Perfil detectado:**
- Cria principalmente vagas de Dev Sênior
- Sempre aumenta salário sugerido em ~15%
- Pula explicações detalhadas
- Usa JD import frequentemente

**Comportamento personalizado:**
```
Maria: "Dev Python Sênior"

LIA (personalizada):
"Dev Python Sênior para Engenharia. 
Salário: R$ 20.000 - R$ 26.000 (ajustado ao seu padrão).
Skills: Python, FastAPI, AWS.

[Próximo →]"

(Sem explicações longas, fluxo direto, salário já ajustado)
```

#### Recrutador Novo (João)
**Perfil detectado:**
- Apenas 3 vagas criadas
- Dados insuficientes para personalização

**Comportamento:**
```
João: "Dev Python Sênior"

LIA (padrão):
"Entendi que você precisa de um Desenvolvedor Python Sênior!

Vou preencher automaticamente baseado nos dados da empresa:
• Salário: R$ 18.000 - R$ 22.000 (benchmark interno)
• Skills sugeridas: Python, SQL, REST APIs

Quer me contar mais sobre a vaga ou posso continuar com essas configurações?"

(Modo explicativo completo para novo usuário)
```

#### Recrutador Executivo (Carla)
**Perfil detectado:**
- Cria vagas de gestão/diretoria
- Linguagem formal
- Detalhista, não pula etapas
- Faz muitas correções em competências

**Comportamento personalizado:**
```
Carla: "Diretor de Tecnologia"

LIA (personalizada):
"Prezada Carla,

Para a posição de Diretor de Tecnologia, preparei as seguintes sugestões:

**Remuneração Executiva:**
- Faixa salarial: R$ 45.000 - R$ 65.000
- Bônus anual: 3-6 salários

**Competências de Liderança:**
Gostaria de sua validação para estas competências, pois observei que você costuma ajustá-las:
- Visão Estratégica (Essencial)
- Gestão de P&L (Essencial)
- Liderança de Equipes (Essencial)

Poderia confirmar ou ajustar conforme necessário?"

(Tom formal, pedindo confirmação onde costuma corrigir)
```

### 19.6 Privacidade e Transparência

```python
class PersonalizationSettings(Base):
    """Configurações de privacidade controladas pelo usuário"""
    
    # Opt-in/out
    enable_personalization = Column(Boolean, default=True)
    use_correction_history = Column(Boolean, default=True)
    use_preference_detection = Column(Boolean, default=True)
    use_outcome_data = Column(Boolean, default=True)
    
    # Transparência
    show_confidence_indicators = Column(Boolean, default=True)
    explain_suggestions = Column(Boolean, default=True)
```

**Indicadores de Transparência:**
```
LIA: "Salário: R$ 22.000 - R$ 28.000 
     📊 Ajustado ao seu padrão (+15% vs. benchmark)"
     
LIA: "[Próximo →]
     ⚡ Modo rápido ativado (baseado no seu histórico)"
```

---

## 20. Loop de Aprendizagem da IA (Feedback Learning)

### 20.1 Ciclo de Aprendizado

```
┌────────────────────────────────────────────────────────────┐
│                   CICLO DE APRENDIZADO                      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │Interação│───▶│ Registro│───▶│ Análise │───▶│Atualiza │ │
│  │ Wizard  │    │  Evento │    │ Padrão  │    │ Perfil  │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│       │                                             │       │
│       └─────────────────────────────────────────────┘       │
│                    (próxima interação)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 EVENTOS REGISTRADOS                  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ • field_suggested: campo X sugerido com valor Y     │   │
│  │ • field_accepted: sugestão aceita sem alteração     │   │
│  │ • field_corrected: valor alterado de Y para Z       │   │
│  │ • step_skipped: recrutador pulou etapa opcional     │   │
│  │ • explanation_dismissed: fechou explicação rápido   │   │
│  │ • jd_imported: usou importação de JD                │   │
│  │ • time_spent: tempo em cada etapa                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 20.2 WizardFeedback Model

**Arquivo**: `lia-agent-system/app/models/feedback_learning.py`

```python
class WizardFeedback(Base):
    """
    Registro de feedback para aprendizado do wizard.
    """
    __tablename__ = "wizard_feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    feedback_type = Column(String(50))  # "correction", "acceptance", "skip"
    field_name = Column(String(100), nullable=True)
    
    original_value = Column(JSON)
    final_value = Column(JSON)
    
    context = Column(JSON)  # job context quando feedback foi dado
    
    response_time_ms = Column(Integer, nullable=True)
    confidence_at_suggestion = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class JobOutcome(Base):
    """
    Registro de outcomes de vagas para correlação.
    """
    __tablename__ = "job_outcomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    outcome_type = Column(String(50))  # "filled", "cancelled", "expired"
    
    time_to_fill_days = Column(Integer, nullable=True)
    candidates_received = Column(Integer, nullable=True)
    candidates_qualified = Column(Integer, nullable=True)
    interviews_conducted = Column(Integer, nullable=True)
    
    hire_quality_score = Column(Float, nullable=True)  # 1-5
    recruiter_satisfaction = Column(Float, nullable=True)  # 1-5
    
    job_snapshot = Column(JSON)  # snapshot do job no momento do outcome
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 21. Histórico de Mudanças

### Versão 6.1 - Fevereiro 2026 (Consolidação PLANO_IMPLEMENTACAO_WIZARD.md)
- ✅ **Consolidação PLANO_IMPLEMENTACAO_WIZARD.md**: Todas as informações de implementação do Smart Wizard incorporadas
- ✅ **Seção 30.5**: Serviços Backend Existentes (NÃO REIMPLEMENTAR) - 8 serviços com linhas
- ✅ **Seção 30.5**: Hooks Frontend Existentes - 8 hooks com status e linhas
- ✅ **Seção 30.5**: Componentes Frontend Existentes - 7 componentes
- ✅ **Seção 30.6**: Fases de Implementação do Wizard (9 fases, todas ✅ CONCLUÍDAS)
- ✅ **Quality Gates WSI**: Thresholds e fórmulas de cálculo (70 pontos mínimo)
- ✅ **Orquestrador Unificado**: Interface OrchestratorResult e mapeamentos
- ✅ **Tool Calling**: Intent-to-Tool mappings e fluxo de execução
- ✅ **Memória Conversacional**: Formato de contexto injetado e funcionalidades
- ✅ **Testes E2E e WCAG**: Acessibilidade e polish visual documentados
- ✅ **Índice Atualizado**: 29 seções numeradas + apêndices

### Versão 6.0 - Fevereiro 2026 (Reorganização + Fast Track Completo)
- ✅ **Reorganização Estrutural**: Documento dividido em 5 partes lógicas (Visão Geral, Modelo de Dados, Wizard, Learning Loop, Arquitetura Técnica)
- ✅ **Consolidação PLANO_FAST_TRACK_WIZARD.md**: Todas as informações de implementação Fast Track incorporadas
- ✅ **Seção 29 Expandida**: Status de implementação das 5 fases, fluxo completo (7 etapas), campos sensíveis, regeneração WSI, pré-qualificação global, analytics events
- ✅ **Seção 33.5 Expandida**: Cache e Otimização de Tokens (4 camadas, 56% economia, prompt caching Anthropic)
- ✅ **Índice Atualizado**: Nova estrutura com numeração lógica por parte
- ✅ **Arquivos Principais**: Tabelas atualizadas de arquivos backend/frontend Fast Track
- ✅ **Métricas de Sucesso**: Tabela com baseline, target e status de medição

### Versão 4.1 - Janeiro 2026 (Learning Hub)
- ✅ **Seção 25.9**: Sistema de Aprendizado Unificado (Learning Hub)
- ✅ **Catálogos Dinâmicos**: `suggest_skills_with_learning()` e `suggest_responsibilities_with_learning()`
- ✅ **Endpoints de Learning**: `/lia/learning/confirm-skill`, `/confirm-responsibility`, `/context`
- ✅ **Stages 8-10**: Integração com Sourcing Agent e WSI Evaluator
- ✅ **Testes de Integração**: 13 testes validando o learning loop completo
- ✅ **Documentação AUDITORIA_WIZARD_AGENTES.md**: Atualizada com Phase 4 completo

### Versão 4.0 - Janeiro 2026 (Consolidação)
- ✅ **Consolidação documental**: Unificação de 4 documentos em um único arquivo abrangente
- ✅ **Seção 24**: Estrutura Completa do Wizard (3 Fases, 7 Etapas) - consolidado de `FLUXO_WIZARD_VAGA_COMPLETO.md`
- ✅ **Seção 25**: Mapeamento de Configurações da Empresa - consolidado de `SETTINGS_MENU_MAPPING_FOR_WIZARD.md`
- ✅ **Seção 26**: Sistema de Análise Proativa da LIA - consolidado de `LIA_PROACTIVE_ANALYSIS_SYSTEM.md`
- ✅ **Seção 27**: Próximos Passos (Clustering e Embeddings) - consolidado de `clustering-embeddings-proposal.md`
- ✅ Interfaces TypeScript completas para todas as etapas do wizard
- ✅ Diagramas ASCII de fluxo de dados e análise de compensação
- ✅ Tabelas de mapeamento Wizard ↔ Configurações
- ✅ Catálogo de Skills detalhado por área e senioridade
- ✅ Perguntas de Screening categorizadas

### Versão 3.0 - Janeiro 2026
- ✅ Implementação completa da Intelligence Layer
- ✅ Implementação completa da Personalização por Recrutador
- ✅ Integração do intelligence_layer_service com job_intake_agent
- ✅ Integração do recruiter_personalization_service com job_intake_agent
- ✅ Criação de API endpoints para Intelligence Layer
- ✅ Criação de API endpoints para Recruiter Profiles
- ✅ Modelos de dados alinhados com schema do banco
- ✅ Remoção de PersonalizationEvent (substituído por WizardFeedback)
- ✅ Atualização do RecruiterProfile para schema compatível

### Versão 2.0 - Janeiro 2026
- ✅ Implementação de JobDraft
- ✅ Implementação de FieldTypology
- ✅ Implementação de ConfidencePolicyService
- ✅ Implementação de SkillsCatalogService
- ✅ Criação de API endpoints para Job Drafts
- ✅ Integração com frontend

### Versão 1.0 - Dezembro 2025
- Documentação inicial do plano
- Análise de arquitetura existente
- Definição de fases de implementação

---

## Conclusão das Fases 1-6 (Janeiro 2026)

### Status Final das Fases

Todas as fases planejadas foram implementadas com sucesso:

| Fase | Descrição | Status | Data Conclusão |
|------|-----------|--------|----------------|
| **Fase 1** | Tipologia de Campos e JobDraft | ✅ Implementado | Jan 2026 |
| **Fase 2** | Níveis de Confiança e Catálogo de Skills | ✅ Implementado | Jan 2026 |
| **Fase 3** | Intelligence Layer | ✅ Implementado | Jan 2026 |
| **Fase 4** | Personalização por Recrutador | ✅ Implementado | Jan 2026 |
| **Fase 5** | Feedback Learning Loop | ✅ Implementado | Jan 2026 |
| **Fase 6** | Consolidação do Wizard (10→7 etapas) | ✅ Implementado | 25 Jan 2026 |

### Nova Estrutura do Wizard: 7 Etapas

O wizard foi consolidado de 10 para 7 etapas para melhor experiência do usuário:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   WIZARD DE CRIAÇÃO DE VAGA - ESTRUTURA FINAL               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FASE: CONSTRUÇÃO (5 etapas)                                                │
│  ├── 1. input-evaluation     ← Nova etapa com análise proativa              │
│  │       └── CompensationAnalysisPanel integrado                            │
│  ├── 2. job-description      ← Renomeado de basic-info                      │
│  ├── 3. competencies         ← Mantido                                      │
│  ├── 4. salary               ← Aprimorado com sugestões da análise          │
│  └── 5. wsi-questions        ← Mantido                                      │
│                                                                              │
│  FASE: ATIVAÇÃO (1 etapa)                                                   │
│  └── 6. review-publish       ← Consolidação de review + pre-publish         │
│                                                                              │
│  FASE: SELEÇÃO (1 etapa)                                                    │
│  └── 7. search-calibration   ← Consolidação de 3 etapas anteriores          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Decisões de Implementação

#### 22.3.1 Análise Proativa de Compensação

**Decisão:** Integrar análise de compensação na primeira etapa do wizard (input-evaluation).

**Justificativa:**
- Recrutador tem visibilidade imediata de benchmarks salariais
- Decisões de remuneração são informadas desde o início
- Reduz retrabalho na etapa de salário

**Implementação:**
- `CompensationAnalysisService` fornece dados de benchmark interno + mercado
- `CompensationAnalysisPanel` exibe análise visual no painel lateral
- Integração com `MarketBenchmarkService` para dados externos

#### 22.3.2 Consolidação de Etapas (10→7)

**Decisão:** Reduzir de 10 para 7 etapas consolidando etapas logicamente relacionadas.

**Justificativa:**
- Menos etapas = experiência mais fluida
- Etapas de revisão + publicação são naturalmente sequenciais
- Busca + calibração + kanban são parte do mesmo fluxo

**Mapeamento:**
| Etapas Anteriores | Nova Etapa |
|-------------------|------------|
| description | input-evaluation (expandido) |
| basic-info | job-description (renomeado) |
| competencies | competencies |
| salary | salary (aprimorado) |
| wsi-questions | wsi-questions |
| review + pre-publish | review-publish |
| candidate-search + calibration + active-search | search-calibration |

#### 22.3.3 Serviços Integrados

**Decisão:** Criar camada de serviços especializados para cada responsabilidade.

**Serviços Implementados:**
- **IntelligenceLayerService** - Detecção de padrões e correlações
- **MarketBenchmarkService** - Dados de mercado (salários, skills)
- **CompanyConfigurationService** - Defaults da empresa
- **CompensationAnalysisService** - Análise proativa de remuneração
- **SkillsCatalogService** - Catálogo de competências por área
- **RecruiterPersonalizationService** - Personalização por usuário
- **ConfidencePolicyService** - Cálculo de confiança para inferências

### Arquivos Criados/Modificados

#### Backend (lia-agent-system/app/)

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `models/job_draft.py` | ✅ Criado | JobDraft, DraftFieldHistory |
| `models/recruiter_profile.py` | ✅ Criado | RecruiterProfile, RecruiterFieldPreference, PersonalizationSettings |
| `models/feedback_learning.py` | ✅ Criado | WizardFeedback, JobOutcome |
| `schemas/field_typology.py` | ✅ Criado | FieldTypology enum, FieldDefinition |
| `services/confidence_policy_service.py` | ✅ Criado | Cálculo de confiança determinístico |
| `services/skills_catalog_service.py` | ✅ Criado | Catálogo de skills por área |
| `services/intelligence_layer_service.py` | ✅ Criado | Pattern Detection, Suggestions |
| `services/recruiter_personalization_service.py` | ✅ Criado | Personalização por recrutador |
| `services/compensation_analysis_service.py` | ✅ Criado | Análise proativa de compensação |
| `api/v1/intelligence.py` | ✅ Criado | Endpoints de inteligência |
| `api/v1/recruiter_profiles.py` | ✅ Criado | Endpoints de perfil do recrutador |
| `api/v1/job_drafts.py` | ✅ Criado | Endpoints de draft de vaga |
| `agents/specialized/job_intake_agent.py` | ✅ Modificado | Integração com novos serviços |

#### Frontend (plataforma-lia/src/)

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `components/expanded-chat-modal.tsx` | ✅ Modificado | Novo fluxo 7 etapas |
| `components/job-creation/CompensationAnalysisPanel.tsx` | ✅ Criado | Painel de análise de compensação |
| `hooks/use-job-wizard-backend.ts` | ✅ Modificado | Suporte a nova estrutura |
| `hooks/use-wizard-auto-save.ts` | ✅ Criado | Auto-save de rascunho |
| `hooks/use-compensation-analysis.ts` | ✅ Criado | Hook para análise de compensação |
| `components/ui/field-confidence-indicator.tsx` | ✅ Criado | Indicador visual de confiança |
| `components/ui/field-origin-badge.tsx` | ✅ Criado | Badge de origem do campo |

#### Documentação (docs/)

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `FLUXO_WIZARD_VAGA_COMPLETO.md` | ✅ Atualizado | Nova estrutura 7 etapas documentada |
| `proposals/job-wizard-enhancement-plan.md` | ✅ Atualizado | Seção de conclusão adicionada |

### Métricas de Sucesso Esperadas

| Métrica | Baseline | Meta | Status |
|---------|----------|------|--------|
| Tempo médio de criação de vaga | ~15 min | < 8 min | 🎯 A medir |
| Taxa de abandono do wizard | ~25% | < 10% | 🎯 A medir |
| Campos corrigidos manualmente | ~40% | < 15% | 🎯 A medir |
| Satisfação do recrutador (NPS) | - | > 50 | 🎯 A medir |

### Próximos Passos (Backlog)

Funcionalidades para futuras iterações:

1. **Dashboard de Analytics do Wizard** - Visualização de métricas de uso e abandono
2. **Integração de feedback learning em tempo real** - Ajuste de sugestões durante a sessão
3. **Divisão do componente monolítico** - Separar expanded-chat-modal.tsx em componentes menores
4. **A/B Testing Framework** - Testar variações de fluxo para otimização
5. **Integração com mais plataformas de publicação** - Indeed, Catho, Glassdoor

### Considerações Finais

A implementação do plano de aprimoramento do wizard foi concluída com sucesso, alcançando os seguintes objetivos:

1. ✅ **Experiência do Recrutador** - Fluxo mais fluido com menos etapas e análise proativa
2. ✅ **Defaults Inteligentes** - Campos pré-preenchidos com base em tipologia e configurações
3. ✅ **Rastreabilidade** - JobDraft permite acompanhar todo o ciclo de vida do rascunho
4. ✅ **Personalização** - Experiência adaptada por recrutador com base em histórico
5. ✅ **Intelligence Layer** - Sugestões contextuais baseadas em padrões e outcomes
6. ✅ **Feedback Learning** - Infraestrutura para aprendizado contínuo implementada

A documentação detalhada do fluxo está disponível em `docs/FLUXO_WIZARD_VAGA_COMPLETO.md`.

---

## 22. Sistema de Geração de Job Description

### 22.1 Duas Versões de JD

O wizard gera duas versões distintas de Job Description em português:

| Versão | Propósito | Inclui Interview Process? |
|--------|-----------|---------------------------|
| **JD Preview (v1)** | Validação após coleta inicial | ❌ Não |
| **JD Final (v2)** | Publicação final | ✅ Sim |

### 22.2 JD Preview (v1)

Exibida após a etapa de coleta de informações para validação:
- Indicadores visuais de sugestões da LIA (💡)
- Alertas de compensação (⚠️)
- Comparativo de mercado (percentil salarial)
- Score de completude

### 22.3 JD Final (v2)

Versão completa para publicação:
- Todas as informações consolidadas
- Timeline do processo seletivo
- Link de candidatura
- Sem indicadores de sugestão (versão limpa)

### 22.4 Seções do JD (Português)

1. Sobre a Empresa
2. A Vaga
3. O Que Você Vai Fazer
4. O Que Buscamos
5. Requisitos Obrigatórios
6. Diferenciais
7. Por Que Trabalhar Conosco
8. Remuneração
9. Nossos Valores
10. Processo Seletivo (apenas v2)
11. Diversidade e Inclusão

### 22.5 Implementação

**Backend:**
- `app/schemas/job_description.py`: Schemas Pydantic para JD Preview e Final
- `app/services/jd_template_service.py`: JDTemplateService com generate_preview() e generate_final()

**Frontend:**
- `components/job-description/types.ts`: TypeScript types
- `components/job-description/JobDescriptionPreview.tsx`: Renderiza v1
- `components/job-description/JobDescriptionFinal.tsx`: Renderiza v2

---

## 23. Sistema de Interação com Sugestões via Chat

### 23.1 Visão Geral

Permite que recrutadores interajam com sugestões da LIA via linguagem natural no chat, além dos botões do painel.

### 23.2 Tipos de Interação Suportados

| Tipo | Exemplos | Ação |
|------|----------|------|
| **ACCEPT** | "pode adicionar Docker", "aceito Machine Learning" | Adiciona skill à lista |
| **REJECT** | "não preciso de Kubernetes", "remova SQL" | Remove skill da lista |
| **REPLACE** | "troque Docker por Podman", "prefiro Vue ao invés de React" | Substitui skill |
| **ADJUST_LEVEL** | "Docker como diferencial", "Python é obrigatório" | Altera nível (required/nice_to_have) |
| **CLARIFY** | "por que você sugeriu Machine Learning?" | Explica razão da sugestão |

### 23.3 Detecção de Intenção

O sistema usa detecção via regex otimizado para:
- Skills de uma palavra: Python, Docker, AWS
- Skills multi-palavra: Machine Learning, Power BI, Data Science
- Combinações: "aceito Python e Docker, mas remova Java"

### 23.4 Fluxo de Processamento

```
Recrutador → "Aceito Docker mas troque React por Vue"
     │
     ▼
SuggestionInteractionService.detect_interactions()
     │
     ├── ACCEPT: Docker
     └── REPLACE: React → Vue
     │
     ▼
apply_interactions() → Atualiza suggested_skills no estado
     │
     ▼
generate_confirmation_message() → "✅ Adicionei Docker. 🔄 Substituí React por Vue."
```

### 23.5 Implementação

**Backend:**
- `app/schemas/suggestion_interaction.py`: Schemas para tipos de interação
- `app/services/suggestion_interaction_service.py`: Serviço com detect_interactions(), apply_interactions(), generate_confirmation_message()

**Integração:**
- `job_intake_agent.py`: Processa interações durante _handle_conversational_job_creation

---

# PARTE 3: WIZARD DE CRIAÇÃO DE VAGAS

---

## 24. Estrutura Completa do Wizard (3 Fases, 7 Etapas)

> **Consolidado de:** `docs/FLUXO_WIZARD_VAGA_COMPLETO.md`

### 24.1 Visão Geral do Fluxo

O wizard de criação de vagas é organizado em **3 Fases** com **7 Etapas**:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        WIZARD DE CRIAÇÃO DE VAGA v3.0                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  FASE 1: CONSTRUÇÃO          FASE 2: ATIVAÇÃO        FASE 3: SELEÇÃO          │
│  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │ 1. input-evaluation │    │                  │    │                       │ │
│  │ 2. job-description  │───▶│ 6. review-publish│───▶│ 7. search-calibration │ │
│  │ 3. competencies     │    │                  │    │                       │ │
│  │ 4. salary           │    │                  │    │                       │ │
│  │ 5. wsi-questions    │    │                  │    │                       │ │
│  └─────────────────────┘    └──────────────────┘    └───────────────────────┘ │
│                                                                                 │
│  Serviços Integrados:                                                          │
│  ├── IntelligenceLayerService        ├── CompensationAnalysisService          │
│  ├── MarketBenchmarkService          ├── SkillsCatalogService                 │
│  ├── CompanyConfigurationService     ├── RecruiterPersonalizationService      │
│  └── ConfidencePolicyService                                                   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 24.2 Tipos e Interfaces do Wizard

```typescript
type WizardStage = 'input-evaluation' | 'job-description' | 'competencies' | 
                   'salary' | 'wsi-questions' | 'review-publish' | 'search-calibration'

type WizardPhase = 'construction' | 'activation' | 'selection'

const WIZARD_PHASES: WizardPhaseConfig[] = [
  { 
    id: 'construction', 
    label: 'Construção', 
    stages: ['input-evaluation', 'job-description', 'competencies', 'salary', 'wsi-questions'] 
  },
  { 
    id: 'activation', 
    label: 'Ativação', 
    stages: ['review-publish'] 
  },
  { 
    id: 'selection', 
    label: 'Seleção', 
    stages: ['search-calibration'] 
  }
]
```

### 24.3 FASE 1: CONSTRUÇÃO (5 Etapas)

#### Etapa 1: Input & Evaluation (`input-evaluation`)

| Campo | Descrição |
|-------|-----------|
| **Título** | Entrada & Avaliação |
| **Painel** | CriteriaDetectedPanel, CompensationAnalysisPanel |
| **Funcionalidades** | Detecção automática de campos, análise proativa de compensação |

**Interface CompensationAnalysis:**
```typescript
interface CompensationAnalysis {
  internalBenchmark: {
    minSalary: number; maxSalary: number; avgSalary: number;
    sampleSize: number; similarRoles: string[]
  }
  marketBenchmark: {
    p25: number; p50: number; p75: number; p90: number;
    source: string; updatedAt: string
  }
  recommendation: {
    minSuggested: number; maxSuggested: number; percentile: number;
    competitiveness: 'below_market' | 'at_market' | 'above_market';
    alerts: string[]
  }
}
```

#### Etapa 2: Job Description (`job-description`)

| Campo | Tipologia | Origem |
|-------|-----------|--------|
| `job_title` | CRITICAL | Detectado/Manual |
| `seniority` | CRITICAL | Inferido/Manual |
| `department` | PROBABLE | Detectado/Default empresa |
| `location` | PROBABLE | Detectado/Default empresa |
| `work_model` | PROBABLE | Default empresa |
| `employment_type` | PROBABLE | Default empresa |

```typescript
interface JobDescriptionData {
  job_title: string
  seniority: 'junior' | 'pleno' | 'senior' | 'specialist' | 'lead' | 'manager' | 'director'
  department: string
  location: string
  work_model: 'presencial' | 'hibrido' | 'remoto'
  employment_type: 'clt' | 'pj' | 'estagio' | 'temporario'
  manager?: string
  responsibilities?: string[]
  field_origins: Record<string, FieldOrigin>
}
```

#### Etapa 3: Competências (`competencies`)

**Interfaces:**
```typescript
interface TechnicalSkill {
  id: string; name: string;
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'methodology'
  weight: number // 1-5
  source: 'catalog' | 'detected' | 'manual'
}

interface BehavioralCompetency {
  id: string; name: string; weight: number // 1-5
  justification: string; enabled: boolean
  source: 'catalog' | 'detected' | 'manual'
}
```

**Catálogo de Skills por Área:**

| Área | Skills Técnicas | Skills Comportamentais |
|------|-----------------|------------------------|
| Engineering | Python, Java, Node.js, React, TypeScript, SQL, Docker, AWS, Kubernetes | Resolução de Problemas, Pensamento Analítico, Colaboração |
| Finance | Excel Avançado, Power BI, SAP, IFRS, Modelagem Financeira | Atenção a Detalhes, Gestão de Risco, Comunicação |
| HR | R&S, ATS, LinkedIn Recruiter, Entrevistas por Competências | Empatia, Escuta Ativa, Negociação |
| Marketing | SEO, SEM, Google Ads, Analytics, Copywriting | Criatividade, Orientação a Dados, Adaptabilidade |
| Sales | Vendas Consultivas, CRM, Salesforce, HubSpot, Negociação B2B | Persuasão, Resiliência, Foco em Resultados |

#### Etapa 4: Remuneração (`salary`)

```typescript
interface SalaryInfo {
  minSalary: number; maxSalary: number;
  suggestedMin: number; suggestedMax: number;
  minBonus: number; maxBonus: number; bonusCriteria: string;
  benefits: Benefit[];
  marketPosition: 'below' | 'at' | 'above'; percentile: number
}

interface Benefit {
  id: string; name: string; value?: string;
  enabled: boolean; source: 'company_default' | 'manual'
}
```

#### Etapa 5: Triagem WSI (`wsi-questions`)

```typescript
interface WSIQuestion {
  id: string; question: string;
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean; options?: string[];
  expectedAnswer?: string | number | boolean;
  batch: number // 1, 2, 3 para envio gradual
  category?: 'technical' | 'behavioral' | 'situacional' | 'fit'
  source: 'company_default' | 'job_specific' | 'auto_generated'
}
```

### 24.4 FASE 2: ATIVAÇÃO

#### Etapa 6: Revisão e Publicação (`review-publish`)

**Plataformas de Publicação:**
```typescript
interface PublishingPlatform {
  id: string; name: string; icon: string;
  enabled: boolean; connected: boolean; estimatedReach: number
}

const AVAILABLE_PLATFORMS: PublishingPlatform[] = [
  { id: 'linkedin', name: 'LinkedIn Jobs', enabled: true, connected: true, estimatedReach: 5000 },
  { id: 'site', name: 'Site Carreiras', enabled: true, connected: true, estimatedReach: 1000 },
  { id: 'gupy', name: 'Gupy', enabled: false, connected: false, estimatedReach: 3000 },
  { id: 'indeed', name: 'Indeed', enabled: false, connected: false, estimatedReach: 8000 }
]
```

### 24.5 FASE 3: SELEÇÃO

#### Etapa 7: Busca e Calibração (`search-calibration`)

```typescript
interface CalibrationCandidate {
  id: string; name: string; photoUrl?: string; linkedinUrl?: string;
  currentRole: string; currentCompany: string; location: string;
  overallScore: number;
  highlights: { icon: string; label: string; value: string }[]
  matchCriteria: CalibrationMatchCriteria[]
}

interface CalibrationMatchCriteria {
  label: string; matched: boolean; value?: string; weight: number
}
```

**Fluxo de Calibração:**
```
1. Busca Inicial (base local + Pearch AI)
     │
     ▼
2. Seleção para Calibração (1-5 candidatos)
     │
     ▼
3. Recrutador avalia cada candidato
     ├── ✅ Aprovar → Adiciona ao kanban + feedback positivo
     └── ❌ Rejeitar → Feedback negativo + motivo
     │
     ▼
4. RecruiterPersonalizationService registra preferências
     │
     ▼
5. Busca refinada com perfil calibrado
```

### 24.6 Migração do Fluxo (10 → 7 etapas)

| Fluxo Anterior (10 etapas) | Novo Fluxo (7 etapas) | Mudança |
|---------------------------|----------------------|---------|
| 1. description | 1. input-evaluation | Expandido com análise proativa |
| 2. basic-info | 2. job-description | Renomeado |
| 3. competencies | 3. competencies | Mantido |
| 4. salary | 4. salary | Aprimorado com sugestões |
| 5. wsi-questions | 5. wsi-questions | Mantido |
| 6. review + 7. pre-publish | 6. review-publish | **Consolidado** |
| 8-10. candidate-search/calibration/active-search | 7. search-calibration | **Consolidado** |

---

## 25. Mapeamento de Configurações da Empresa

> **Consolidado de:** `docs/SETTINGS_MENU_MAPPING_FOR_WIZARD.md`  
> **Documento Atualizado:** A versão mais recente e detalhada está em `docs/SETTINGS_MENU_MAPPING_FOR_WIZARD.md` (v2.0 - 28/Jan/2026)

### 25.1 Estrutura do Menu Configurações

```
🏢 Empresa & Equipe
├── Dados da Empresa ──────── "company-data"
│   ├── Informações Básicas
│   ├── Cultura e Identidade  
│   ├── Tech Stack
│   ├── Big Five da Empresa
│   └── Idiomas Padrão
├── Informações Estratégicas ── "strategic-info"
├── Departamentos ──────────── "departments"
├── Benefícios ─────────────── "benefits"
└── Usuários ───────────────── "users"

⚙️ Recrutamento
├── Pipeline ───────────────── "pipeline"
├── Perguntas Screening ────── "screening"
├── Status de Candidatos ───── "candidate-statuses"
└── Solicitação de Dados ───── "data-requests"

📊 Planejamento
└── Planejamento de Contratações ─ Workforce Planning
```

### 25.2 CompanyData Interface Completa

```typescript
interface CompanyData {
  // === DADOS BÁSICOS ===
  name: string                    // Razão Social
  tradeName: string               // Nome Fantasia
  cnpj: string                    // CNPJ
  website: string                 // Site Institucional
  email: string                   // Email Principal
  phone: string                   // Telefone Principal
  address: string                 // Endereço Completo
  logo?: string                   // URL do Logo
  industry: string                // Setor/Indústria
  size: string                    // Porte (1-10, 11-50, etc.)
  employee_count?: number         // Número de funcionários
  locations?: string[]            // Filiais/Escritórios
  linkedin_url?: string           // LinkedIn da empresa

  // === CULTURA E IDENTIDADE ===
  mission?: string                // Missão
  vision?: string                 // Visão
  values?: string[]               // Lista de Valores
  coreCompetencies?: string[]     // Competências-chave
  work_model?: string             // Modelo: Híbrido/Remoto/Presencial
  evp_bullets?: string[]          // Employee Value Proposition
  dei_initiatives?: string        // Diversidade e Inclusão

  // === TECNOLOGIA ===
  tech_stack?: string[]           // Stack de tecnologia categorizado
  engineering_culture?: string    // Cultura de engenharia
  default_languages?: string[]    // Idiomas padrão da empresa

  // === BIG FIVE DA EMPRESA ===
  openness_score?: number         // Abertura (0-100)
  conscientiousness_score?: number // Conscienciosidade (0-100)
  extraversion_score?: number     // Extroversão (0-100)
  agreeableness_score?: number    // Amabilidade (0-100)
  stability_score?: number        // Estabilidade Emocional (0-100)

  // === DADOS ESTRATÉGICOS ===
  additional_data?: {
    hiring_volume?: number        // Volume mensal de contratações
    job_types?: string[]          // Tipos de vagas (CLT, PJ, etc.)
    current_ats?: string          // ATS atual
    main_challenges?: string[]    // Principais desafios de recrutamento
    main_priority?: string        // Prioridade principal
  }
}
```

### 25.3 Tech Stack Categorizado

| Categoria | Ícone | Sugestões Padrão |
|-----------|-------|------------------|
| **Backend** | Server | Node.js, Python, Java, .NET, Go, Ruby, PHP, Rust |
| **Frontend** | Layout | React, Vue.js, Angular, Next.js, Svelte, TypeScript |
| **Dados** | Database | PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch |
| **Cloud** | Cloud | AWS, Azure, GCP, Vercel, Heroku, DigitalOcean |
| **DevOps** | Settings | Docker, Kubernetes, Jenkins, GitHub Actions, Terraform |
| **IA/ML** | Brain | TensorFlow, PyTorch, OpenAI, Anthropic, LangChain |
| **ERPs** | Briefcase | SAP, Oracle, Totvs, Salesforce, Dynamics 365 |
| **Design** | Palette | Figma, Adobe XD, Sketch, InVision, Framer |
| **Mobile** | Smartphone | React Native, Flutter, Swift, Kotlin, iOS, Android |

### 25.4 Estrutura de Departamento

```typescript
interface Department {
  id: string; name: string; description: string;
  manager?: string; manager_title?: string;
  manager_email?: string; manager_phone?: string;
  headcount: number; color: string;
  members?: DepartmentMember[]
}

interface DepartmentMember {
  id: string; name: string; title?: string;
  email?: string; linkedin_url?: string;
  level: string; is_active: boolean
}
```

### 25.5 Estrutura de Benefício

```typescript
interface Benefit {
  id: string; name: string; description: string;
  category: string  // health, food, transport, education, financial, quality_life, family, security
  valueType: 'monetary' | 'percentage' | 'informative'
  value?: number
  seniorityLevel: string[]  // all, junior, pleno, senior, coordinator, manager, director, c-level
  waitingPeriod: number     // Dias de carência
  isHighlighted: boolean
  isActive: boolean
}
```

### 25.6 Pipeline e Etapas Padrão

| Ordem | Etapa | Tipo | SLA | Responsável |
|-------|-------|------|-----|-------------|
| 1 | Triagem Automática | screening | 24h | LIA |
| 2 | Triagem Manual | screening | 48h | Recrutador |
| 3 | Teste Técnico | test | 72h | Equipe Técnica |
| 4 | Assessment/Dinâmica | assessment | 24h | RH/Psicólogo |
| 5 | Entrevista RH | interview | 48h | Recrutador |
| 6 | Entrevista Técnica | interview | 72h | Tech Lead |
| 7 | Entrevista com Gestor | interview | 48h | Gestor |
| 8 | Case/Desafio | case | 120h | Equipe |
| 9 | Verificação de Referências | reference | 48h | RH |
| 10 | Aprovação Final | approval | 72h | Comitê |
| 11 | Proposta/Oferta | offer | 24h | RH |

### 25.7 Perguntas de Screening por Categoria

#### Elegibilidade e Requisitos Legais
| Pergunta | Tipo | Contexto |
|----------|------|----------|
| Você se identifica com o grupo elegível? | yesno | Vagas afirmativas |
| Você possui CNH válida? | yesno + text | Vagas com habilitação |
| Qual categoria da sua CNH? | multiple | Motoristas |
| Você possui passaporte válido? | yesno | Viagens internacionais |

#### Disponibilidade e Mobilidade
| Pergunta | Tipo | Contexto |
|----------|------|----------|
| Disponibilidade para viagens frequentes? | yesno | Comercial, consultoria |
| Aceita trabalho em turnos/escalas? | yesno | Operações, indústria |
| Pode iniciar imediatamente? | text | Urgência |

#### Formação e Certificações
| Pergunta | Tipo | Contexto |
|----------|------|----------|
| Possui formação superior completa? | yesno | Vagas com diploma |
| Qual sua área de formação? | text | Seguimento |
| Possui certificação [X] válida? | yesno | PMP, AWS, CPA |

### 25.8 Mapeamento Wizard ↔ Configurações

| Etapa do Wizard | Campos Pré-preenchidos | Fonte |
|-----------------|----------------------|-------|
| **Etapa 1 - Detecção** | Modelo de trabalho, localização | `CompanyData.work_model`, `locations` |
| **Etapa 2 - Básicas** | Departamento, Gestor, Localização | `departments[]`, `managers[]`, `headquarters` |
| **Etapa 3 - Técnicos** | Sugestões de stack, Idiomas | `tech_stack[]`, `default_languages[]` |
| **Etapa 4 - Comportamentais** | Valores, Competências, Big Five | `values[]`, `coreCompetencies[]`, `*_score` |
| **Etapa 5 - Benefícios** | Benefícios ativos | `BenefitsTab` com filtro por senioridade |
| **Etapa 6 - Triagem** | Perguntas padrão | `screening_questions[]` |
| **Etapa 7 - Entrevistas** | Pipeline completo | `recruitment_stages[]` |
| **Etapas 8-10 - Sourcing** | Skills promovidas, Cutoffs calibrados | `LearningHub.get_learning_context()` |

### 25.9 Sistema de Aprendizado Unificado (Learning Hub)

> **Atualizado:** Janeiro 2026 - Phase 4 Completo

O wizard agora integra um sistema de aprendizado que melhora sugestões baseado no histórico da empresa:

#### Fluxo de Aprendizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED LEARNING SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WIZARD STAGE 1                LEARNING HUB                    AGENTS       │
│  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────┐  │
│  │ Recrutador      │          │ LearningHub     │          │ Sourcing    │  │
│  │ confirma/rejeita│─────────▶│ Service         │◀─────────│ Agent       │  │
│  │ skills/resps    │          │                 │          │             │  │
│  │                 │          │ • record_skill  │          │ WSI         │  │
│  │ POST /learning/ │          │ • record_resp   │          │ Evaluator   │  │
│  │ confirm-skill   │          │ • get_context   │          └─────────────┘  │
│  └─────────────────┘          └────────┬────────┘                           │
│                                        │                                     │
│                                        ▼                                     │
│                     ┌─────────────────────────────────────┐                  │
│                     │           DATABASE                  │                  │
│                     │ • CompanySkill (promoted após 3x)   │                  │
│                     │ • CompanyResponsibility (hash dedup)│                  │
│                     │ • AgentFeedback (histórico)         │                  │
│                     │ • CompanyPattern (padrões)          │                  │
│                     └─────────────────────────────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Catálogos Dinâmicos (por Empresa)

| Catálogo | Tabela | Promoção | Benefício |
|----------|--------|----------|-----------|
| **Skills Dinâmicas** | `company_skills` | Após 3 confirmações | Sugestões personalizadas por empresa |
| **Responsabilidades** | `company_responsibilities` | Hash SHA256 dedup | Evita repetição, melhora qualidade |
| **Padrões** | `company_patterns` | Detecção automática | "77% das vagas são híbridas" |

#### Novos Métodos nos Catálogos

```python
# SkillsCatalogService - agora com learning
async def suggest_skills_with_learning(
    db: AsyncSession,
    company_id: str,
    role: str,
    seniority: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Retorna:
    - technical_skills: Lista mesclada (dinâmicas + estáticas)
    - company_learned_skills: Skills promovidas da empresa
    - source_mix: {"dynamic": 3, "static": 7}
    """

# ResponsibilitiesCatalogService - agora com learning
async def suggest_responsibilities_with_learning(
    db: AsyncSession,
    company_id: str,
    role: str,
    seniority: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Retorna responsabilidades mescladas priorizando aprendidas
    """
```

#### Endpoints de Learning

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/lia/learning/confirm-skill` | POST | Registra confirmação/rejeição de skill |
| `/lia/learning/confirm-responsibility` | POST | Registra responsabilidade (com dedup) |
| `/lia/learning/context` | POST | Retorna contexto de learning da empresa |

#### Stages 8-10 com Agentes

| Stage | Endpoint | Agente | Learning |
|-------|----------|--------|----------|
| 8 | `/wizard/stage8/search` | Sourcing Agent | Usa skills promovidas em buscas |
| 8 | `/wizard/stage8/feedback` | - | Registra feedback de seleções |
| 9 | `/wizard/stage9/evaluate` | WSI Evaluator | Usa cutoffs calibrados |
| 9 | `/wizard/stage9/calibrate` | - | Ajusta cutoffs por padrões |
| 10 | `/wizard/stage10/start-sourcing` | Sourcing Agent | Sourcing proativo |
| 10 | `/wizard/stage10/outreach` | - | Outreach automatizado |
| 10 | `/wizard/stage10/feedback` | - | Registra taxas de engajamento |

#### Isolamento Multi-Tenant

Todos os dados de learning são isolados por `company_id`:
- Skills de Empresa A **nunca** aparecem para Empresa B
- Padrões são calculados apenas com dados históricos da própria empresa
- Feedback de agentes é segregado por empresa

---

## 26. Sistema de Análise Proativa da LIA

> **Consolidado de:** `docs/LIA_PROACTIVE_ANALYSIS_SYSTEM.md`

### 26.1 Visão Geral do Sistema

O Wizard utiliza uma **camada de inteligência proativa** que analisa informações em tempo real:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE ANÁLISE PROATIVA DA LIA                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────────────────────────────────┐  │
│  │ Descrição do     │     │              SERVIÇOS DE ANÁLISE             │  │
│  │ Recrutador       │────▶│                                              │  │
│  │                  │     │  ┌────────────────────────────────────────┐  │  │
│  │ "Preciso de um   │     │  │ IntelligenceLayerService               │  │  │
│  │  Dev Python      │     │  │ - Detecção de padrões                  │  │  │
│  │  Sênior para     │     │  │ - Correlação de outcomes               │  │  │
│  │  Dados em SP"    │     │  │ - Sugestões contextuais                │  │  │
│  └──────────────────┘     │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ SkillsCatalogService                   │  │  │
│                           │  │ - Catálogo de skills por área          │  │  │
│                           │  │ - Mapeamento cargo → competências      │  │  │
│                           │  │ - Ajuste por senioridade               │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ CompensationAnalysisService            │  │  │
│                           │  │ - Política salarial da empresa         │  │  │
│                           │  │ - Benchmark de mercado                 │  │  │
│                           │  │ - Total Compensation                   │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ MarketBenchmarkService                 │  │  │
│                           │  │ - Pesquisa web de salários             │  │  │
│                           │  │ - Tendências de mercado                │  │  │
│                           │  │ - Skills em demanda                    │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           └──────────────────────────────────────────────┘  │
│                                               │                              │
│                                               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    PARECER DA LIA (EvaluationResponse)               │   │
│  │  • detected_fields: {title, seniority, department, skills...}        │   │
│  │  • completeness_score: 85%                                           │   │
│  │  • compensation_analysis: {salary, bonus, benefits, total_comp}      │   │
│  │  • suggestions: [{field, suggested, reason, source}...]              │   │
│  │  • recommended_action: "proceed" | "review_compensation" | "missing" │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 26.2 Catálogo de Skills Detalhado

```python
TECH_SKILLS_CATALOG = {
    "engineering": {
        "backend": ["Python", "Java", "Node.js", "Go", "Ruby", "C#", ".NET"],
        "frontend": ["React", "Vue.js", "Angular", "TypeScript", "Next.js"],
        "devops": ["Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform"],
        "data": ["SQL", "PostgreSQL", "MongoDB", "Redis", "Spark", "Airflow"],
        "ai_ml": ["Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch"]
    },
    "finance": {
        "accounting": ["IFRS", "GAAP", "SAP FI/CO", "Contabilidade Geral"],
        "fp_a": ["Orçamento", "Forecast", "Power BI", "Excel Avançado"]
    }
}

BEHAVIORAL_COMPETENCIES_CATALOG = {
    "leadership": {
        "name": "Liderança",
        "subcategories": ["Liderança de Equipe", "Desenvolvimento de Pessoas", "Tomada de Decisão"]
    },
    "problem_solving": {
        "name": "Resolução de Problemas",
        "subcategories": ["Pensamento Analítico", "Pensamento Crítico", "Inovação"]
    }
}

# Mapeamento Cargo → Skills
ROLE_SKILLS_MAPPING = {
    "desenvolvedor backend": {
        "area": "engineering", 
        "category": "backend", 
        "behavioral": ["problem_solving", "collaboration"]
    },
    "cientista de dados": {
        "area": "engineering", 
        "category": "ai_ml", 
        "behavioral": ["problem_solving", "communication"]
    }
}

# Ajuste por Senioridade
SENIORITY_SKILL_COUNTS = {
    "junior": {"min": 3, "max": 5},
    "pleno": {"min": 5, "max": 8},
    "senior": {"min": 8, "max": 12},
    "lead": {"min": 10, "max": 15}
}
```

### 26.3 Análise de Compensação Completa

```
┌─────────────────────────────────────────────────────────────────┐
│              FLUXO DE ANÁLISE DE COMPENSAÇÃO                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT: Dev Python Sênior, São Paulo, Tecnologia                │
│         Proposta: R$ 15.000 - R$ 20.000                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 1. POLÍTICA DA EMPRESA (CompensationPolicy)                 ││
│  │    • salary_min: R$ 14.000                                   ││
│  │    • salary_max: R$ 22.000                                   ││
│  │    • bonus_target: 15%                                       ││
│  │    • Status: ✅ DENTRO DA POLÍTICA                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 2. BENCHMARK DE MERCADO (MarketBenchmarkService)            ││
│  │    • Mediana: R$ 18.000                                      ││
│  │    • Percentil 25: R$ 14.000                                 ││
│  │    • Percentil 75: R$ 22.000                                 ││
│  │    • Tendência: "crescente"                                  ││
│  │    • Demanda: "alta"                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 3. HISTÓRICO INTERNO (JobInsightsService)                   ││
│  │    • 15 vagas similares analisadas                           ││
│  │    • Média: R$ 16.500                                        ││
│  │    • Time-to-fill médio: 32 dias                            ││
│  │    • Taxa de preenchimento: 87%                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 4. TOTAL COMPENSATION ANUAL                                  ││
│  │    • Salário: R$ 204.000 (média * 12)                        ││
│  │    • Bônus: R$ 20.400 (10% anual)                            ││
│  │    • Benefícios: R$ 25.560                                    ││
│  │    • TOTAL: R$ 249.960/ano                                    ││
│  │    • Mercado (P50): R$ 280.000/ano                           ││
│  │    • Status: ⚠️ 11% abaixo do mercado                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 26.4 EvaluationResponse Schema

```python
class EvaluationResponse(BaseModel):
    detected_fields: Dict[str, Any]
    completeness_score: float
    missing_critical_fields: List[str]
    missing_probable_fields: List[str]
    
    company_alignment: {
        "culture_match": 0.85,
        "skills_from_catalog": ["Python", "AWS", "Docker"],
    }
    
    market_alignment: {
        "salary_percentile": 75,
        "market_demand": "high",
        "competing_companies": 15
    }
    
    compensation_analysis: CompensationAnalysisResult
    
    suggestions: [
        {
            "field": "salary_min",
            "suggested": 18000,
            "reason": "Baseado em dados de mercado",
            "source": "market_benchmark"
        }
    ]
    
    recommended_action: "proceed" | "review_compensation" | "missing_critical"
    overall_confidence: float
```

### 26.5 Interface de Sugestões

```typescript
interface Suggestion {
  field: string
  value: any
  reason: string
  source: 'detected' | 'catalog' | 'market' | 'company'
  confidence: 'high' | 'medium' | 'low'
  status: 'pending' | 'accepted' | 'rejected'
}
```

**Padrão Visual de Aceite:**
```
┌─ Skill Sugerida ──────────────────────────────────────────┐
│                                                            │
│  💡 Docker                                                 │
│     Fonte: Catálogo de Skills (Engineering > DevOps)      │
│     Razão: 85% das vagas Dev Python Sênior incluem Docker │
│     Confiança: Alta                                        │
│                                                            │
│  [✓ Aceitar] [✗ Rejeitar] [📝 Editar Nível]              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Arquivos Principais de Implementação

### Backend (lia-agent-system/app/)

| Arquivo | Descrição |
|---------|-----------|
| `models/job_draft.py` | Modelo JobDraft e DraftFieldHistory |
| `models/recruiter_profile.py` | RecruiterProfile, RecruiterFieldPreference, PersonalizationSettings, ProfileCalculationLog |
| `models/intelligence_layer.py` | IntelligenceInsight, PatternCache, SuccessProfile, OutcomeCorrelation |
| `models/feedback_learning.py` | WizardFeedback, JobOutcome |
| `schemas/field_typology.py` | FieldTypology enum e FieldDefinition |
| `services/confidence_policy_service.py` | Cálculo determinístico de confiança |
| `services/skills_catalog_service.py` | Catálogo de skills por área |
| `services/intelligence_layer_service.py` | Pattern detection, outcome correlation, suggestions |
| `services/recruiter_personalization_service.py` | Personalização por recrutador |
| `api/v1/job_drafts.py` | Endpoints de Job Drafts |
| `api/v1/intelligence.py` | Endpoints de Intelligence Layer |
| `api/v1/recruiter_profiles.py` | Endpoints de Recruiter Profiles |
| `agents/specialized/job_intake_agent.py` | Agente principal (refatorado) |
| `schemas/job_description.py` | Schemas para JD Preview e Final |
| `services/jd_template_service.py` | Geração de Job Description v1 e v2 |
| `schemas/suggestion_interaction.py` | Tipos de interação com sugestões |
| `services/suggestion_interaction_service.py` | Processamento de comandos via chat |

### Frontend (plataforma-lia/src/)

| Arquivo | Descrição |
|---------|-----------|
| `hooks/use-job-draft.ts` | Hook para gerenciar estado do draft |
| `components/ui/confidence-indicator.tsx` | Indicador visual de confiança |
| `components/ui/field-origin-badge.tsx` | Badge de origem do campo |
| `components/job-wizard/job-creation-wizard.tsx` | Wizard principal (melhorado) |
| `components/job-description/` | Componentes de renderização de JD |

---

## Métricas de Sucesso

| Métrica | Baseline | Target | Atual |
|---------|----------|--------|-------|
| Taxa de aceitação de sugestões | 65% | 90% | Em medição |
| Tempo de criação de vaga | 15 min | 8 min | Em medição |
| Correções por vaga | 5.2 | 2.0 | Em medição |
| Precisão de predições TTF | - | ±20% | Em medição |
| Satisfação do recrutador (NPS) | - | +20 pts | Em medição |

---

## 27. Próximos Passos: Clustering e Embeddings

> **Status**: Proposta para implementação futura  
> **Prioridade**: Baixa (aguardar volume de dados)  
> **Pré-requisitos**: 500+ vagas criadas, Learning Engine consolidado

### 27.1 Objetivo

Implementar um sistema de clustering e embeddings vetoriais para:
- Encontrar vagas similares automaticamente
- Agrupar candidatos por perfil
- Melhorar sugestões baseadas em similaridade semântica
- Habilitar busca por contexto (não apenas keywords)

### 27.2 Por Que Não Agora?

| Razão | Impacto |
|-------|---------|
| Volume atual insuficiente | ROI baixo com poucos dados |
| Foco em experiência básica | Prioridade é consolidar wizard |
| Clustering requer massa crítica | 500+ vagas para padrões significativos |
| Investimento de infraestrutura | pgvector, embeddings, pipelines |

### 27.3 Arquitetura Proposta

```python
# Extensão do modelo JobVacancy
class JobVacancy(Base):
    # ... campos existentes ...
    
    # Novos campos para embeddings
    embedding_vector = Column(ARRAY(Float))  # 1536 dims (OpenAI)
    embedding_model = Column(String(50))      # "text-embedding-3-small"
    embedding_generated_at = Column(DateTime)
    cluster_id = Column(UUID, ForeignKey("job_clusters.id"))
    cluster_confidence = Column(Float)

class JobCluster(Base):
    """Agrupamentos automáticos de vagas"""
    id = Column(UUID, primary_key=True)
    company_id = Column(UUID)
    name = Column(String(200))           # Nome gerado automaticamente
    centroid_vector = Column(ARRAY(Float))
    common_skills = Column(ARRAY(String))
    avg_salary_min = Column(Float)
    avg_salary_max = Column(Float)
    job_count = Column(Integer)
    avg_time_to_fill = Column(Float)
    avg_success_rate = Column(Float)
```

### 27.4 Serviço de Embeddings

```python
class EmbeddingService:
    """
    Gera e gerencia embeddings para vagas e candidatos.
    Modelo: text-embedding-3-small (OpenAI) - 1536 dimensões
    Custo: $0.02/1M tokens
    """
    
    async def generate_job_embedding(self, job: JobVacancy) -> List[float]:
        text = self._build_job_text(job)
        return await self._embed(text)
    
    async def find_similar_jobs(
        self,
        embedding: List[float],
        company_id: str,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Tuple[JobVacancy, float]]:
        """Busca vagas similares usando similaridade de cosseno (pgvector)"""
        pass
    
    async def cluster_jobs(
        self,
        company_id: str,
        min_jobs: int = 20,
        n_clusters: int = None  # Auto-determinado via silhouette score
    ) -> List[JobCluster]:
        """Agrupa vagas similares usando K-Means ou HDBSCAN"""
        pass
```

### 27.5 Caso de Uso no Wizard

```
Recrutador: "Preciso de um Dev Python Sênior"

LIA (com clustering):
"Entendi! Encontrei 5 vagas similares que você criou nos últimos 12 meses.
Baseado no sucesso dessas vagas:
• Skills mais comuns: Python, FastAPI, PostgreSQL, Docker
• Faixa salarial típica: R$ 18.000 - R$ 25.000
• Tempo médio de preenchimento: 28 dias

Vou usar essas referências como base. Confirma?"
```

### 27.6 Infraestrutura Necessária

```sql
-- PostgreSQL pgvector (já disponível no Neon/Replit)
CREATE EXTENSION IF NOT EXISTS vector;

-- Índice para busca eficiente
CREATE INDEX job_embeddings_idx ON job_vacancies 
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);
```

### 27.7 Cronograma Sugerido (6 semanas)

| Fase | Duração | Entregas |
|------|---------|----------|
| **Preparação** | 1 semana | Campos de embedding, pgvector, migrations |
| **Geração** | 2 semanas | EmbeddingService, pipeline assíncrono, API similaridade |
| **Clustering** | 2 semanas | Algoritmo, análise de padrões, dashboard |
| **Integração** | 1 semana | Wizard, sugestões, métricas |

### 27.8 Métricas de Sucesso

| Métrica | Baseline | Target |
|---------|----------|--------|
| Precisão de sugestões | - | >80% aceitas |
| Tempo de criação de vaga | atual | -20% |
| Qualidade de matches | score atual | +15% |
| Custo de embeddings | - | <$50/mês |

### 27.9 Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Volume insuficiente | Alta | Adiar até 500+ vagas |
| Custo de embeddings | Baixa | Cache agressivo, batch processing |
| Performance de busca | Média | Índices IVFFlat, limitar scope |
| Qualidade de clusters | Média | Validação manual inicial |

---

---

## 28. Sistema de Aprendizagem com Histórico do Cliente

### 28.1 Visão Geral

Sistema de aprendizado contínuo que utiliza dados históricos do cliente para melhorar progressivamente as sugestões do wizard. O sistema opera em ciclo contínuo de consumo, processamento, predição e aprendizagem.

### 28.2 Prioridade de Fontes de Dados

O wizard consulta as fontes na seguinte ordem de prioridade (do mais autoritativo ao fallback):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRIORIDADE DE DADOS NO WIZARD                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1️⃣  MENU CONFIGURAÇÕES (sempre primeiro)                              │
│      → Dados cadastrados na implementação                               │
│      → Estrutura organizacional, benefícios padrão, faixas salariais    │
│                                                                         │
│  2️⃣  HISTÓRICO DA PLATAFORMA LIA                                       │
│      → Vagas já criadas na própria LIA                                  │
│      → Padrões de uso do recrutador                                     │
│                                                                         │
│  3️⃣  IMPORTAÇÃO ATS BÁSICA (Fase 1B)                                   │
│      → JDs históricos: título, responsabilidades, skills, salário       │
│                                                                         │
│  4️⃣  INTEGRAÇÃO HRIS / WORKFORCE PLANNING (Fase 1A)                    │
│      → Vagas planejadas/aprovadas, headcount, orçamento                 │
│                                                                         │
│  5️⃣  ATS COMPLETO + DATALAKES + ETLs (Fase 2)                          │
│      → Candidatos, entrevistas, métricas de processo                    │
│                                                                         │
│  6️⃣  TEMPLATES CURADOS (326) - Fallback                                │
│      → Quando cliente não tem histórico                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 28.3 Ciclo de Aprendizagem (Learning Loop)

```
                         ┌──────────────────┐
                         │   1. CONSUMO     │
                         │   DE DADOS       │
                         └────────┬─────────┘
                                  │
         Configurações, Histórico, ATS, HRIS, ETLs
                                  │
                                  ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  6. APRENDIZADO  │      │  2. PROCESSAMENTO│      │                  │
│                  │      │  E NORMALIZAÇÃO  │      │                  │
│  • Atualiza      │      │                  │      │                  │
│    padrões       │◄─────│  • Extração      │─────►│  3. ANÁLISE DE   │
│  • Ajusta pesos  │      │  • Categorização │      │     PADRÕES      │
│  • Melhora       │      │  • Enriquecimento│      │                  │
│    predições     │      │                  │      │  • Correlações   │
│                  │      └──────────────────┘      │  • Tendências    │
└────────┬─────────┘                               │  • Anomalias     │
         │                                          └────────┬─────────┘
         │                                                   │
         │         ┌──────────────────┐                      │
         │         │  5. FEEDBACK     │                      │
         │         │                  │                      │
         └────────►│  • Recrutador    │◄─────────────────────┘
                   │    aceita/rejeita│                      │
                   │  • Ajustes feitos│      ┌───────────────┘
                   │  • Outcome final │      │
                   │    (contratou?)  │      ▼
                   └────────┬─────────┘  ┌──────────────────┐
                            │            │  4. PREDIÇÃO E   │
                            │            │     SUGESTÃO     │
                            │            │                  │
                            └───────────►│  • LIA sugere    │
                                         │  • Preenche campos│
                                         │  • Explica "porquê"│
                                         └──────────────────┘
```

### 28.4 Fases de Implementação

#### Fase 1A: Integração Workforce Planning (Proativo)
*"LIA sugere abrir vagas antes do recrutador pedir"*

| Dado | Uso |
|------|-----|
| Cargo planejado | Pré-preenche título |
| Departamento | Pré-preenche área |
| Gestor responsável | Pré-preenche requisitante |
| Headcount | Quantidade de vagas |
| Orçamento/Faixa | Valida salário |
| Data prevista | Urgência/prioridade |

#### Fase 1B: Catálogo do Cliente (Importação JDs) ⬅️ **IMPLEMENTAR AGORA**
*"Usa padrões do próprio cliente"*

**Dados a importar:**
- Título da vaga
- Responsabilidades principais
- Skills técnicas (nome + nível)
- Skills comportamentais
- Faixa salarial
- Benefícios praticados

#### Fase 2A: Inteligência Preditiva
*"Predições baseadas em outcomes"*

| Dado | Uso Preditivo |
|------|---------------|
| Candidato contratado | Perfil de sucesso |
| Candidatos entrevistados | Taxa de conversão |
| Volume de candidatos | Previsão de atração |
| Canais de publicação | ROI por canal |
| Time-to-fill | Previsão de prazo |

#### Fase 2B: Dados Não-Estruturados
*"Datalakes, HRIS, Fopag"*

- Conectores para SAP, Workday, etc.
- ETL de planilhas
- Dados de folha de pagamento (faixas reais)

### 28.5 Modelo de Dados - Catálogo do Cliente

```python
class ClientJobCatalog(Base):
    """Catálogo de padrões extraídos do histórico do cliente"""
    __tablename__ = "client_job_catalogs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    
    # Fonte dos dados
    source = Column(String(50))  # "ats_import", "lia_history", "manual"
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    # Estatísticas
    total_jobs_imported = Column(Integer, default=0)
    total_jds_processed = Column(Integer, default=0)
    coverage_score = Column(Float)  # % de campos preenchidos

class ClientJobPattern(Base):
    """Padrões de vagas do cliente"""
    __tablename__ = "client_job_patterns"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    catalog_id = Column(UUID, ForeignKey("client_job_catalogs.id"))
    
    # Identificação
    title_normalized = Column(String(200))      # "desenvolvedor backend"
    title_variations = Column(ARRAY(String))    # ["Dev Backend", "Backend Developer"]
    department = Column(String(100))
    
    # Padrões
    typical_seniorities = Column(ARRAY(String))
    salary_ranges = Column(JSON)  # {"junior": {min, max}, "pleno": {...}}
    common_skills = Column(JSON)  # [{name, level, frequency}]
    common_behavioral = Column(JSON)
    common_responsibilities = Column(ARRAY(String))
    common_benefits = Column(ARRAY(String))
    
    # Métricas de uso
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    success_rate = Column(Float)  # % de contratações
    avg_time_to_fill = Column(Integer)

class ClientSkillCatalog(Base):
    """Skills do catálogo do cliente"""
    __tablename__ = "client_skill_catalogs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, nullable=False, index=True)
    
    name = Column(String(100))
    name_normalized = Column(String(100))
    category = Column(String(50))  # "technical", "behavioral"
    typical_level = Column(String(20))  # "basic", "intermediate", "advanced"
    frequency = Column(Integer)  # quantas vezes apareceu
    associated_titles = Column(ARRAY(String))
```

### 28.6 Serviço de Importação de JDs

```python
class JDImportService:
    """
    Serviço para importação e processamento de Job Descriptions.
    Extrai padrões e popula o catálogo do cliente.
    """
    
    async def import_from_ats(
        self,
        tenant_id: UUID,
        ats_type: str,  # "gupy", "pandape", "greenhouse"
        jobs_data: List[Dict]
    ) -> ImportResult:
        """
        Importa jobs de um ATS e extrai padrões.
        
        Campos esperados:
        - title: str
        - responsibilities: List[str]
        - technical_skills: List[{name, level}]
        - behavioral_skills: List[str]
        - salary_min, salary_max: float
        - benefits: List[str]
        """
        pass
    
    async def extract_patterns(
        self,
        tenant_id: UUID,
        min_frequency: int = 2
    ) -> List[ClientJobPattern]:
        """
        Analisa JDs importados e extrai padrões recorrentes.
        Agrupa títulos similares, identifica skills comuns, etc.
        """
        pass
    
    async def get_suggestions_for_title(
        self,
        tenant_id: UUID,
        title: str
    ) -> Optional[ClientJobPattern]:
        """
        Retorna padrões históricos para um título de vaga.
        Usado pelo wizard para auto-preenchimento.
        """
        pass
```

### 28.7 Integração com o Wizard

```python
class WizardDataPriority:
    """
    Ordem de consulta para cada campo no wizard.
    """
    
    PRIORITY = [
        "settings",           # 1. Menu Configurações
        "lia_history",        # 2. Histórico da plataforma LIA
        "ats_basic_import",   # 3. JDs importados (básico)
        "workforce_planning", # 4. HRIS/Workforce Planning
        "ats_full_import",    # 5. ATS completo + ETLs
        "curated_templates",  # 6. Templates curados (326)
    ]
    
    async def get_field_value(
        self,
        field: str,
        context: JobContext
    ) -> FieldSuggestion:
        for source in self.PRIORITY:
            value = await self.query(source, field, context)
            if value and value.confidence > 0.7:
                return FieldSuggestion(
                    value=value.value,
                    source=source,
                    confidence=value.confidence,
                    explanation=f"Baseado em {source}"
                )
        return await self.llm_fallback(field, context)
```

### 28.8 Menu Configurações - Seção de Integrações

Nova seção a adicionar no Menu Configurações:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔗 INTEGRAÇÕES E IMPORTAÇÕES                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📥 ATS de Origem                                                       │
│     → Status: ✅ Conectado (Gupy)                                       │
│     → Última sync: 02/02/2026 14:30                                     │
│     → Vagas importadas: 847                                             │
│     → JDs processados: 623                                              │
│                                                                         │
│  📊 Qualidade dos Dados                                                 │
│     → Cobertura de skills: 78%                                          │
│     → Cobertura de salários: 92%                                        │
│     → Recomendação: "Importe mais JDs de TI"                            │
│                                                                         │
│  📈 Workforce Planning                                                  │
│     → Status: ⏳ Não configurado                                        │
│     → [Conectar SAP SuccessFactors]                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 28.9 Evolução da Precisão

| Ciclo | Precisão das Sugestões | Fonte Principal |
|-------|------------------------|-----------------|
| Implementação inicial | ~60% | Templates curados |
| Após importação ATS | ~70% | Histórico do cliente |
| Após 10 vagas na LIA | ~75% | Padrões refinados |
| Após 50 vagas | ~85% | Learning contínuo |
| Após 100+ vagas | ~92% | Predições assertivas |

### 28.10 Métodos de Entrada de Dados

#### Opção A: Upload Manual (Menu Configurações)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚙️  CONFIGURAÇÕES > INTEGRAÇÕES > IMPORTAR DADOS                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📥 Importar Job Descriptions                                           │
│                                                                         │
│  Arraste arquivos aqui ou clique para selecionar                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │   📄 Formatos aceitos: CSV, XLSX, JSON                            │  │
│  │   📊 Máximo: 10.000 registros por arquivo                         │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Ou cole dados diretamente:                                             │
│  [    Campo de texto para colar CSV/JSON    ]                           │
│                                                                         │
│  ────────────────────────────────────────────────────────────────────   │
│                                                                         │
│  📋 Mapeamento de Colunas (após upload)                                 │
│                                                                         │
│  Coluna do arquivo    →    Campo LIA                                    │
│  ─────────────────────────────────────────                              │
│  "titulo_vaga"        →    [Título da Vaga ▼]                           │
│  "descricao"          →    [Responsabilidades ▼]                        │
│  "requisitos_tec"     →    [Skills Técnicas ▼]                          │
│  "competencias"       →    [Skills Comportamentais ▼]                   │
│  "salario_min"        →    [Salário Mínimo ▼]                           │
│  "salario_max"        →    [Salário Máximo ▼]                           │
│  "beneficios"         →    [Benefícios ▼]                               │
│                                                                         │
│                            [Processar Importação]                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Endpoint de Upload:**
```python
@router.post("/import/upload")
async def upload_job_data(
    file: UploadFile,
    column_mapping: Dict[str, str],
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Upload manual de arquivo CSV/XLSX/JSON com JDs.
    
    column_mapping exemplo:
    {
        "titulo_vaga": "title",
        "descricao": "responsibilities",
        "requisitos_tec": "technical_skills",
        "competencias": "behavioral_skills",
        "salario_min": "salary_min",
        "salario_max": "salary_max"
    }
    """
    return await jd_import_service.process_upload(
        tenant_id=tenant_id,
        file=file,
        mapping=column_mapping
    )
```

#### Opção B: Integração via API (ATS Conectado)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONECTORES DE ATS SUPORTADOS                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🟢 Gupy         → OAuth2, sync automático                              │
│  🟢 Pandapé      → API Key, sync agendado                               │
│  🟢 Greenhouse   → API Key, webhook                                     │
│  🟡 Workable     → Em desenvolvimento                                   │
│  🟡 Lever        → Em desenvolvimento                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Endpoints de Integração:**
```python
@router.post("/integrations/ats/connect")
async def connect_ats(
    ats_type: ATSType,  # "gupy", "pandape", "greenhouse"
    credentials: ATSCredentials,
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Conecta ao ATS do cliente e configura sync."""
    pass

@router.post("/integrations/ats/sync")
async def sync_ats_data(
    ats_connection_id: UUID,
    sync_options: SyncOptions,  # full, incremental, date_range
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Executa sync com o ATS conectado."""
    pass

@router.post("/integrations/ats/webhook")
async def ats_webhook(
    ats_type: str,
    payload: Dict,
    x_signature: str = Header(...)
):
    """Webhook para receber atualizações do ATS em tempo real."""
    pass
```

#### Opção C: API Pública (Integração Externa)

```python
@router.post("/api/v1/import/jobs")
async def import_jobs_api(
    jobs: List[JobImportSchema],
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    API pública para importação de jobs de qualquer fonte.
    
    JobImportSchema:
    {
        "title": "Desenvolvedor Backend",
        "department": "TI",
        "responsibilities": ["Desenvolver APIs", "..."],
        "technical_skills": [
            {"name": "Python", "level": "advanced"},
            {"name": "AWS", "level": "intermediate"}
        ],
        "behavioral_skills": ["Comunicação", "Trabalho em equipe"],
        "salary_min": 12000,
        "salary_max": 18000,
        "benefits": ["VR", "Plano de Saúde"]
    }
    """
    pass
```

### 28.11 Pipeline de Processamento da LIA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE PROCESSAMENTO                             │
│                    (JDProcessingPipeline)                                │
└─────────────────────────────────────────────────────────────────────────┘

     ENTRADA                                           SAÍDA
  (JDs brutos)                                    (Padrões prontos)
       │                                                │
       ▼                                                │
┌──────────────┐                                        │
│ ETAPA 1      │                                        │
│ VALIDAÇÃO    │                                        │
│              │                                        │
│ • Campos     │                                        │
│   obrigatórios│                                        │
│ • Formato    │                                        │
│ • Encoding   │                                        │
└──────┬───────┘                                        │
       │                                                │
       ▼                                                │
┌──────────────┐                                        │
│ ETAPA 2      │                                        │
│ NORMALIZAÇÃO │                                        │
│              │                                        │
│ • Títulos    │  "Dev Backend" → "desenvolvedor backend"
│ • Skills     │  "Nodejs" → "Node.js"                  │
│ • Salários   │  "15k" → 15000.00                      │
│ • Benefícios │  "VR" → "Vale Refeição"                │
└──────┬───────┘                                        │
       │                                                │
       ▼                                                │
┌──────────────┐                                        │
│ ETAPA 3      │                                        │
│ EXTRAÇÃO     │                                        │
│ (LLM)        │                                        │
│              │                                        │
│ • Skills de  │  "Experiência em Node e React"         │
│   texto livre│  → [{name:"Node.js"}, {name:"React"}]  │
│ • Responsa-  │                                        │
│   bilidades  │  Texto corrido → Lista estruturada     │
│ • Nível      │  "5 anos exp" → "senior"               │
└──────┬───────┘                                        │
       │                                                │
       ▼                                                │
┌──────────────┐                                        │
│ ETAPA 4      │                                        │
│ AGRUPAMENTO  │                                        │
│              │                                        │
│ • Títulos    │  Agrupa variações do mesmo cargo       │
│   similares  │  "Dev Backend" + "Backend Dev" = 1     │
│ • Frequência │  Conta ocorrências de cada skill       │
│ • Ranges     │  Calcula min/max/média de salários     │
└──────┬───────┘                                        │
       │                                                │
       ▼                                                │
┌──────────────┐                                        │
│ ETAPA 5      │                                        │
│ PERSISTÊNCIA │                                        │
│              │                                        │
│ • client_job_│                                        │
│   patterns   │  Padrões por título                    │
│ • client_    │                                        │
│   skill_     │  Catálogo de skills do cliente         │
│   catalogs   │                                        │
└──────┬───────┘                                        │
       │                                                │
       ▼                                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    DADOS PRONTOS PARA USO                     │
│                                                               │
│  client_job_patterns:                                         │
│  {                                                            │
│    "title_normalized": "desenvolvedor backend",               │
│    "title_variations": ["Dev Backend", "Backend Developer"],  │
│    "occurrence_count": 8,                                     │
│    "typical_seniorities": ["pleno", "senior"],                │
│    "salary_ranges": {                                         │
│      "pleno": {"min": 8000, "max": 14000, "avg": 11000},      │
│      "senior": {"min": 14000, "max": 22000, "avg": 18000}     │
│    },                                                         │
│    "common_skills": [                                         │
│      {"name": "Node.js", "frequency": 7, "typical_level": "advanced"},
│      {"name": "Python", "frequency": 5, "typical_level": "intermediate"},
│      {"name": "AWS", "frequency": 6, "typical_level": "intermediate"}
│    ],                                                         │
│    "common_responsibilities": [                               │
│      "Desenvolver e manter APIs RESTful",                     │
│      "Implementar testes automatizados",                      │
│      "Participar de code reviews"                             │
│    ],                                                         │
│    "common_benefits": ["VR", "Plano de Saúde", "PLR"]         │
│  }                                                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 28.12 Serviço de Processamento Detalhado

```python
class JDProcessingPipeline:
    """
    Pipeline de processamento de Job Descriptions.
    Transforma JDs brutos em padrões utilizáveis pelo wizard.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        llm_client: AnthropicClient,
        skill_normalizer: SkillNormalizerService
    ):
        self.db = db
        self.llm = llm_client
        self.normalizer = skill_normalizer
    
    async def process_batch(
        self,
        tenant_id: UUID,
        jobs: List[RawJobData],
        options: ProcessingOptions
    ) -> ProcessingResult:
        """
        Processa um lote de JDs e atualiza o catálogo do cliente.
        
        Args:
            tenant_id: ID do tenant
            jobs: Lista de JDs brutos
            options: Opções de processamento (usar LLM, etc.)
            
        Returns:
            Resultado com estatísticas e padrões gerados
        """
        
        # Etapa 1: Validação
        validated = await self._validate_batch(jobs)
        
        # Etapa 2: Normalização
        normalized = await self._normalize_batch(validated)
        
        # Etapa 3: Extração com LLM (se texto livre)
        if options.use_llm_extraction:
            extracted = await self._extract_with_llm(normalized)
        else:
            extracted = normalized
        
        # Etapa 4: Agrupamento por título
        grouped = await self._group_by_title(extracted)
        
        # Etapa 5: Persistência
        patterns = await self._persist_patterns(tenant_id, grouped)
        
        return ProcessingResult(
            total_processed=len(jobs),
            patterns_created=len(patterns),
            skills_cataloged=await self._count_skills(tenant_id),
            coverage_score=await self._calculate_coverage(tenant_id)
        )
    
    async def _validate_batch(self, jobs: List[RawJobData]) -> List[ValidatedJob]:
        """Valida campos obrigatórios e formato."""
        validated = []
        for job in jobs:
            if not job.title:
                continue  # Pula registros sem título
            validated.append(ValidatedJob(
                title=job.title,
                responsibilities=job.responsibilities or [],
                technical_skills=job.technical_skills or [],
                behavioral_skills=job.behavioral_skills or [],
                salary_min=self._parse_salary(job.salary_min),
                salary_max=self._parse_salary(job.salary_max),
                benefits=job.benefits or []
            ))
        return validated
    
    async def _normalize_batch(self, jobs: List[ValidatedJob]) -> List[NormalizedJob]:
        """Normaliza títulos, skills e outros campos."""
        normalized = []
        for job in jobs:
            normalized.append(NormalizedJob(
                title_original=job.title,
                title_normalized=self._normalize_title(job.title),
                seniority=self._infer_seniority(job.title),
                responsibilities=job.responsibilities,
                technical_skills=[
                    self.normalizer.normalize(s) for s in job.technical_skills
                ],
                behavioral_skills=job.behavioral_skills,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                benefits=self._normalize_benefits(job.benefits)
            ))
        return normalized
    
    async def _extract_with_llm(self, jobs: List[NormalizedJob]) -> List[EnrichedJob]:
        """Usa LLM para extrair dados de texto livre."""
        
        EXTRACTION_PROMPT = """
        Analise este Job Description e extraia os dados estruturados.
        
        Texto: {text}
        
        Extraia:
        1. Skills técnicas (nome + nível: basic/intermediate/advanced)
        2. Competências comportamentais
        3. Responsabilidades principais (lista de até 10 itens)
        4. Senioridade inferida (junior/pleno/senior)
        
        Retorne em JSON.
        """
        
        enriched = []
        for job in jobs:
            if job.has_structured_data:
                enriched.append(job.to_enriched())
                continue
            
            # Chama LLM para extrair de texto livre
            response = await self.llm.complete(
                EXTRACTION_PROMPT.format(text=job.raw_text)
            )
            extracted = json.loads(response.content)
            enriched.append(EnrichedJob(
                **job.dict(),
                technical_skills=extracted["technical_skills"],
                behavioral_skills=extracted["behavioral_skills"],
                responsibilities=extracted["responsibilities"],
                seniority=extracted["seniority"]
            ))
        
        return enriched
    
    async def _group_by_title(
        self,
        jobs: List[EnrichedJob]
    ) -> Dict[str, JobPattern]:
        """Agrupa jobs por título normalizado e calcula estatísticas."""
        
        groups: Dict[str, List[EnrichedJob]] = defaultdict(list)
        
        for job in jobs:
            groups[job.title_normalized].append(job)
        
        patterns = {}
        for title, group in groups.items():
            patterns[title] = JobPattern(
                title_normalized=title,
                title_variations=list(set(j.title_original for j in group)),
                occurrence_count=len(group),
                
                # Senioridades encontradas
                typical_seniorities=list(set(j.seniority for j in group if j.seniority)),
                
                # Salary ranges por senioridade
                salary_ranges=self._calculate_salary_ranges(group),
                
                # Skills mais frequentes
                common_skills=self._aggregate_skills(group),
                
                # Responsabilidades mais comuns
                common_responsibilities=self._aggregate_responsibilities(group),
                
                # Benefícios mais comuns
                common_benefits=self._aggregate_benefits(group)
            )
        
        return patterns
    
    async def _persist_patterns(
        self,
        tenant_id: UUID,
        patterns: Dict[str, JobPattern]
    ) -> List[ClientJobPattern]:
        """Persiste padrões no banco de dados."""
        
        persisted = []
        for title, pattern in patterns.items():
            # Upsert: atualiza se existir, cria se não
            existing = await self.db.execute(
                select(ClientJobPattern)
                .where(ClientJobPattern.tenant_id == tenant_id)
                .where(ClientJobPattern.title_normalized == title)
            )
            existing = existing.scalar_one_or_none()
            
            if existing:
                # Merge com dados existentes
                existing.occurrence_count += pattern.occurrence_count
                existing.title_variations = list(set(
                    existing.title_variations + pattern.title_variations
                ))
                # ... merge outros campos
            else:
                # Cria novo
                existing = ClientJobPattern(
                    tenant_id=tenant_id,
                    **pattern.dict()
                )
                self.db.add(existing)
            
            persisted.append(existing)
        
        await self.db.commit()
        return persisted
```

### 28.13 Uso pelo Wizard

```python
class WizardSuggestionService:
    """Serviço que consulta todas as fontes para gerar sugestões."""
    
    async def get_suggestions_for_title(
        self,
        tenant_id: UUID,
        title: str,
        context: Optional[JobContext] = None
    ) -> WizardSuggestions:
        """
        Busca sugestões em cascata de prioridade.
        Retorna dados mesclados de todas as fontes disponíveis.
        """
        
        suggestions = WizardSuggestions()
        title_normalized = self._normalize_title(title)
        
        # 1. Menu Configurações (sempre disponível)
        settings = await self.settings_service.get_company_settings(tenant_id)
        suggestions.work_model = FieldSuggestion(
            value=settings.default_work_model,
            source="settings",
            confidence=0.95
        )
        suggestions.benefits = FieldSuggestion(
            value=settings.default_benefits,
            source="settings",
            confidence=0.95
        )
        
        # 2. Histórico LIA
        lia_pattern = await self.lia_history_service.find_pattern(
            tenant_id, title_normalized
        )
        if lia_pattern:
            suggestions.merge_from(lia_pattern, source="lia_history", confidence=0.88)
        
        # 3. Catálogo Importado (ATS)
        client_pattern = await self.client_catalog_service.find_pattern(
            tenant_id, title_normalized
        )
        if client_pattern:
            suggestions.merge_from(client_pattern, source="client_import", confidence=0.82)
        
        # 4. Templates Curados (fallback)
        if suggestions.has_gaps():
            template = await self.template_service.find_best_match(title)
            if template:
                suggestions.fill_gaps_from(template, source="curated_template", confidence=0.70)
        
        return suggestions
```

### 28.14 Fluxo Completo (Diagrama de Sequência)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Cliente  │    │  Upload  │    │ Pipeline │    │   DB     │    │  Wizard  │
│  (RH)    │    │   API    │    │  Process │    │ Patterns │    │  Agent   │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │               │
     │ Upload CSV    │               │               │               │
     │──────────────>│               │               │               │
     │               │               │               │               │
     │               │ Valida/Mapeia │               │               │
     │               │──────────────>│               │               │
     │               │               │               │               │
     │               │               │ Normaliza     │               │
     │               │               │───────┐       │               │
     │               │               │       │       │               │
     │               │               │<──────┘       │               │
     │               │               │               │               │
     │               │               │ Extrai (LLM)  │               │
     │               │               │───────┐       │               │
     │               │               │       │       │               │
     │               │               │<──────┘       │               │
     │               │               │               │               │
     │               │               │ Agrupa        │               │
     │               │               │───────┐       │               │
     │               │               │       │       │               │
     │               │               │<──────┘       │               │
     │               │               │               │               │
     │               │               │ Persiste      │               │
     │               │               │──────────────>│               │
     │               │               │               │               │
     │               │ Resultado     │               │               │
     │<──────────────│<──────────────│               │               │
     │ "623 JDs      │               │               │               │
     │  processados" │               │               │               │
     │               │               │               │               │
     │               │               │               │               │
     ═══════════════════════════════════════════════════════════════════
     │                        MAIS TARDE                              │
     ═══════════════════════════════════════════════════════════════════
     │               │               │               │               │
     │ "Criar vaga   │               │               │               │
     │  dev backend" │               │               │               │
     │───────────────│───────────────│───────────────│──────────────>│
     │               │               │               │               │
     │               │               │               │  Busca        │
     │               │               │               │<──────────────│
     │               │               │               │  patterns     │
     │               │               │               │──────────────>│
     │               │               │               │               │
     │               │               │               │               │
     │ Sugestões     │               │               │               │
     │ preenchidas   │               │               │               │
     │<──────────────│───────────────│───────────────│───────────────│
     │               │               │               │               │
```

### 28.15 Cronograma - Fase 1B (Importação JDs Básicos)

| Semana | Entregas |
|--------|----------|
| **1** | Modelo de dados (ClientJobPattern, ClientSkillCatalog), migrations |
| **2** | JDImportService, parser de JDs, extração de campos básicos |
| **3** | API de importação, integração com Gupy/Pandapé |
| **4** | Integração com Wizard, priorização de fontes, testes |

**Campos Fase 1B:**
- ✅ Título
- ✅ Responsabilidades
- ✅ Skills técnicas
- ✅ Skills comportamentais
- ✅ Faixa salarial
- ✅ Benefícios

---

## 29. Fast Track e Templates Curados

### 29.1 Visão Geral

O Fast Track permite criar vagas em até 80% menos tempo (15 min → 3 min) reutilizando templates curados ou vagas anteriores do cliente.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODOS DE CRIAÇÃO DE VAGA                            │
├──────────────────────────────────┬──────────────────────────────────────────┤
│         COMPLETO (Scratch)       │           FAST TRACK (Reuse)             │
├──────────────────────────────────┼──────────────────────────────────────────┤
│ • 3 fases, 7 etapas              │ • 1 fase, 2 etapas                       │
│ • Conversa detalhada com LIA     │ • Seleção + Revisão                      │
│ • Coleta campo a campo           │ • Copia tudo, ajusta uma vez             │
│ • ~15 min para nova vaga         │ • ~3 min para vaga similar               │
│ • Ideal para: vagas novas        │ • Ideal para: vagas recorrentes          │
└──────────────────────────────────┴──────────────────────────────────────────┘
```

### 29.2 Status de Implementação Fast Track

| Fase | Status | Progresso |
|------|--------|-----------|
| Fase 1: Templates Curados | ✅ Concluído | 361 templates (100%) |
| Fase 2: Learning Loop Backend | ✅ Concluído | 100% |
| Fase 3: Fast Track UX | ✅ Concluído | 100% |
| Fase 4: Learning Loop Inteligente | ✅ Concluído | 100% |
| Fase 5: Polimento Final | ✅ Concluído | 100% (core) |

### 29.3 Fluxo Completo Fast Track (7 Etapas)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: DETECÇÃO (✅ IMPLEMENTADO)                                 │
│ Usuário digita título da vaga                                       │
│ Sistema busca vagas similares (>70% match semântico)               │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: SUGESTÃO CONVERSACIONAL (✅ IMPLEMENTADO)                  │
│ LIA mostra sugestões no chat + painel lateral                       │
│ Usuário responde em linguagem natural ("sim", "a 2", "não")         │
│ Analytics: fast_track_suggestion_shown                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: CÓPIA COMPLETA (✅ IMPLEMENTADO)                           │
│ Copia: título, descrição, skills, salário, WSI, etc.               │
│ Preenche todos os campos automaticamente                            │
│ Analytics: fast_track_accepted                                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: CAMPOS SENSÍVEIS (✅ IMPLEMENTADO)                         │
│                                                                     │
│ LIA: "Copiei tudo! Só preciso confirmar alguns detalhes:            │
│ - Quem é o gestor desta vaga?                                       │
│ - A localização continua [cidade anterior]?                         │
│ - Essa vaga é afirmativa para algum grupo?"                         │
│                                                                     │
│ Usuário responde em linguagem natural                               │
│ LIA interpreta via NLU e preenche campos                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: REVISÃO (✅ IMPLEMENTADO - FastTrackReviewPanel)           │
│ Painel lateral com seções colapsáveis para edição                   │
│ LIA: "Quer ajustar algo ou posso publicar?"                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 6: REGENERAÇÃO WSI (✅ IMPLEMENTADO)                          │
│                                                                     │
│ SE usuário editou competências:                                     │
│ LIA: "Percebi que você alterou competências (+React, -Angular).     │
│ Quer que eu atualize as perguntas WSI?"                             │
│                                                                     │
│ Usuário: "sim" → Chama /wsi/regenerate-questions                    │
│ Usuário: "não" → Mantém perguntas originais                         │
│ Analytics: fast_track_wsi_regenerated                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 7: PUBLICAÇÃO (✅ IMPLEMENTADO)                               │
│ Botão "Publicar Vaga" no painel                                     │
│ Registra Fast Track usage + gera embedding                          │
│ Inclui eligibility_questions da pré-qualificação global             │
└─────────────────────────────────────────────────────────────────────┘
```

### 29.4 Campos Sensíveis - Implementação

**Filosofia:** LIA interpreta respostas em linguagem natural (sem dropdowns)

| Campo | Pergunta LIA | Padrões Reconhecidos | Status |
|-------|--------------|----------------------|--------|
| Gestor | "Quem é o gestor desta vaga?" | Nome completo, regex extração | ✅ |
| Localização | "A localização continua [cidade]?" | "sim", "não, [cidade]", "remoto" | ✅ |
| Vaga Afirmativa | "Essa vaga é afirmativa?" | "não", "sim, para [grupo]", grupos específicos | ✅ |

**Estados de controle:**
- `awaitingSensitiveFieldsConfirmation`: Gates resposta do usuário
- `fastTrackAppliedData`: Armazena dados para referência na pergunta

**Localização no código:** `expanded-chat-modal.tsx:5195-5350`

### 29.5 Regeneração WSI - Implementação

**Trigger:** Usuário edita competências técnicas ou comportamentais no painel

**Estados de controle:**
- `fastTrackOriginalCompetencies`: Salva skills originais do Fast Track
- `wsiRegenerationPrompted`: Previne prompts duplicados
- `awaitingWSIRegenerationConfirmation`: Gates resposta do usuário

**Fluxo implementado:**
1. Fast Track aplicado → salva competências originais
2. useEffect monitora mudanças em `technicalSkills` / `behavioralCompetencies`
3. Se mudança detectada durante stage 'competencies':
   - Gera summary de mudanças (+skill, -skill)
   - LIA pergunta conversacionalmente
4. Usuário responde "sim" → chama API regenerateWSIQuestions
5. Novas perguntas substituem as anteriores
6. Analytics: `fast_track_wsi_regenerated` disparado

**Localização no código:** `expanded-chat-modal.tsx:1240-1286, 5105-5190`

### 29.6 Pré-qualificação Global - Implementação

**Hook utilizado:** `useCompanyEligibilityQuestions()`

**Fluxo:**
1. Hook carrega perguntas da empresa automaticamente
2. Perguntas sincronizadas para `companyDefaultQuestions`
3. Mantidas separadas dos dados Fast Track (não sobrescritas)
4. Incluídas no payload final como `eligibility_questions`

**Localização no código:** `expanded-chat-modal.tsx:684, 2174-2186, 3878`

### 29.7 Analytics Events Fast Track

| Evento | Payload | Pontos de Disparo |
|--------|---------|-------------------|
| `fast_track_suggestion_shown` | `{ accepted: false }` | Quando sugestões aparecem |
| `fast_track_accepted` | `{ accepted: true }` | Quando usuário aceita |
| `fast_track_rejected` | `{ accepted: false }` | 3 pontos: explícito, from_scratch, UI dismiss |
| `fast_track_wsi_regenerated` | `{ accepted: true }` | Após regeneração bem-sucedida |

**Prevenção de duplicatas:**
- `fastTrackSuggestionsShownTracked`: Previne múltiplos `suggestion_shown`
- Estados de awaiting previnem eventos durante confirmações

### 29.8 Arquivos Principais Fast Track

**Backend (lia-agent-system):**
| Arquivo | Descrição |
|---------|-----------|
| `app/services/job_embedding_service.py` | Embeddings e busca semântica |
| `app/api/v1/job_embeddings.py` | Endpoints Fast Track |
| `app/api/v1/wsi_questions.py` | Regeneração WSI |
| `app/services/pre_qualification_service.py` | Pré-qualificação |

**Frontend (plataforma-lia):**
| Arquivo | Descrição |
|---------|-----------|
| `src/hooks/useFastTrack.ts` | Hook principal Fast Track |
| `src/hooks/use-company-eligibility-questions.ts` | Pré-qualificação global |
| `src/hooks/useWizardAnalytics.ts` | Analytics tracking |
| `src/components/job-wizard/FastTrackSuggestions.tsx` | Cards de sugestões |
| `src/components/job-wizard/FastTrackReviewPanel.tsx` | Painel de revisão |
| `src/components/expanded-chat-modal.tsx` | Modal do wizard (~9800 linhas) |
| `src/services/lia-api.ts` | Funções de API |

### 29.9 Métricas de Sucesso Fast Track

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Tempo 1ª vaga | 15 min | 15 min | ✅ Baseline |
| Tempo 10ª vaga | 15 min | 3 min | ⏳ Medir |
| Taxa de reuso Fast Track | 0% | 60%+ | ⏳ Medir |
| Cobertura templates | 326 | 480+ | 📊 68% |

### 29.10 Biblioteca de Templates Curados

**Total: 326 Templates Validados**

| Categoria | Qtd | Subcategorias |
|-----------|-----|---------------|
| **tecnologia** | 119 | desenvolvimento, dados, infra, seguranca, design, gestao, arquitetura, qualidade, produto |
| **comercial** | 98 | inside_sales, field_sales, customer_success, gestao, canais, vendas_tecnicas, ecommerce, sales_ops |
| **rh** | 32 | recrutamento, business_partner, dp, remuneracao, td, desenvolvimento, cultura, gestao |
| **administrativo** | 21 | geral, secretariado, facilities, compras, documentacao, patrimonio, gestao |
| **financas** | 19 | contabilidade, fiscal, controladoria, planejamento, tesouraria, auditoria, gestao |
| **operacoes** | 14 | logistica, supply_chain, compras, qualidade, comex, gestao |
| **saude** | 13 | enfermagem, medicina, terapias, farmacia, gestao |
| **marketing** | 8 | digital, conteudo, branding, performance, growth, gestao |
| **customer_success** | 2 | cs_management, onboarding |

### 29.11 WSI Quality Gates (100% Compliance)

Todos os 326 templates passam pelos seguintes quality gates:

```python
def validate_template(template: Dict) -> List[str]:
    errors = []
    
    # Gate 1: Mínimo 5 skills técnicas
    if len(template.get("technical_skills", [])) < 5:
        errors.append("Mínimo 5 skills técnicas requeridas")
    
    # Gate 2: Skills com níveis válidos
    for skill in template.get("technical_skills", []):
        if skill.get("level") not in ["basic", "intermediate", "advanced"]:
            errors.append(f"Nível inválido: {skill.get('level')}")
    
    # Gate 3: Mínimo 3 competências comportamentais
    if len(template.get("behavioral_competencies", [])) < 3:
        errors.append("Mínimo 3 competências comportamentais")
    
    # Gate 4: Competências com justificativas
    for comp in template.get("behavioral_competencies", []):
        if not comp.get("justification"):
            errors.append(f"Competência sem justificativa: {comp.get('name')}")
    
    # Gate 5: Mínimo 5 responsabilidades
    if len(template.get("responsibilities", [])) < 5:
        errors.append("Mínimo 5 responsabilidades requeridas")
    
    return errors
```

### 29.12 Arquivos de Templates

```
lia-agent-system/app/data/
├── templates/
│   └── __init__.py                      # Registro central
├── curated_templates_tech.py            # 119 templates
├── curated_templates_vendas.py          # 98 templates
├── curated_templates_rh.py              # 32 templates
├── curated_templates_financas.py        # 19 templates
├── curated_templates_administrativo.py  # 21 templates
├── curated_templates_cs.py              # 2 templates
├── curated_templates_saude.py           # 13 templates
├── curated_templates_marketing.py       # 8 templates
└── curated_templates_operacoes.py       # 14 templates
```

### 29.13 Serviço de Templates

```python
class JobTemplateService:
    """Serviço para gerenciar templates de vagas."""
    
    def search_templates(
        self,
        query: str,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        seniority: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Busca templates por texto, categoria ou senioridade.
        Retorna templates ordenados por relevância.
        """
        
    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Retorna template específico por ID."""
        
    def get_categories(self) -> List[Dict]:
        """Retorna lista de categorias com contagem."""
        
    def _normalize_category(self, category: str) -> str:
        """Normaliza aliases de categoria."""
        aliases = {
            "vendas": "comercial",
            "sales": "comercial",
            "recursos_humanos": "rh",
            "people": "rh",
            "tech": "tecnologia",
            "ti": "tecnologia",
            "cs": "customer_success",
        }
        return aliases.get(category.lower(), category.lower())
```

### 29.14 Script de Validação

```bash
# Validar todos os templates
cd lia-agent-system && python scripts/validate_templates.py

# Output esperado:
# ✅ VALIDAÇÃO COMPLETA!
# Total de templates: 326
# Categorias: 9
# Erros: 0
# Duplicatas: 0
```

---

## 30. Modos de Criação de Vagas (Completo vs Fast Track)

### 30.1 Fluxo de Decisão Inicial

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             NOVA VAGA                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   LIA: "Oi! Vamos criar uma nova vaga. Você pode:"                         │
│                                                                              │
│   ┌─────────────────────────┐    ┌─────────────────────────────────┐        │
│   │    COMEÇAR DO ZERO      │    │       FAST TRACK ⚡              │        │
│   │                         │    │                                  │        │
│   │  Criar vaga completa    │    │  Reusar vaga anterior           │        │
│   │  com minha ajuda        │    │  ou template curado             │        │
│   │  (~15 min)              │    │  (~3 min)                       │        │
│   └─────────────────────────┘    └─────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 30.2 Modo Completo (Scratch) - 3 Fases, 7 Etapas

```
┌─ FASE 1: CONSTRUÇÃO ──────────────────────────────────────────────────────┐
│                                                                            │
│  Etapa 1: Assessment                                                       │
│  ├── Título da vaga                                                        │
│  ├── Departamento                                                          │
│  ├── Nível de senioridade                                                  │
│  ├── Modelo de trabalho                                                    │
│  └── Contexto da posição                                                   │
│                                                                            │
│  Etapa 2: Remuneração                                                      │
│  ├── Faixa salarial (com benchmark de mercado)                            │
│  ├── Benefícios                                                            │
│  └── Tipo de contratação                                                   │
│                                                                            │
│  Etapa 3: Competências                                                     │
│  ├── Skills técnicas (mín. 5)                                             │
│  ├── Competências comportamentais (mín. 3)                                │
│  └── Responsabilidades                                                     │
│                                                                            │
│  Etapa 4: Screening                                                        │
│  ├── Perguntas de triagem                                                  │
│  ├── Configuração WSI                                                      │
│  └── Critérios eliminatórios                                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ FASE 2: ATIVAÇÃO ─────────────────────────────────────────────────────────┐
│                                                                            │
│  Etapa 5: Review                                                           │
│  ├── Validação de campos                                                   │
│  ├── Geração de Job Description                                            │
│  ├── Preview da vaga                                                       │
│  └── Ajustes finais                                                        │
│                                                                            │
│  Etapa 6: Publicação                                                       │
│  ├── Canais de divulgação                                                  │
│  ├── Job boards                                                            │
│  └── Notificações                                                          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ FASE 3: SELEÇÃO ──────────────────────────────────────────────────────────┐
│                                                                            │
│  Etapa 7: Acompanhamento                                                   │
│  ├── Pipeline de candidatos                                                │
│  ├── Screening automático                                                  │
│  └── Análise WSI                                                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 30.3 Modo Fast Track - 1 Fase, 2 Etapas

```
┌─ FAST TRACK ⚡ ─────────────────────────────────────────────────────────────┐
│                                                                            │
│  Etapa 1: SELEÇÃO DE BASE                                                  │
│  ├── Escolher fonte:                                                       │
│  │   ├── Vagas anteriores do cliente                                       │
│  │   ├── Templates curados (326)                                           │
│  │   └── Busca por texto/categoria                                         │
│  │                                                                         │
│  └── Preview do template selecionado                                       │
│                                                                            │
│  Etapa 2: REVISÃO E AJUSTES                                                │
│  ├── Painel lateral com todos os campos                                    │
│  ├── Edição inline                                                         │
│  ├── LIA sugere ajustes contextuais                                        │
│  │   ├── "Salário está 11% abaixo do mercado"                             │
│  │   └── "Considere adicionar skill X"                                     │
│  │                                                                         │
│  └── Publicação direta                                                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 30.4 Comparativo de Tempo

| Ação | Completo | Fast Track | Economia |
|------|----------|------------|----------|
| Informações básicas | 3 min | 10 seg | 95% |
| Competências | 5 min | 30 seg | 90% |
| Screening | 4 min | 20 seg | 92% |
| Review/JD | 3 min | 1 min | 67% |
| **TOTAL** | **15 min** | **~3 min** | **80%** |

### 30.5 Quando Usar Cada Modo

| Cenário | Modo Recomendado | Motivo |
|---------|------------------|--------|
| Primeira vaga do cargo | Completo | Coletar detalhes específicos |
| Vaga recorrente (ex: Dev Jr) | Fast Track | Reutilizar template existente |
| Substituição de funcionário | Fast Track | Copiar da vaga anterior |
| Nova área/departamento | Completo | Definir padrões |
| Contratação em massa | Fast Track | Escalar rapidamente |
| Vaga com requisitos únicos | Completo | Personalização total |

### 30.6 Evolução com Learning Loop

Com o Learning Loop (Seção 28), o Fast Track se torna mais inteligente:

```
                      EVOLUÇÃO DA PRECISÃO
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  100% ─┼────────────────────────────────────────────── ◆ 92%   │
│        │                                           ◆ 87%       │
│   80% ─┼────────────────────────────── ◆ 80%                   │
│        │                      ◆ 75%                             │
│   60% ─┼────────── ◆ 65%                                       │
│        │  ◆ 60%                                                 │
│   40% ─┼                                                        │
│        │                                                        │
│    0% ─┼────┬────┬────┬────┬────┬────┬────                     │
│        │  Job1 Job3 Job5 Job7 Job9 Job11                       │
│                                                                 │
│  ◆ = Precisão de sugestões aceitas                             │
└─────────────────────────────────────────────────────────────────┘

Fontes de Aprendizagem (por prioridade):
1. Configurações da empresa → 100% precisão
2. Histórico LIA → 95% precisão  
3. JDs importados do ATS → 85% precisão
4. Workforce Planning → 80% precisão
5. Templates curados → 70% precisão inicial
```

### 30.7 Integração com Pipeline

Ambos os modos alimentam o mesmo pipeline de seleção:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   [Modo Completo]  ─┐                                                       │
│                     ├──► JobVacancy ──► Pipeline ──► WSI Screening          │
│   [Fast Track]    ──┘                                                       │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                      VAGA PUBLICADA                                │    │
│   │                                                                    │    │
│   │  • Todas as validações WSI aplicadas                              │    │
│   │  • Quality Gates verificados                                       │    │
│   │  • Screening automático ativo                                      │    │
│   │  • Sourcing inteligente iniciado                                   │    │
│   │  • Learning Loop coletando feedback                                │    │
│   │                                                                    │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 30.5 Serviços Backend Existentes (NÃO REIMPLEMENTAR)

Antes de implementar qualquer funcionalidade, verificar se já existe. Os seguintes serviços **JÁ ESTÃO IMPLEMENTADOS**:

| Serviço | Arquivo | Linhas | Funcionalidade | Usar Em |
|---------|---------|--------|----------------|---------|
| **Pearch AI** | `pearch_service.py` | 1043 | Busca global de candidatos via API v2 | Fase de busca |
| **Market Benchmark** | `market_benchmark_service.py` | 703 | Benchmark de salários via web search | Fase de salário |
| **Intelligence Layer** | `intelligence_layer_service.py` | ~500 | Pattern Detection, Confidence Adjuster | Quality Gates |
| **Recruiter Personalization** | `recruiter_personalization_service.py` | ~400 | Preferências por recrutador | Smart Start |
| **Skills Catalog** | `skills_catalog_service.py` | ~300 | Catálogo de skills por área | Competências |
| **Confidence Policy** | `confidence_policy_service.py` | ~200 | Cálculo determinístico de confiança | Quality Gates |
| **Conversation Memory** | `conversation_memory.py` | ~853 | Persistência de conversas | Memória |
| **Tool Registry** | `tool_registry.py` | ~600 | 59 tools registradas | Tool Calling |

### Hooks Frontend Existentes

| Hook | Arquivo | Linhas | Funcionalidade | Status |
|------|---------|--------|----------------|--------|
| **useWizardNavigation** | `hooks/useWizardNavigation.ts` | 258 | Navegação via chat, validação de stages | ✅ |
| **useWSIQualityGates** | `hooks/useWSIQualityGates.ts` | 170 | Quality score, bloqueio <70%, barra visual | ✅ |
| **useChatSync** | `hooks/useChatSync.ts` | 336 | Rastreio de mudanças, sincronização bidirecional | ✅ |
| **useWizardOrchestrator** | `hooks/useWizardOrchestrator.ts` | 254 | Orquestrador unificado, mapeamento de campos | ✅ |
| **useWizardState** | `hooks/useWizardState.ts` | ~200 | Estado centralizado do wizard | ✅ |
| **useToolCalling** | `hooks/useToolCalling.ts` | ~250 | Tool calling lifecycle | ✅ |
| **useConversationMemory** | `hooks/useConversationMemory.ts` | ~300 | Memória conversacional | ✅ |
| **useContextSwitching** | `hooks/useContextSwitching.ts` | 312 | Troca de contexto general/wizard/fast_track | ✅ |

### Componentes Frontend Existentes

| Componente | Arquivo | Funcionalidade |
|------------|---------|----------------|
| `ConfidenceIndicator` | `job-creation/confidence-indicator.tsx` | Mostra nível de confiança visual |
| `FieldOriginBadge` | `job-creation/field-origin-badge.tsx` | Mostra origem (inferido, default, benchmark) |
| `FinalReviewPanel` | `job-creation/final-review-panel.tsx` | Painel de revisão final |
| `ScreeningQuestionsPanel` | `job-creation/ScreeningQuestionsPanel.tsx` | Painel de perguntas WSI |
| `WSIQualityBar` | `expanded-chat/components/WSIQualityBar.tsx` | Barra visual de qualidade |
| `ToolConfirmationMessage` | `expanded-chat/components/tool-confirmation-message.tsx` | UI confirmação de tool |
| `ToolExecutionFeedback` | `expanded-chat/components/tool-execution-feedback.tsx` | UI resultado de tool |

---

## 30.6 Fases de Implementação do Wizard (Status)

| # | Fase | Descrição | Estimativa | Status |
|---|------|-----------|------------|--------|
| **1** | Smart Start + Catálogo | Integração com dados cadastrados | 4-5 dias | ✅ CONCLUÍDA |
| **2** | Navegação + Comandos | Comandos de edição via chat | 6-8 dias | ✅ CONCLUÍDA |
| **3** | Quality Gates para WSI | Validação de qualidade de dados | 4-5 dias | ✅ CONCLUÍDA |
| **4** | Sincronização Chat ↔ Painel | Bidirecional em tempo real | 5-6 dias | ✅ CONCLUÍDA |
| **5** | Orquestrador Unificado | Endpoint único de roteamento | 6-8 dias | ✅ CONCLUÍDA |
| **6** | Tool Calling | Integrar 59 tools no wizard | 5-6 dias | ✅ CONCLUÍDA |
| **7** | Memória Conversacional | Contexto persistente | 5-6 dias | ✅ CONCLUÍDA |
| **8** | Fast Track | Reutilização de vagas anteriores | 8-10 dias | ✅ CONCLUÍDA |
| **9** | UX e Qualidade | Testes, acessibilidade, polish | 8-10 dias | ✅ CONCLUÍDA |

### Fase 2: Comandos de Edição via Chat

**Comandos Suportados:**

| Padrão | Campo Afetado | Exemplo |
|--------|---------------|---------|
| "mude X para Y" | Qualquer campo | "mude senioridade para sênior" |
| "adicione X" | Skills, benefícios | "adicione Python nas skills" |
| "remova X" | Skills, benefícios | "remova vale combustível" |
| "volte para X" | Navegação | "volte para salário" |
| "pule para X" | Navegação | "pule para revisão" |

**Localização:** `expanded-chat-modal.tsx:6141-6312`

### Fase 3: Quality Gates WSI

```typescript
const QUALITY_THRESHOLDS = {
  TECHNICAL_SKILLS_MIN: 5,     // Peso: 8 × 5 = 40 pontos
  BEHAVIORAL_MIN: 3,           // Peso: 10 × 3 = 30 pontos
  RESPONSIBILITIES_MIN: 3,     // Peso: 5 × 3 = 15 pontos
  SENIORITY_WEIGHT: 5,         // 5 pontos
  WORK_MODEL_WEIGHT: 5,        // 5 pontos
  DESCRIPTION_MIN_CHARS: 200,  // 5 pontos
}
// Total máximo: 100 pontos
// Mínimo para avançar: 70 pontos
```

**Retorno do hook `useWSIQualityGates`:**
- `score: number` - Score 0-100
- `fields: WSIQualityField[]` - Status de cada campo
- `canAdvance: boolean` - true se score >= 70
- `scoreColor: 'green' | 'yellow' | 'red'`
- `summaryText: string` - "Adicione mais 2 skills técnicas"

### Fase 4: Sincronização Chat ↔ Painel

```typescript
interface FieldChange {
  field: string
  oldValue: any
  newValue: any
  source: 'panel' | 'chat' | 'orchestrator'
  timestamp: Date
  displayLabel?: string
}
```

**Funções do hook `useChatSync`:**
- `trackFieldChange(change)` - Registra mudança de campo
- `generateChangeSummary()` - Resume mudanças para mensagem
- `generateLLMContext()` - Contexto para LLM (histórico de edições)
- `getGroupedChanges()` - Agrupa mudanças próximas

### Fase 5: Orquestrador Unificado

```typescript
interface OrchestratorResult {
  action: WizardOrchestratorAction  // 'navigate' | 'update_field' | 'ask_question' | etc.
  response: string
  fieldUpdates?: OrchestratorFieldUpdates
  targetStage?: WizardStage
  confidence: number
  reasoning?: string
  suggestions?: Array<{ field: string; value: any; reason: string }>
}
```

**Mapeamento Backend → Frontend (36 campos):**
- `salary_min` → `salaryInfo.minSalary`
- `technical_skills` → `technicalSkills`
- `seniority_level` → `detectedCriteria.senioridadeIdiomas`

**Context Switching (3 contextos):**
- `general` - Chat livre
- `wizard` - Modo criação de vaga
- `fast_track` - Modo Fast Track

### Fase 6: Tool Calling

**Intent-to-Tool Mappings:**

| Intent (PT-BR) | Tool | Confirmação |
|----------------|------|-------------|
| "publica a vaga" | publish_job | ✅ Sim |
| "pause a vaga" | pause_job | ✅ Sim |
| "encerra a vaga" | close_job | ✅ Sim |
| "salva como rascunho" | update_job | ❌ Não |
| "valida os campos" | validate_job_fields | ❌ Não |

**Fluxo de Execução:**
1. Usuário digita comando em linguagem natural
2. Backend detecta intent via regex patterns
3. Orquestrador retorna `suggested_tool_call`
4. Frontend exibe `ToolConfirmationMessage` se requires_confirmation
5. Usuário confirma → Hook executa via API
6. Frontend exibe `ToolExecutionFeedback` com resultado

### Fase 7: Memória Conversacional

**Formato de Contexto Injetado:**
```
## Contexto da Conversa
Resumo: {summary ou "Início da conversa"}
Últimas mensagens:
- [user]: {mensagem}
- [assistant]: {resposta}

## Preferências do Usuário
{preferences se disponível}
```

**Funcionalidades:**
- **Auto-summary**: Gera resumo a cada 10 mensagens via LLM
- **Context injection**: Injetado no system prompt (max 4000 tokens)
- **Persistência**: localStorage por contexto
- **Cross-session**: Recupera conversa ativa ao reabrir wizard

### Fase 9: UX e Qualidade

**Testes E2E:**
- `e2e/tests/chat/tool-calling.spec.ts` - Confirmação de ações, cancelamento, estado
- `e2e/tests/chat/conversation-memory.spec.ts` - Persistência, resumo, restauração

**Acessibilidade WCAG:**

| Elemento | Implementação |
|----------|---------------|
| Aria-labels | Botões fullscreen, input, enviar, confirmar/cancelar |
| Keyboard navigation | Enter enviar, ESC fechar, Tab navegação |
| Focus management | Auto-focus input, aria-modal="true" |
| Screen readers | role="dialog", aria-live="polite", role="status" |
| sr-only hints | Descrições ocultas para navegação |

**Polish Visual:**

| Feature | Implementação |
|---------|---------------|
| Typing indicator | "LIA está digitando..." com animação dots bounce |
| Transitions | animate-in fade-in-0, slide-in-from-bottom, duration-300 |
| Backdrop click | Fecha modal ao clicar fora (modo não-inline) |
| Focus ring | Visível em elementos focáveis |

---

# PARTE 5: ARQUITETURA TÉCNICA

---

## 31. Arquitetura Multi-Agente (9 agentes)

### 31.1 Visão Geral

A plataforma LIA utiliza uma arquitetura multi-agente com **9 agentes ativos** baseada no WeDOTalent Multi-Agent Architecture v2.2.

### 31.2 Diagrama de Agentes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA MULTI-AGENTE LIA v2.2                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                    ORCHESTRATOR (Ag.0)                                   │   │
│  │         Roteamento, Memória, Delegação, Coordenação                      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│    ┌───────────────────────────────────┼───────────────────────────────────┐    │
│    ▼                   ▼               ▼               ▼                   ▼    │
│  ┌────────┐  ┌────────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Ag.1   │  │    Ag.2        │  │   Ag.3   │  │    Ag.4     │  │   Ag.5     │ │
│  │ Job    │  │   Sourcing     │  │ Triagem  │  │Entrevistador│  │ Avaliador  │ │
│  │Intake  │  │   Agent        │  │Curricular│  │  WSI Voice  │  │    WSI     │ │
│  └────────┘  └────────────────┘  └──────────┘  └─────────────┘  └────────────┘ │
│                                                                                  │
│  ┌────────┐  ┌────────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Ag.6   │  │    Ag.7        │  │   Ag.8   │  │    Ag.9     │  │ Especial   │ │
│  │Schedu- │  │   Analista     │  │Integrador│  │   Task      │  │ Recruiter  │ │
│  │ ling   │  │   Feedback     │  │   ATS    │  │  Planner    │  │ Assistant  │ │
│  └────────┘  └────────────────┘  └──────────┘  └─────────────┘  └────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 31.3 Tabela de Agentes

| ID | Agente | Classe | Responsabilidades |
|----|--------|--------|-------------------|
| Ag.0 | Orchestrator | `Orchestrator` | Roteamento, memória, delegação |
| Ag.1 | JobIntakeAgent | `job_intake_agent.py` | Wizard de vagas (etapas 1-5) |
| Ag.2 | SourcingAgent | `sourcing_agent.py` | Busca de candidatos, Pearch AI |
| Ag.3 | TriagemCurricularAgent | `triagem_curricular_agent.py` | Parsing de CV, triagem inicial |
| Ag.4 | EntrevistadorAgent | `entrevistador_agent.py` | Entrevistas WhatsApp/Voice |
| Ag.5 | AvaliadorWSIAgent | `avaliador_wsi_agent.py` | Avaliação científica WSI |
| Ag.6 | SchedulingAgent | `scheduling_agent.py` | Agendamento (Microsoft Graph) |
| Ag.7 | AnalistaFeedbackAgent | `analista_feedback_agent.py` | KPIs, relatórios, comunicação |
| Ag.8 | IntegradorATSAgent | `integrador_ats_agent.py` | Sync ATS (Gupy, Pandapé, etc.) |
| Ag.9 | TaskPlannerAgent | `task_planner_agent.py` | Decomposição de tarefas, DAG |
| Esp. | RecruiterAssistantAgent | `recruiter_assistant_agent.py` | Briefing diário, assistência |

### 31.4 Agentes Legados (Deprecated)

| Agente | Substituição | Status |
|--------|--------------|--------|
| ScreeningAgent | TriagemCurricular + Entrevistador + AvaliadorWSI | Deprecated |
| CommunicationAgent | AnalistaFeedbackAgent | Deprecated |
| AnalyticsAgent | AnalistaFeedbackAgent | Deprecated |

> **Nota**: A arquitetura anterior com 13 agentes foi consolidada para 9 agentes ativos, com funcionalidades redistribuídas para maior eficiência.

---

### 31.5 Detalhamento de Agentes (Arquitetura Anterior - Referência)

A documentação detalhada abaixo mantém os detalhes técnicos dos agentes para referência de reconstrução:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORQUESTRADOR CENTRAL                             │
│                    (WizardOrchestratorService + LangGraph)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ JobIntake   │  │ Sourcing    │  │ Screening   │  │ Triagem     │        │
│  │ Agent       │  │ Agent       │  │ Agent       │  │ Curricular  │        │
│  │             │  │             │  │             │  │ Agent       │        │
│  │ • Criação   │  │ • Busca     │  │ • Perguntas │  │ • Análise   │        │
│  │   de vagas  │  │   ativa     │  │   triagem   │  │   currículos│        │
│  │ • Fast Track│  │ • Matching  │  │ • Scoring   │  │ • Extração  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Avaliador   │  │ Entrevista- │  │ Scheduling  │  │ Recruiter   │        │
│  │ WSI Agent   │  │ dor Agent   │  │ Agent       │  │ Assistant   │        │
│  │             │  │             │  │             │  │ Agent       │        │
│  │ • WSI Score │  │ • Condução  │  │ • Agenda    │  │ • Chat LIA  │        │
│  │ • 7 blocos  │  │   entrevista│  │ • Conflitos │  │ • Sugestões │        │
│  │ • Fit Score │  │ • Avaliação │  │ • Lembretes │  │ • Insights  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Analytics   │  │ Communica-  │  │ Integrador  │  │ Task        │        │
│  │ Agent       │  │ tion Agent  │  │ ATS Agent   │  │ Planner     │        │
│  │             │  │             │  │             │  │ Agent       │        │
│  │ • Métricas  │  │ • Templates │  │ • Gupy      │  │ • Backlog   │        │
│  │ • Dashboards│  │ • Multi-    │  │ • Pandapé   │  │ • Priorização│       │
│  │ • Relatórios│  │   canal     │  │ • Merge     │  │ • Follow-ups│        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                   Analista Feedback Agent                    │           │
│  │  • Coleta feedback do recrutador • Aprende com correções    │           │
│  │  • Atualiza patterns • Alimenta learning loop               │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 31.2 Agentes Especializados

| Agente | Arquivo | Responsabilidade Principal |
|--------|---------|---------------------------|
| **JobIntakeAgent** | `job_intake_agent.py` (188KB) | Criação de vagas, Fast Track, coleta de requisitos |
| **SourcingAgent** | `sourcing_agent.py` (78KB) | Busca ativa de candidatos, matching inteligente |
| **ScreeningAgent** | `screening_agent.py` (15KB) | Perguntas de triagem, scoring inicial |
| **TriagemCurricularAgent** | `triagem_curricular_agent.py` (58KB) | Análise de currículos, extração de dados |
| **AvaliadorWSIAgent** | `avaliador_wsi_agent.py` (69KB) | Avaliação WSI, 7 blocos, fit score |
| **EntrevistadorAgent** | `entrevistador_agent.py` (47KB) | Condução de entrevistas, avaliação |
| **SchedulingAgent** | `scheduling_agent.py` (62KB) | Agendamento, conflitos, lembretes |
| **RecruiterAssistantAgent** | `recruiter_assistant_agent.py` (111KB) | Chat LIA, sugestões proativas |
| **AnalyticsAgent** | `analytics_agent.py` (17KB) | Métricas, dashboards, relatórios |
| **CommunicationAgent** | `communication_agent.py` (13KB) | Templates, multi-canal |
| **IntegradorATSAgent** | `integrador_ats_agent.py` (26KB) | Integrações Gupy, Pandapé, Merge |
| **TaskPlannerAgent** | `task_planner_agent.py` (33KB) | Backlog, priorização, follow-ups |
| **AnalistaFeedbackAgent** | `analista_feedback_agent.py` (83KB) | Feedback, aprendizado, patterns |

### 31.3 BaseAgent e Herança

```python
class BaseAgent(ABC):
    """Classe base para todos os agentes da LIA."""
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        llm_client: Any,
        tools: List[Any] = None,
        memory: Any = None
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.tools = tools or []
        self.memory = memory
    
    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResponse:
        """Processa uma tarefa e retorna resposta."""
        pass
    
    @abstractmethod
    async def can_handle(self, task: AgentTask) -> bool:
        """Verifica se o agente pode processar a tarefa."""
        pass
```

### 31.4 AgentRegistry

O `AgentRegistry` centraliza o registro e descoberta de agentes:

```python
class AgentRegistry:
    """Registro central de agentes."""
    
    _agents: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """Registra um agente no sistema."""
        cls._agents[agent.name] = agent
    
    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        """Retorna agente por nome."""
        return cls._agents.get(name)
    
    @classmethod
    def find_agent_for_task(cls, task: AgentTask) -> Optional[BaseAgent]:
        """Encontra agente apropriado para a tarefa."""
        for agent in cls._agents.values():
            if agent.can_handle(task):
                return agent
        return None
```

### 31.5 Robustez e Error Handling

```
lia-agent-system/app/agents/robustness/
├── error_handling.py      # AgentError, AgentErrorCode, AgentErrorResponse
├── input_validation.py    # Schemas de validação por tipo de input
├── enhanced_base.py       # EnhancedBaseAgent, RobustAgentMixin
└── enhanced_registry.py   # EnhancedAgentRegistry com circuit breaker
```

**Tipos de Erro:**
- `VALIDATION_ERROR`: Input inválido
- `TIMEOUT_ERROR`: Timeout de processamento
- `LLM_ERROR`: Falha na chamada LLM
- `TOOL_ERROR`: Falha na execução de tool
- `UNKNOWN_ERROR`: Erro não categorizado

---

## 32. Sistema de Prompts

### 32.1 Estrutura de Arquivos

```
lia-agent-system/app/agents/prompts/
├── __init__.py              # Exports públicos
├── agent_prompts.py         # Definições dos prompts (50KB)
├── prompt_registry.py       # Sistema de versionamento (16KB)
├── README.md                # Guia de convenções (10KB)
└── examples/                # Exemplos de uso
```

### 32.2 Componentes Compartilhados

Todos os prompts de agentes compartilham componentes base:

```python
LIA_PERSONA = """
Você é LIA (Learning Intelligence Assistant), uma assistente de IA 
especializada em recrutamento e seleção da WeDoTalent.

PERSONALIDADE:
- Tom: Profissional, empático, consultivo
- Comunicação: Clara, objetiva, sem jargões desnecessários
- Postura: Parceira estratégica, não robô

PRINCÍPIOS:
- Sempre priorize a experiência do candidato
- Sugira, nunca imponha decisões
- Aprenda com feedback do recrutador
- Mantenha confidencialidade absoluta
"""

ETHICAL_GUIDELINES = """
DIRETRIZES ÉTICAS OBRIGATÓRIAS:
1. Nunca discrimine por gênero, raça, idade, orientação sexual
2. Não use informações protegidas para decisões
3. Sempre explique o raciocínio por trás das recomendações
4. Permita override humano em todas as decisões
5. Registre auditoria de todas as ações sensíveis
"""

HR_VOCABULARY = """
Termos técnicos de RH para usar naturalmente:
- **Recrutamento**: pipeline, funil, conversão, time-to-fill
- **Seleção**: fit cultural, fit técnico, soft skills, hard skills
- **WSI**: WeDoTalent Skill Index, score, blocos, pesos
- **Pipeline**: etapas, stages, kanban, movimentação
"""

DATA_PERSISTENCE_GUIDELINES = """
PERSISTÊNCIA DE DADOS (OBRIGATÓRIO):
1. Sempre salve dados extraídos no JobDraft
2. Registre interações para learning loop
3. Mantenha histórico de conversas
4. Capture feedback implícito e explícito
"""
```

### 32.3 Estrutura Padrão de Prompt

```python
AGENT_NAME_PROMPT = f"""{LIA_PERSONA}

{ETHICAL_GUIDELINES}

Você é o Agente [N] da LIA - [Nome do Agente].

## Sua Identidade
- Nome: [Nome]
- Papel: [Descrição do papel]
- Expertise: [Áreas de especialização]

## Vocabulário Esperado nas Respostas
{HR_VOCABULARY}

## Suas Responsabilidades
- [Responsabilidade 1]
- [Responsabilidade 2]

## [Seção Específica do Agente]
[Conteúdo específico: metodologias, fluxos, etc.]

## Persistência de Dados (OBRIGATÓRIO)
{DATA_PERSISTENCE_GUIDELINES}

## Formato de Resposta
[Especificações de formato: JSON, texto, etc.]
"""
```

### 32.4 Prompt Registry (Versionamento)

```python
class PromptRegistry:
    """Sistema de versionamento de prompts."""
    
    _prompts: Dict[str, PromptVersion] = {}
    
    @classmethod
    def register_prompt(
        cls,
        name: str,
        content: str,
        version: str,
        author: str,
        changelog: str
    ) -> None:
        """Registra uma nova versão de prompt."""
        cls._prompts[name] = PromptVersion(
            name=name,
            content=content,
            version=version,
            author=author,
            changelog=changelog,
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def get_prompt(cls, name: str) -> Optional[str]:
        """Retorna o conteúdo do prompt."""
        prompt = cls._prompts.get(name)
        return prompt.content if prompt else None
    
    @classmethod
    def get_version(cls, name: str) -> Optional[str]:
        """Retorna a versão atual do prompt."""
        prompt = cls._prompts.get(name)
        return prompt.version if prompt else None
```

### 32.5 Prompts Registrados

| Prompt | Versão | Descrição |
|--------|--------|-----------|
| `orchestrator` | 3.2.0 | Orquestrador central |
| `job_intake` | 4.1.0 | Criação de vagas |
| `sourcing` | 2.5.0 | Busca ativa |
| `screening` | 2.3.0 | Triagem inicial |
| `wsi_evaluator` | 3.0.0 | Avaliação WSI |
| `interviewer` | 2.8.0 | Entrevistas |
| `scheduler` | 2.1.0 | Agendamento |
| `assistant` | 4.0.0 | Chat principal |
| `analytics` | 2.0.0 | Métricas |
| `communication` | 2.4.0 | Multi-canal |
| `ats_integrator` | 1.8.0 | Integrações ATS |
| `task_planner` | 2.2.0 | Planejamento |
| `feedback_analyst` | 3.1.0 | Análise feedback |

---

## 33. Integrações LLM e Provedores de IA

### 33.1 Provedores Configurados

| Provedor | Modelo Principal | Uso |
|----------|------------------|-----|
| **Anthropic** | Claude 3.5 Sonnet | Agentes principais, raciocínio complexo |
| **OpenAI** | GPT-4 Turbo | Embeddings, backup |
| **Google Gemini** | Gemini Pro | Análise multimodal (imagens, vídeos) |
| **Deepgram** | Nova-2 | Speech-to-Text (voice) |
| **OpenAI TTS** | TTS-1 | Text-to-Speech (voice) |

### 33.2 Configuração (`config.py`)

```python
class Settings(BaseSettings):
    # Anthropic (Principal)
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_MAX_TOKENS: int = 4096
    
    # OpenAI (Embeddings + Backup)
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    
    # Google Gemini (Multimodal)
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-pro-vision"
    
    # Voice
    DEEPGRAM_API_KEY: str
    OPENAI_TTS_MODEL: str = "tts-1"
```

### 33.3 Hierarquia de Fallback

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELEÇÃO DE MODELO LLM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tarefa Recebida                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────┐                                        │
│  │ Análise Multimodal? │──────Sim────▶ Gemini Pro Vision        │
│  └─────────────────────┘                                        │
│       │ Não                                                      │
│       ▼                                                          │
│  ┌─────────────────────┐                                        │
│  │ Embedding/Search?   │──────Sim────▶ OpenAI text-embedding-3  │
│  └─────────────────────┘                                        │
│       │ Não                                                      │
│       ▼                                                          │
│  ┌─────────────────────┐                                        │
│  │ Raciocínio Complexo?│──────Sim────▶ Claude 3.5 Sonnet        │
│  └─────────────────────┘                                        │
│       │ Não                                                      │
│       ▼                                                          │
│  ┌─────────────────────┐                                        │
│  │ Tarefa Simples      │──────────────▶ Claude (default)        │
│  └─────────────────────┘                                        │
│                                                                  │
│  Fallback: Se Claude falhar ───────────▶ GPT-4 Turbo            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 33.4 Tool Calling System

O sistema possui **26+ tools registradas** que permitem à LIA executar ações reais:

**Categorias de Tools:**

| Categoria | Quantidade | Exemplos |
|-----------|------------|----------|
| **Job Management** | 12 | `create_job`, `update_job`, `publish_job` |
| **Candidate Management** | 10 | `update_stage`, `add_note`, `schedule_interview` |
| **Communication** | 8 | `send_email`, `send_whatsapp`, `send_sms` |
| **Search & Sourcing** | 7 | `search_candidates`, `search_local`, `source_linkedin` |
| **Analytics** | 6 | `get_metrics`, `generate_report`, `predict_time_to_fill` |
| **WSI Evaluation** | 5 | `calculate_wsi`, `get_fit_score`, `generate_questions` |
| **ATS Integration** | 5 | `sync_gupy`, `sync_pandape`, `import_candidates` |
| **Calendar** | 4 | `get_availability`, `create_event`, `send_reminder` |
| **Templates** | 2 | `search_templates`, `apply_template` |

**Estrutura de Tool:**

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    requires_confirmation: bool = False
    tenant_scoped: bool = True

class ToolExecutionContext:
    """Contexto de execução com tenant scoping."""
    company_id: str
    user_id: str
    session_id: str
    permissions: List[str]
```

### 33.5 Cache e Otimização de Tokens

#### 33.5.1 Estratégias de Cache

O sistema utiliza múltiplas camadas de cache para reduzir custos e latência:

| Camada | Tecnologia | TTL | Uso |
|--------|------------|-----|-----|
| **L1 - Response Cache** | Redis | 1h | Respostas idênticas de LLM |
| **L2 - Embedding Cache** | Redis | 24h | Embeddings de textos |
| **L3 - Pattern Cache** | PostgreSQL | 7d | Padrões detectados por empresa |
| **L4 - Template Cache** | Memory | Session | Templates compilados |

#### 33.5.2 AICacheService

```python
class AICacheService:
    """Cache para respostas de LLM."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hora
    
    async def get_cached_response(
        self,
        prompt_hash: str,
        model: str
    ) -> Optional[str]:
        """Busca resposta em cache."""
        key = f"ai_cache:{model}:{prompt_hash}"
        return await self.redis.get(key)
    
    async def cache_response(
        self,
        prompt_hash: str,
        model: str,
        response: str
    ) -> None:
        """Armazena resposta em cache."""
        key = f"ai_cache:{model}:{prompt_hash}"
        await self.redis.setex(key, self.ttl, response)
    
    def generate_prompt_hash(self, prompt: str, context: dict) -> str:
        """Gera hash determinístico para prompt + contexto."""
        content = f"{prompt}:{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
```

#### 33.5.3 Otimização de Tokens

**Estratégias implementadas:**

| Estratégia | Economia | Descrição |
|------------|----------|-----------|
| **Prompt Compression** | ~30% | Remove redundância em prompts longos |
| **Context Windowing** | ~40% | Envia apenas contexto relevante |
| **Batch Processing** | ~25% | Agrupa requisições similares |
| **Incremental Updates** | ~50% | Envia apenas deltas de mudanças |

**Configurações por modelo:**

```python
TOKEN_LIMITS = {
    "claude-sonnet-4-20250514": {
        "max_input": 200000,
        "max_output": 4096,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015
    },
    "gpt-4o": {
        "max_input": 128000,
        "max_output": 4096,
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015
    },
    "gemini-2.0-flash": {
        "max_input": 1000000,
        "max_output": 8192,
        "cost_per_1k_input": 0.00035,
        "cost_per_1k_output": 0.0014
    }
}
```

#### 33.5.4 Prompt Caching (Anthropic)

Utilizamos o cache de prompts da Anthropic para reduzir custos em prompts com prefixos repetitivos:

```python
async def call_with_cache(self, system_prompt: str, user_message: str):
    """Usa cache de prompt da Anthropic para prefixos estáticos."""
    response = await self.client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Cache por 5 min
            }
        ],
        messages=[{"role": "user", "content": user_message}]
    )
    return response
```

#### 33.5.5 Métricas de Economia

| Período | Tokens Input | Tokens Output | Custo | Economia com Cache |
|---------|--------------|---------------|-------|-------------------|
| Sem cache | 10M/dia | 2M/dia | ~$80/dia | - |
| Com cache L1 | 6M/dia | 2M/dia | ~$55/dia | 31% |
| Com todas camadas | 4M/dia | 1.5M/dia | ~$35/dia | 56% |

### 33.6 Token Economy Architecture (v7.2)

O sistema implementa uma arquitetura de cache em 3 camadas para economizar tokens de LLM e acelerar respostas:

```
┌─────────────────────────────────────────────────────────────────┐
│                   TOKEN ECONOMY ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   LAYER 1    │    │   LAYER 2    │    │   LAYER 3    │       │
│  │   Session    │ →  │    Redis     │ →  │  PostgreSQL  │       │
│  │   (1 hour)   │    │  (7 days)    │    │  (30 days)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│   In-memory          Short TTL           Long TTL               │
│   Per conversation   Volatile data       Stable patterns        │
│   Acesso instantâneo Fallback gracioso   Padrões consolidados   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Camada | TTL | Dados | Uso |
|--------|-----|-------|-----|
| **L1: SessionCache** | 1 hora | Contexto de conversa atual | Acesso instantâneo, sem I/O |
| **L2: RedisCache** | 7 dias | Sugestões, market data | Dados voláteis, fallback se indisponível |
| **L3: PostgresCache** | 30 dias | Padrões consolidados, embeddings | Dados estáveis, learning patterns |

**Componentes Implementados:**
- `CacheManagerService` (`cache_manager_service.py`): Orquestra as 3 camadas
- `SessionCache`: Cache em memória por sessão de conversa
- `CacheEntry` (model): Persistência L3 com hit tracking
- `QueryEmbedding` (model): Similaridade semântica para cache hits

### 33.7 IntelligentDataOrchestrator

O `IntelligentDataOrchestrator` consolida dados de **5 fontes** com priorização baseada em confiança:

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA SOURCE PRIORITY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRIORITY 1: Learning Patterns ───────── VERY_HIGH (95%)        │
│              (Preferências históricas da empresa)                │
│                          │                                       │
│  PRIORITY 2: Company Config ─────────── HIGH (85%)              │
│              (Políticas explícitas de RH)                        │
│                          │                                       │
│  PRIORITY 3: Job Insights ───────────── HIGH (85%)              │
│              (Dados internos da LIA)                             │
│                          │                                       │
│  PRIORITY 4: ATS History ────────────── MEDIUM (70%)            │
│              (Histórico de ATSs conectados)                      │
│                          │                                       │
│  PRIORITY 5: Market Benchmark ───────── LOW_MEDIUM (55%)        │
│              (Dados externos de mercado)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fluxo de Consulta:**
1. Verifica cache (Session → Redis → PostgreSQL)
2. Se cache miss, consulta fontes em ordem de prioridade
3. Ordena resultados por confiança
4. Detecta consenso entre fontes (threshold: 20% de variação)
5. Armazena resultado no cache
6. Captura feedback silencioso para learning loop

**Tools Disponíveis para o Wizard:**

| Tool | Descrição | Schema |
|------|-----------|--------|
| `get_intelligent_salary` | Salário consolidado de múltiplas fontes | company_id, job_title, seniority, location |
| `get_intelligent_skills` | Skills consolidadas com categorização | company_id, job_title, seniority, limit |
| `capture_wizard_feedback` | Captura silenciosa de feedback | field_name, suggested_value, final_value |

### 33.8 Learning Loop Silencioso

O sistema captura feedback **silenciosamente** sem alterar a UX:

```
┌─────────────────────────────────────────────────────────────────┐
│                   SILENT LEARNING LOOP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CAPTURE                 ANALYZE                  APPLY         │
│   ────────                ───────                  ─────         │
│   ┌─────────┐            ┌─────────┐            ┌─────────┐     │
│   │Feedback │ ────────►  │Learning │ ────────►  │Improved │     │
│   │Events   │            │Patterns │            │Suggest. │     │
│   └─────────┘            └─────────┘            └─────────┘     │
│        │                      │                      │           │
│        ▼                      ▼                      ▼           │
│   Silently records      Detects patterns       Uses patterns    │
│   accepted/modified/    from accumulated       for better       │
│   rejected values       feedback data          suggestions      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tipos de Outcome Capturados:**
- `accepted`: Usuário aceitou sugestão sem modificar
- `modified`: Usuário ajustou o valor sugerido
- `rejected`: Usuário rejeitou explicitamente

**Thresholds de Confiança para Patterns:**
- **Alta Confiança**: 20+ amostras, acceptance rate > 75%
- **Média Confiança**: 10+ amostras, acceptance rate > 50%
- **Baixa Confiança**: 5+ amostras
- **Promoção**: Pattern promovido se acceptance rate > 75%
- **Demoção**: Pattern demovido se acceptance rate < 25%

**Modelos de Dados:**

```python
# Eventos de Feedback (captura silenciosa)
class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    company_id: str           # Tenant
    field_name: str           # Campo afetado (salary, skills, etc.)
    suggested_value: JSON     # O que foi sugerido
    final_value: JSON         # O que usuário usou
    outcome: str              # accepted | modified | rejected
    processed_for_learning: bool  # Já gerou pattern?

# Padrões Aprendidos
class LearningPattern(Base):
    __tablename__ = "learning_patterns"
    company_id: str           # Tenant
    pattern_type: str         # salary_adjustment, skill_preference, etc.
    pattern_value: JSON       # Valor do padrão
    sample_size: int          # Quantas amostras geraram
    acceptance_rate: float    # Taxa de aceitação
    confidence_score: float   # Score 0-1
```

---

## 33.9 Integrações ATS/HRIS

### 33.9.1 Provedores Implementados

| Provedor | Tipo | Cobertura | Arquivo |
|----------|------|-----------|---------|
| **Gupy** | Nativo | Brasil | `ats_clients/gupy.py` |
| **Pandapé** | Nativo | Brasil | `ats_clients/pandape.py` |
| **StackOne** | Universal | 50+ ATS | `ats_clients/stackone.py` |
| **Merge** | Universal | 200+ ATS/HRIS | `ats_clients/merge.py` |

### 33.9.2 Funcionalidades de Sync

```python
class ATSClient(ABC):
    """Interface base para clientes ATS"""
    
    @abstractmethod
    async def sync_jobs(self) -> List[Job]:
        """Sincroniza vagas do ATS"""
        pass
    
    @abstractmethod
    async def sync_candidates(self, job_id: str) -> List[Candidate]:
        """Sincroniza candidatos do ATS"""
        pass
    
    @abstractmethod
    async def update_status(self, candidate_id: str, status: str) -> bool:
        """Atualiza status do candidato no ATS"""
        pass
    
    @abstractmethod
    async def publish_job(self, job: Job) -> str:
        """Publica vaga no ATS"""
        pass
```

### 33.9.3 Benefícios da Integração ATS

| Benefício | Descrição |
|-----------|-----------|
| **Dados Históricos** | Acesso a vagas passadas para learning |
| **Sync Bidirecional** | Publicação e atualização de status |
| **Candidatos Unificados** | Base única com múltiplas fontes |
| **Automação de Status** | Movimentação automática no funil |

---

## 34. Serviços Principais

### 34.1 Contagem de Serviços

O backend possui **177+ serviços** organizados por domínio:

```
lia-agent-system/app/services/
├── Core Services (30+)
│   ├── conversation_manager.py
│   ├── learning_hub_service.py
│   ├── automation_service.py
│   └── notification_service.py
│
├── AI/ML Services (15+)
│   ├── ml/outcome_predictor.py
│   ├── ml/feature_engineering.py
│   ├── ai_cache_service.py
│   └── embedding_service.py
│
├── Wizard Services (10+)
│   ├── wizard_orchestrator_service.py
│   ├── wizard_analytics_service.py
│   ├── job_template_service.py
│   └── intelligence_layer_service.py
│
├── Integration Services (20+)
│   ├── ats_clients/gupy.py
│   ├── ats_clients/pandape.py
│   ├── ats_clients/merge.py
│   ├── pearch_service.py
│   └── calendar_service.py
│
├── Communication Services (15+)
│   ├── email_service.py
│   ├── communication_service.py
│   ├── whatsapp_service.py
│   └── notification_service.py
│
└── Analytics Services (10+)
    ├── predictive_analytics_service.py
    ├── search_analytics_service.py
    └── pattern_detector_service.py
```

### 34.2 Serviços Críticos do Wizard

| Serviço | Responsabilidade |
|---------|------------------|
| `WizardOrchestratorService` | Coordenação do wizard, roteamento de intents |
| `WizardAnalyticsService` | Métricas do wizard, tracking de tempo |
| `IntelligenceLayerService` | Camada de inteligência, sugestões |
| `JobTemplateService` | Busca e aplicação de templates |
| `FeedbackLearningService` | Captura de feedback, learning loop |
| `RecruiterPersonalizationService` | Personalização por recrutador |
| `SkillsCatalogService` | Catálogo de skills, autocomplete |
| `SalaryBenchmarkService` | Benchmarks de mercado |

---

> **Documento mantido por**: Equipe LIA  
> **Última revisão**: 04 de Fevereiro de 2026  
> **Versão**: 7.2 (Orquestração Inteligente + Integrações ATS)  
> **Documentos consolidados nesta versão**:
> - `docs/FLUXO_WIZARD_VAGA_COMPLETO.md` → Seção 24
> - `docs/SETTINGS_MENU_MAPPING_FOR_WIZARD.md` → Seção 25
> - `docs/LIA_PROACTIVE_ANALYSIS_SYSTEM.md` → Seção 26
> - `docs/proposals/clustering-embeddings-proposal.md` → Seção 27
> - Learning Loop + Importação de JDs → Seção 28
> - Fast Track + Templates Curados → Seções 29 e 30
> - Arquitetura Multi-Agente → Seção 31
> - Sistema de Prompts → Seção 32
> - Integrações LLM → Seção 33
> - Serviços Principais → Seção 34
> - `docs/templates/TAXONOMIA_TEMPLATES.md` → Referência
> - `lia-agent-system/app/agents/prompts/README.md` → Referência
>
> **Próxima revisão planejada**: Março 2026

---

## 35. Arquivos Críticos para Reconstrução

> **Objetivo**: Lista completa de todos os arquivos essenciais para reconstruir a plataforma LIA, organizados por categoria.

### 35.1 LangGraph/LangChain Core (Orchestration)

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/orchestrator/orchestrator.py` | Orquestrador principal multi-agente com roteamento |
| `lia-agent-system/app/orchestrator/intent_router.py` | Classificador de intenções (15 intents, 3 modos) |
| `lia-agent-system/app/orchestrator/task_planner.py` | Planejamento e decomposição de tarefas |
| `lia-agent-system/app/services/llm.py` | Configuração LLM (Claude/GPT-4/Gemini fallback) |
| `lia-agent-system/app/services/graph_runner.py` | Executor de StateGraphs LangGraph |
| `lia-agent-system/app/config/langsmith.py` | Integração LangSmith para observabilidade |

### 35.2 State Graphs e Nodes

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/agents/job_wizard_graph.py` | StateGraph principal do Wizard (7 etapas) |
| `lia-agent-system/app/agents/conversation.py` | Graph conversacional persistente |
| `lia-agent-system/app/agents/job_vacancy_nodes.py` | Nodes de criação e edição de vagas |
| `lia-agent-system/app/agents/sourcing_engagement_nodes.py` | Nodes de sourcing e engajamento |
| `lia-agent-system/app/models/graph_session.py` | Persistência de sessão do graph |

### 35.3 Agentes Especializados (9 Agentes Ativos)

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/agents/base_agent.py` | BaseAgent (classe base com herança) |
| `lia-agent-system/app/agents/agent_registry.py` | AgentRegistry (discovery e instanciação) |
| `lia-agent-system/app/agents/specialized/job_intake_agent.py` | Criação de vagas e Fast Track |
| `lia-agent-system/app/agents/specialized/sourcing_agent.py` | Busca ativa de candidatos |
| `lia-agent-system/app/agents/specialized/screening_agent.py` | Triagem por questionário |
| `lia-agent-system/app/agents/specialized/triagem_curricular_agent.py` | Análise de CVs |
| `lia-agent-system/app/agents/specialized/avaliador_wsi_agent.py` | Avaliação WSI 7 blocos |
| `lia-agent-system/app/agents/specialized/entrevistador_agent.py` | Condução de entrevistas |
| `lia-agent-system/app/agents/specialized/scheduling_agent.py` | Agendamento inteligente |
| `lia-agent-system/app/agents/specialized/recruiter_assistant_agent.py` | Assistência geral |
| `lia-agent-system/app/agents/specialized/analytics_agent.py` | Relatórios e métricas |
| `lia-agent-system/app/agents/specialized/communication_agent.py` | Multi-canal (email, WhatsApp) |
| `lia-agent-system/app/agents/specialized/integrador_ats_agent.py` | Sincronização ATS |
| `lia-agent-system/app/agents/specialized/task_planner_agent.py` | Planejamento de atividades |
| `lia-agent-system/app/agents/specialized/analista_feedback_agent.py` | Loop de aprendizagem |

### 35.4 Sistema de Prompts

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/agents/prompts/agent_prompts.py` | Prompts de todos os 9 agentes ativos |
| `lia-agent-system/app/agents/prompts/prompt_registry.py` | PromptRegistry com versionamento |
| `lia-agent-system/app/agents/prompts/shared_components.py` | LIA_PERSONA, ETHICAL_GUIDELINES |
| `lia-agent-system/app/agents/prompts/README.md` | Documentação de prompts |

### 35.5 Tool System (59+ Tools)

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/tools/job_wizard_tools.py` | Tools do Wizard (create_job, update_draft, etc.) |
| `lia-agent-system/app/tools/query_tools.py` | Tools de consulta (search, filter, aggregate) |
| `lia-agent-system/app/tools/candidate_tools.py` | Tools de candidatos (update_stage, add_note) |
| `lia-agent-system/app/tools/job_tools.py` | Tools de vagas (publish, close, clone) |
| `lia-agent-system/app/tools/export_tools.py` | Tools de exportação (PDF, Excel) |
| `lia-agent-system/app/tools/communication_tools.py` | Tools de comunicação (send_email, send_whatsapp) |
| `lia-agent-system/app/services/tool_executor_service.py` | Executor centralizado com ToolExecutionContext |

### 35.6 Templates Curados (361 Templates)

| Arquivo | Templates | Categorias |
|---------|-----------|------------|
| `lia-agent-system/app/data/curated_templates_tech.py` | 119 | desenvolvimento, dados, infra, segurança, design, gestão |
| `lia-agent-system/app/data/curated_templates_vendas.py` | 98 | inside_sales, field_sales, customer_success, canais |
| `lia-agent-system/app/data/curated_templates_rh.py` | 32 | recrutamento, bp, dp, remuneração, t&d |
| `lia-agent-system/app/data/curated_templates_administrativo.py` | 21 | geral, secretariado, facilities, compras |
| `lia-agent-system/app/data/curated_templates_financas.py` | 19 | contabilidade, fiscal, controladoria, tesouraria |
| `lia-agent-system/app/data/curated_templates_operacoes.py` | 14 | logística, supply_chain, qualidade |
| `lia-agent-system/app/data/curated_templates_saude.py` | 13 | enfermagem, medicina, terapias |
| `lia-agent-system/app/data/curated_templates_marketing.py` | 8 | digital, conteúdo, branding, performance |
| `lia-agent-system/app/data/curated_templates_cs.py` | 2 | cs_management, onboarding |
| `lia-agent-system/scripts/validate_templates.py` | - | Script de validação WSI Quality Gates |

### 35.7 Services Críticos (Top 50)

#### Core Services
| Arquivo | Descrição |
|---------|-----------|
| `app/services/wizard_orchestrator_service.py` | Orquestração do wizard |
| `app/services/intelligence_layer_service.py` | Camada de inteligência |
| `app/services/feedback_learning_service.py` | Loop de aprendizagem |
| `app/services/recruiter_personalization_service.py` | Personalização |
| `app/services/wsi_service.py` | Metodologia WSI |
| `app/services/memory_service.py` | Memória conversacional |
| `app/services/context_aggregator_service.py` | Agregação de contexto |

#### AI/ML Services
| Arquivo | Descrição |
|---------|-----------|
| `app/services/embedding_service.py` | Embeddings OpenAI (1536 dims) |
| `app/services/semantic_search_service.py` | Busca semântica |
| `app/services/rag_service.py` | Retrieval Augmented Generation |
| `app/services/multimodal_service.py` | Análise de imagem/vídeo |
| `app/services/cv_scoring_service.py` | Scoring de CVs |
| `app/services/culture_analyzer_service.py` | Análise cultural |

#### Wizard Services
| Arquivo | Descrição |
|---------|-----------|
| `app/services/jd_generator_service.py` | Geração de Job Description |
| `app/services/compensation_analysis_service.py` | Análise salarial |
| `app/services/skills_catalog_service.py` | Catálogo de skills |
| `app/services/job_template_service.py` | Templates de vagas |
| `app/services/job_insights_service.py` | Insights de mercado |

#### Integration Services
| Arquivo | Descrição |
|---------|-----------|
| `app/services/merge_ats_service.py` | Integração Merge (ATS) |
| `app/services/pearch_service.py` | Integração Pearch AI |
| `app/services/hubspot_service.py` | Integração HubSpot |
| `app/services/microsoft_graph_service.py` | Microsoft Graph |
| `app/services/whatsapp_service.py` | WhatsApp Business |

### 35.8 Models (Schemas de Dados)

| Arquivo | Descrição |
|---------|-----------|
| `app/models/job_draft.py` | JobDraft, DraftFieldHistory |
| `app/models/intelligence_layer.py` | IntelligenceInsight, PatternCache |
| `app/models/feedback_learning.py` | WizardFeedback, JobOutcome |
| `app/models/recruiter_profile.py` | RecruiterProfile, Preferences |
| `app/models/agent_activity.py` | Registro de atividades de agentes |
| `app/models/graph_session.py` | Persistência de sessão LangGraph |
| `app/models/wsi_evaluation.py` | Avaliações WSI |
| `app/models/candidate.py` | Candidato principal |
| `app/models/job_vacancy.py` | Vaga de emprego |
| `app/models/company.py` | Empresa/Tenant |

### 35.9 API Endpoints Críticos

| Arquivo | Endpoints |
|---------|-----------|
| `app/api/v1/chat.py` | `/chat`, `/orchestrator/pipeline-chat` |
| `app/api/v1/job_drafts.py` | CRUD de drafts |
| `app/api/v1/intelligence.py` | Sugestões e insights |
| `app/api/v1/wsi.py` | Avaliações WSI |
| `app/api/v1/screening.py` | Triagem de candidatos |
| `app/api/v1/sourcing.py` | Busca ativa |
| `app/api/v1/voice.py` | Integração de voz |
| `app/api/v1/agent_monitoring.py` | Monitoramento de agentes |

### 35.10 Documentação Arquitetural

| Arquivo | Conteúdo |
|---------|----------|
| `docs/proposals/job-wizard-enhancement-plan.md` | Este documento (4700+ linhas) |
| `docs/architecture/COMPLETE_SYSTEM_ARCHITECTURE.md` | Arquitetura C4 completa |
| `docs/architecture/agents/LIA_AGENT_ARCHITECTURE_COMPLETE.md` | Arquitetura de agentes |
| `docs/architecture/core/AI_EVOLUTION_STRATEGY.md` | Estratégia de evolução IA |
| `docs/architecture/core/AI_STAGE_AUTOMATION_ARCHITECTURE.md` | Automação de estágios |
| `docs/architecture/core/TECHNICAL_STACK.md` | Stack tecnológico |
| `docs/architecture/core/PORTABILITY_GUIDE.md` | Guia de portabilidade |
| `docs/adr/ADR-001-multi-agent-architecture.md` | ADR multi-agente |
| `docs/adr/ADR-002-observability-stack.md` | ADR observabilidade |
| `docs/LIA_METHODOLOGY.md` | Metodologia WSI completa |
| `docs/templates/TAXONOMIA_TEMPLATES.md` | Taxonomia de templates |

### 35.11 Configuração e Infraestrutura

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/main.py` | Entry point FastAPI |
| `lia-agent-system/app/config/settings.py` | Configurações centrais |
| `lia-agent-system/app/config/database.py` | Conexão PostgreSQL |
| `lia-agent-system/app/config/redis.py` | Configuração Redis |
| `lia-agent-system/requirements.txt` | Dependências Python |
| `plataforma-lia/package.json` | Dependências Node.js |
| `plataforma-lia/tailwind.config.ts` | Configuração Tailwind |

### 35.12 Resumo de Contagem

| Categoria | Quantidade |
|-----------|------------|
| **Arquivos Python Total** | 591 |
| **Arquivos LangGraph/LangChain** | 22 |
| **Agentes Especializados** | 9 (ativos) |
| **Tools Registrados** | 26+ |
| **Services** | 177+ |
| **Templates Curados** | 361 |
| **Integrações ATS** | 4 (Gupy, Pandapé, StackOne, Merge) |
| **Documentos MD** | 30+ |
| **Endpoints API** | 137 |

---

## 36. Fluxos Conversacionais Detalhados

> **Objetivo**: Scripts completos de diálogo da LIA para ambos os modos de criação de vagas, incluindo perguntas, interpretação de respostas e preenchimento automático de campos.

### 36.1 Filosofia Conversacional

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRINCÍPIO: CHAT É A INTERFACE PRINCIPAL                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ❌ ERRADO (Bot linear)           ✅ CORRETO (Assistente conversacional)   │
│   ┌─────────────────────────┐      ┌─────────────────────────────────────┐  │
│   │ Selecione uma opção:    │      │ Me conta sobre a vaga! Qual cargo   │  │
│   │ [ ] CLT                 │      │ você está abrindo?                  │  │
│   │ [ ] PJ                  │      └─────────────────────────────────────┘  │
│   │ [ ] Temporário          │                                               │
│   └─────────────────────────┘      Usuário: "Preciso de um dev sênior       │
│                                    para o time de dados, CLT, remoto"       │
│                                                                              │
│                                    ┌─────────────────────────────────────┐  │
│                                    │ Entendi! Vou criar:                 │  │
│                                    │ • Cargo: Dev Sênior - Dados         │  │
│                                    │ • Contrato: CLT                     │  │
│                                    │ • Modelo: Remoto                    │  │
│                                    │                                     │  │
│                                    │ Posso sugerir uma faixa salarial?   │  │
│                                    └─────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 36.2 MODO COMPLETO - Scripts por Etapa

#### Etapa 1: Abertura e Contexto Inicial

```
┌─ SCRIPT: INÍCIO DO WIZARD ───────────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Oi! Vamos criar uma nova vaga. Você pode:"                             │
│      "• Me contar tudo de uma vez (cargo, requisitos, salário...)"           │
│      "• Ou podemos ir passo a passo - o que preferir!"                       │
│                                                                               │
│ [Usuário responde de forma livre]                                             │
│                                                                               │
│ PROCESSAMENTO NLU:                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ Input: "Preciso de um engenheiro de dados sênior, CLT, remoto, React"   │  │
│ │                                                                          │  │
│ │ Campos Extraídos:                                                        │  │
│ │   job_title: "Engenheiro de Dados" (confiança: 95%)                     │  │
│ │   seniority: "senior" (confiança: 100%)                                 │  │
│ │   employment_type: "clt" (confiança: 100%)                              │  │
│ │   work_model: "remote" (confiança: 100%)                                │  │
│ │   skills_detected: ["React"] (confiança: 90%)                           │  │
│ │                                                                          │  │
│ │ Campos Pendentes:                                                        │  │
│ │   department, salary_range, benefits, responsibilities                  │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│ LIA: "Perfeito! Entendi que você precisa de um Engenheiro de Dados Sênior,  │
│       CLT, remoto. Vi que mencionou React - é uma skill obrigatória?"        │
│                                                                               │
│       [Painel Lateral: Formulário preenchido com campos detectados]          │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 2: Perguntas Contextuais (Campos Faltantes)

```
┌─ SCRIPT: COLETA DE INFORMAÇÕES ──────────────────────────────────────────────┐
│                                                                               │
│ REGRA: LIA faz perguntas agrupadas, não uma por uma                          │
│                                                                               │
│ LIA: "Para essa vaga de Engenheiro de Dados, preciso saber mais duas coisas:│
│       1. Qual departamento/área vai receber essa pessoa?"                    │
│       2. Já tem uma ideia de faixa salarial?"                                │
│                                                                               │
│ [Usuário responde]                                                            │
│ Usuário: "Área de BI, entre 15 e 20 mil"                                     │
│                                                                               │
│ PROCESSAMENTO:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ department: "BI" → normalizado para "Business Intelligence"             │  │
│ │ salary_min: 15000                                                        │  │
│ │ salary_max: 20000                                                        │  │
│ │                                                                          │  │
│ │ AÇÃO: Trigger CompensationAnalysisService                               │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│ LIA: "Ótimo! Área de BI, faixa de R$ 15-20k."                               │
│                                                                               │
│       "💡 Observação: Essa faixa está 11% abaixo da mediana de mercado     │
│        para Eng. Dados Sênior em São Paulo (R$ 18-25k). Quer que eu        │
│        ajuste ou mantemos assim?"                                            │
│                                                                               │
│ [Usuário responde: "mantém" / "ajusta" / linguagem natural]                  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 3: Competências Técnicas

```
┌─ SCRIPT: COMPETÊNCIAS (SKILLS) ──────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Agora vamos às competências técnicas. Para Eng. Dados Sênior, sugiro: │
│                                                                               │
│       **Obrigatórias** (baseado em vagas similares):"                        │
│       • Python (Avançado)"                                                   │
│       • SQL (Avançado)"                                                      │
│       • Spark/Databricks (Intermediário)"                                    │
│       • Airflow ou similar (Intermediário)"                                  │
│       • Cloud (AWS/GCP/Azure)"                                               │
│                                                                               │
│       **Desejáveis**:"                                                       │
│       • Kafka (Intermediário)"                                               │
│       • dbt (Básico)"                                                        │
│                                                                               │
│       "Quer usar essas ou prefere ajustar?"                                  │
│                                                                               │
│ [Usuário responde]                                                            │
│ Usuário: "adiciona Terraform e tira Kafka"                                   │
│                                                                               │
│ PROCESSAMENTO NLU:                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ Ação: ADD skill "Terraform" (inferir nível: Intermediário)              │  │
│ │ Ação: REMOVE skill "Kafka"                                               │  │
│ │                                                                          │  │
│ │ Painel Lateral: Atualiza lista de skills em tempo real                  │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│ LIA: "Feito! Adicionei Terraform e removi Kafka. A lista ficou assim:"      │
│       [Mostra resumo no chat]                                                 │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 4: Competências Comportamentais

```
┌─ SCRIPT: COMPORTAMENTAIS (SOFT SKILLS) ──────────────────────────────────────┐
│                                                                               │
│ LIA: "Para as competências comportamentais, baseado no perfil sênior e na   │
│       área de dados, sugiro:"                                                 │
│                                                                               │
│       • **Comunicação** - Apresentar insights para stakeholders não-técnicos│
│       • **Autonomia** - Conduzir projetos com mínima supervisão              │
│       • **Colaboração** - Trabalhar com times multidisciplinares             │
│                                                                               │
│       "Faz sentido para essa vaga? Quer adicionar ou trocar alguma?"         │
│                                                                               │
│ [Usuário responde]                                                            │
│ Usuário: "perfeito, mas adiciona resolução de problemas"                     │
│                                                                               │
│ LIA: "Adicionei! Agora temos 4 competências comportamentais."               │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 5: Responsabilidades

```
┌─ SCRIPT: RESPONSABILIDADES ──────────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Quais serão as principais responsabilidades? Posso sugerir algumas    │
│       baseadas em vagas similares de Eng. Dados Sênior:"                     │
│                                                                               │
│       1. Desenvolver e manter pipelines de dados escaláveis                  │
│       2. Modelar data warehouses e data lakes                                │
│       3. Garantir qualidade e governança dos dados                           │
│       4. Colaborar com cientistas de dados e analistas                       │
│       5. Documentar processos e arquitetura de dados                         │
│                                                                               │
│       "Quer usar essas como base ou me conta as específicas da vaga?"        │
│                                                                               │
│ [Usuário responde]                                                            │
│ Usuário: "usa essas e adiciona: liderar iniciativas de DataOps"             │
│                                                                               │
│ LIA: "Perfeito! Adicionei 'Liderar iniciativas de DataOps' como 6ª."        │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 6: Perguntas WSI (Screening)

```
┌─ SCRIPT: PERGUNTAS WSI ──────────────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Agora vou gerar as perguntas de triagem WSI. Elas avaliam tanto      │
│       conhecimento técnico quanto comportamental."                           │
│                                                                               │
│       "Gerando perguntas..."                                                  │
│                                                                               │
│       ┌─────────────────────────────────────────────────────────────────┐    │
│       │ **Pergunta 1** (Técnica - Python)                                │    │
│       │ "Descreva um caso onde você otimizou um pipeline de dados       │    │
│       │  que estava com problemas de performance. Qual foi o problema,  │    │
│       │  sua abordagem e o resultado?"                                   │    │
│       │                                                                  │    │
│       │ Avalia: Bloom L4 (Análise) + Dreyfus L4 (Proficiente)          │    │
│       ├─────────────────────────────────────────────────────────────────┤    │
│       │ **Pergunta 2** (Comportamental - Comunicação)                   │    │
│       │ "Como você explica conceitos técnicos de dados para             │    │
│       │  stakeholders de negócio? Dê um exemplo específico."            │    │
│       │                                                                  │    │
│       │ Avalia: Big Five (Extroversão + Abertura)                       │    │
│       ├─────────────────────────────────────────────────────────────────┤    │
│       │ **Pergunta 3** (Técnica - Arquitetura)                          │    │
│       │ "Se você precisasse projetar um data lake do zero, quais        │    │
│       │  decisões arquiteturais você tomaria e por quê?"                │    │
│       │                                                                  │    │
│       │ Avalia: Bloom L5 (Síntese) + Dreyfus L5 (Expert)               │    │
│       └─────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│ LIA: "Gerei 5 perguntas WSI. Quer revisar ou ajustar alguma?"               │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 7: Review e Publicação

```
┌─ SCRIPT: REVIEW FINAL ───────────────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Tudo pronto! Aqui está o resumo da vaga:"                             │
│                                                                               │
│       [Painel Lateral: Preview completo da vaga]                              │
│                                                                               │
│       "📋 **Engenheiro de Dados Sênior**                                     │
│        📍 Remoto | 💼 CLT | 💰 R$ 15.000 - R$ 20.000                        │
│                                                                               │
│        **Skills**: Python, SQL, Spark, Airflow, AWS, Terraform, dbt          │
│        **Comportamentais**: Comunicação, Autonomia, Colaboração, Resolução   │
│        **Responsabilidades**: 6 definidas                                     │
│        **Perguntas WSI**: 5 configuradas                                      │
│                                                                               │
│        ✅ Quality Gates: Todos aprovados"                                     │
│                                                                               │
│ LIA: "Quer publicar agora ou fazer algum ajuste antes?"                      │
│                                                                               │
│ [Usuário responde: "publica" / ajuste específico]                             │
│                                                                               │
│ SE "publica":                                                                 │
│   LIA: "Vaga publicada com sucesso! 🎉"                                      │
│         "Ativei o sourcing automático e vou te avisar quando chegarem"       │
│         "os primeiros candidatos."                                            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 36.3 MODO FAST TRACK - Scripts Completos

#### Etapa 1: Seleção de Template

```
┌─ SCRIPT: FAST TRACK - INÍCIO ────────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Modo Fast Track ativado! ⚡ Vamos criar essa vaga em minutos."         │
│                                                                               │
│       "Encontrei algumas opções para você:"                                   │
│                                                                               │
│       **Suas Vagas Anteriores** (mais preciso)                               │
│       ┌─────────────────────────────────────────────────────────────────┐    │
│       │ 📋 Eng. de Dados Pleno (Abr/2025) - 87% compatível              │    │
│       │ 📋 Cientista de Dados Jr (Mar/2025) - 72% compatível            │    │
│       └─────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│       **Templates Curados** (361 disponíveis)                                │
│       ┌─────────────────────────────────────────────────────────────────┐    │
│       │ 📄 Eng. de Dados Sênior (Template Tecnologia)                   │    │
│       │ 📄 Data Engineer Sr (Template Dados)                            │    │
│       │ 📄 Arquiteto de Dados (Template Dados)                          │    │
│       └─────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│       "Qual você quer usar como base?"                                        │
│                                                                               │
│ [Usuário responde]                                                            │
│ Usuário: "usa a vaga de abril"                                               │
│                                                                               │
│ PROCESSAMENTO:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ Intent: SELECT_PREVIOUS_JOB                                             │  │
│ │ Target: "Eng. de Dados Pleno (Abr/2025)"                                │  │
│ │ Ação: Copiar todos os campos da vaga anterior                           │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Etapa 2: Revisão e Ajustes Rápidos

```
┌─ SCRIPT: FAST TRACK - REVISÃO ───────────────────────────────────────────────┐
│                                                                               │
│ LIA: "Copiei tudo da vaga de Abril! Fiz alguns ajustes automáticos:"        │
│                                                                               │
│       **Mudanças Sugeridas:**                                                 │
│       ┌─────────────────────────────────────────────────────────────────┐    │
│       │ ✏️  Senioridade: Pleno → Sênior (você mencionou)                │    │
│       │ 💰 Salário: R$ 12-16k → R$ 15-20k (ajuste para sênior)          │    │
│       │ ⚠️  Salário 11% abaixo mercado - quer ajustar?                  │    │
│       └─────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│       **Mantidos da vaga original:**                                          │
│       • 5 skills técnicas (Python, SQL, Spark, Airflow, AWS)                 │
│       • 3 competências comportamentais                                        │
│       • 5 responsabilidades                                                   │
│       • 5 perguntas WSI                                                       │
│                                                                               │
│       [Painel Lateral: Todos os campos editáveis]                            │
│                                                                               │
│ LIA: "Quer fazer algum ajuste ou posso publicar?"                            │
│                                                                               │
│ [Usuário responde]                                                            │
│ Usuário: "adiciona terraform nas skills e publica"                           │
│                                                                               │
│ PROCESSAMENTO:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ Ação 1: ADD skill "Terraform" (nível inferido: Intermediário)           │  │
│ │ Ação 2: PUBLISH job                                                      │  │
│ │                                                                          │  │
│ │ Verificação: WSI Quality Gates                                           │  │
│ │   ✅ min 5 skills técnicas: 6 (OK)                                      │  │
│ │   ✅ min 3 competências: 3 (OK)                                         │  │
│ │   ✅ min 5 responsabilidades: 5 (OK)                                    │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│ LIA: "Pronto! Adicionei Terraform e publiquei a vaga. 🎉"                   │
│       "Tempo total: 2 minutos e 34 segundos!"                                │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 36.4 Interpretação de Respostas (NLU Patterns)

```python
# Padrões de interpretação de linguagem natural

NLU_PATTERNS = {
    # Confirmações
    "affirmative": [
        "sim", "pode ser", "ok", "beleza", "isso", "exato", "correto",
        "usa isso", "pode usar", "tá bom", "perfeito", "ótimo", "isso mesmo"
    ],
    
    # Negações
    "negative": [
        "não", "nao", "nem", "nope", "errado", "incorreto", "negativo"
    ],
    
    # Ajustes
    "modify_add": [
        "adiciona", "inclui", "coloca", "bota", "põe", "acrescenta"
    ],
    "modify_remove": [
        "tira", "remove", "exclui", "deleta", "apaga", "retira"
    ],
    "modify_change": [
        "muda", "altera", "troca", "substitui", "atualiza"
    ],
    
    # Ações
    "publish": [
        "publica", "publicar", "manda", "libera", "ativa", "vai", "pronto"
    ],
    "save_draft": [
        "salva", "guarda", "deixa pra depois", "continuo depois"
    ],
    
    # Seleção (Fast Track)
    "select_previous": [
        "usa a anterior", "a de abril", "essa mesma", "a primeira"
    ],
    "select_template": [
        "usa o template", "do catálogo", "o curado"
    ]
}
```

### 36.5 Mapeamento Prompt → Campo → Painel

| Pergunta LIA | Campo Extraído | Onde Aparece |
|--------------|----------------|--------------|
| "Qual cargo você está abrindo?" | `job_title` | Painel: Informações Básicas |
| "Qual o nível de senioridade?" | `seniority` | Painel: Informações Básicas |
| "CLT, PJ ou temporário?" | `employment_type` | Painel: Informações Básicas |
| "Presencial, híbrido ou remoto?" | `work_model` | Painel: Informações Básicas |
| "Qual departamento/área?" | `department` | Painel: Informações Básicas |
| "Faixa salarial?" | `salary_min`, `salary_max` | Painel: Remuneração |
| "Quais skills técnicas?" | `skills[]` | Painel: Competências |
| "Competências comportamentais?" | `behavioral_competencies[]` | Painel: Competências |
| "Responsabilidades?" | `responsibilities[]` | Painel: Descrição |
| "Quer usar essas perguntas WSI?" | `wsi_questions[]` | Painel: Screening |

### 36.6 Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO: TEXTO → ESTRUTURA → BANCO                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ENTRADA                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Usuário: "Dev sênior, Python, 15k, remoto, time de dados"            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  2. PROCESSAMENTO NLU (JobIntakeAgent)                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Claude 3.5 Sonnet                                                     │   │
│  │ ├── Extração de entidades                                            │   │
│  │ ├── Normalização de valores                                          │   │
│  │ ├── Cálculo de confiança                                             │   │
│  │ └── Identificação de campos faltantes                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  3. ESTRUTURA INTERMEDIÁRIA (JobDraft)                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ {                                                                     │   │
│  │   "job_title": {"value": "Desenvolvedor", "confidence": 0.95},       │   │
│  │   "seniority": {"value": "senior", "confidence": 1.0},               │   │
│  │   "salary_min": {"value": 15000, "confidence": 0.90},                │   │
│  │   "work_model": {"value": "remote", "confidence": 1.0},              │   │
│  │   "skills": [{"name": "Python", "level": "advanced"}],               │   │
│  │   "status": "draft",                                                  │   │
│  │   "missing_fields": ["department", "responsibilities"]               │   │
│  │ }                                                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  4. ENRIQUECIMENTO (Intelligence Layer)                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ ├── CompensationAnalysisService → Benchmark salarial                 │   │
│  │ ├── SkillsCatalogService → Sugestões de skills                       │   │
│  │ ├── PatternDetectorService → Padrões do recrutador                   │   │
│  │ └── MarketBenchmarkService → Dados de mercado                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  5. PERSISTÊNCIA (após confirmação)                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL                                                            │   │
│  │ ├── job_vacancies (vaga principal)                                   │   │
│  │ ├── job_skills (skills vinculadas)                                   │   │
│  │ ├── wsi_questions (perguntas de triagem)                             │   │
│  │ └── job_drafts (histórico de rascunhos)                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                               │
│  6. SINCRONIZAÇÃO ATS (se configurado)                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Merge API → Gupy, Pandapé, Greenhouse, Lever                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 37. Learning Loop - Fase 1B: Importação de JDs do ATS

> **Objetivo**: Importar Job Descriptions de sistemas ATS/HRIS para construir catálogos personalizados por cliente e melhorar a precisão das sugestões de 60% para 85%.

### 37.1 Arquitetura de Camadas de Dados

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRIORIDADE DE DADOS NO WIZARD                        │
│                    (do mais autoritativo ao fallback)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1️⃣  MENU CONFIGURAÇÕES (sempre primeiro) ─────────── 100% precisão    │
│      → Dados cadastrados na implementação                               │
│      → Estrutura organizacional, benefícios padrão, faixas salariais    │
│                                                                         │
│  2️⃣  HISTÓRICO DA PLATAFORMA LIA ──────────────────── 95% precisão     │
│      → Vagas já criadas na própria LIA                                  │
│      → Padrões de uso do recrutador                                     │
│      → Feedback loops (o que funcionou)                                 │
│                                                                         │
│  3️⃣  IMPORTAÇÃO ATS BÁSICA (Fase 1B) ✅ ────────────── 85% precisão    │
│      → JDs históricos: título, responsabilidades                        │
│      → Skills técnicas e comportamentais                                │
│      → Salários, benefícios praticados                                  │
│                                                                         │
│  4️⃣  INTEGRAÇÃO HRIS / WORKFORCE PLANNING (Fase 1A)── 80% precisão     │
│      → Vagas planejadas/aprovadas                                       │
│      → Headcount, orçamento                                             │
│      → Sugestões proativas de abertura                                  │
│                                                                         │
│  5️⃣  ATS COMPLETO + DATALAKES + ETLs (Fase 2) ─────── 75% precisão     │
│      → Candidatos, entrevistas, contratações                            │
│      → Métricas de processo (time-to-fill, conversão)                   │
│                                                                         │
│  6️⃣  TEMPLATES CURADOS (326) - Fallback ───────────── 70% precisão     │
│      → Quando cliente não tem histórico                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 37.2 Modelos de Dados Implementados

#### ImportedJobDescription
```python
class ImportedJobDescription(Base):
    """JDs importados do ATS/HRIS."""
    __tablename__ = "imported_job_descriptions"
    
    id: UUID
    company_id: UUID
    external_id: str                    # ID no sistema de origem
    source: ImportSource                # ats_gupy, ats_pandape, etc.
    import_batch_id: UUID
    
    # Dados do cargo
    job_title_original: str
    job_title_normalized: str           # Título normalizado para matching
    department: str
    seniority: str
    seniority_confidence: float
    
    # Descrição e requisitos
    description_raw: Text
    responsibilities: List[str]
    technical_skills: List[Dict]        # [{name, level, category}]
    behavioral_competencies: List[Dict]
    requirements_mandatory: List[str]
    requirements_desirable: List[str]
    
    # Remuneração
    salary_min: float
    salary_max: float
    benefits: List[str]
    
    # Métricas (se disponíveis)
    was_filled: bool
    time_to_fill_days: int
    candidates_count: int
    
    # Status de processamento
    processing_status: ProcessingStatus  # raw, parsed, normalized, enriched
    parsing_confidence: float
```

#### ClientSkillCatalog
```python
class ClientSkillCatalog(Base):
    """Catálogo de skills específico do cliente."""
    __tablename__ = "client_skill_catalogs"
    
    company_id: UUID
    skill_name: str
    skill_name_normalized: str
    skill_type: str                     # technical, behavioral
    frequency: int                      # Quantas vezes aparece
    associated_titles: List[str]        # Cargos que usam esta skill
    associated_departments: List[str]
    typical_level: str                  # basic, intermediate, advanced
    success_rate: float                 # Taxa de sucesso em contratações
```

### 37.3 Serviços Implementados

#### JDImportService
```python
class JDImportService:
    """Importa e processa JDs de fontes externas."""
    
    async def import_batch_jds(db, company_id, jds_data, source) -> ImportBatch
    async def import_jd(db, company_id, jd_data, source) -> ImportedJobDescription
    
    def parse_jd(jd: ImportedJobDescription) -> ParsedJD
    # Extrai: título normalizado, senioridade, skills, responsabilidades
    
    async def _update_skill_catalog(db, company_id, batch_id)
    # Atualiza catálogo de skills após importação
```

#### WizardDataPriorityService
```python
class WizardDataPriorityService:
    """Orquestra consulta de dados em ordem de prioridade."""
    
    PRIORITY_ORDER = [
        DataSource.COMPANY_SETTINGS,    # 1. Configurações
        DataSource.LIA_HISTORY,         # 2. Histórico LIA
        DataSource.IMPORTED_ATS,        # 3. JDs importados
        DataSource.WORKFORCE_PLANNING,  # 4. HRIS (futuro)
        DataSource.CURATED_TEMPLATES,   # 5. Templates curados
    ]
    
    async def get_suggestion(db, field, context) -> Suggestion
    async def get_all_suggestions(db, field, context) -> List[Suggestion]
    async def get_similar_jobs(db, context) -> List[Dict]
    async def get_data_coverage(db, company_id) -> Dict
```

### 37.4 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/learning/import/batch` | POST | Importar múltiplos JDs |
| `/api/v1/learning/import/single` | POST | Importar um JD |
| `/api/v1/learning/import/stats` | GET | Estatísticas de importação |
| `/api/v1/learning/suggestions/{field}` | GET | Sugestão para campo do wizard |
| `/api/v1/learning/suggestions/all` | GET | Todas as sugestões de uma vez |
| `/api/v1/learning/similar-jobs` | GET | Vagas similares (Fast Track) |
| `/api/v1/learning/data-coverage` | GET | Cobertura de dados |

### 37.5 Fluxo de Importação

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE IMPORTAÇÃO DE JDs                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. ENTRADA (várias fontes)                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ • ATS (Gupy, Pandapé, Greenhouse, Lever)                         │  │
│  │ • Planilhas Excel/CSV                                             │  │
│  │ • Upload manual de JDs                                            │  │
│  │ • API de importação                                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  2. PARSING E NORMALIZAÇÃO                                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ JDImportService.parse_jd()                                        │  │
│  │ ├── Normalização de título (remove senioridade, padroniza)       │  │
│  │ ├── Detecção de senioridade (patterns + confiança)               │  │
│  │ ├── Extração de skills técnicas (categorização)                  │  │
│  │ ├── Extração de competências comportamentais                     │  │
│  │ ├── Extração de responsabilidades                                │  │
│  │ └── Extração de benefícios                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  3. PERSISTÊNCIA                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ • imported_job_descriptions (JDs brutos + parseados)             │  │
│  │ • client_skill_catalogs (catálogo de skills)                     │  │
│  │ • import_batches (tracking de importação)                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  4. USO NO WIZARD                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ WizardDataPriorityService.get_suggestion()                       │  │
│  │ → Consulta em ordem de prioridade                                │  │
│  │ → Retorna melhor sugestão com confiança                          │  │
│  │ → Explica origem da sugestão                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 37.6 Ciclo de Aprendizagem

```
                         ┌──────────────────┐
                         │   1. CONSUMO     │
                         │   DE DADOS       │
                         └────────┬─────────┘
                                  │
         Configurações, Histórico, ATS, HRIS
                                  │
                                  ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  6. APRENDIZADO  │      │  2. PROCESSAMENTO│      │                  │
│                  │      │  E NORMALIZAÇÃO  │      │                  │
│  • Atualiza      │      │                  │      │                  │
│    padrões       │◄─────│  • Extração      │─────►│  3. ANÁLISE DE   │
│  • Ajusta pesos  │      │  • Categorização │      │     PADRÕES      │
│  • Melhora       │      │  • Enriquecimento│      │                  │
│    predições     │      │                  │      │  • Correlações   │
│                  │      └──────────────────┘      │  • Tendências    │
└────────┬─────────┘                               │  • Anomalias     │
         │                                          └────────┬─────────┘
         │         ┌──────────────────┐                      │
         │         │  5. FEEDBACK     │                      │
         │         │                  │                      │
         └────────►│  • Recrutador    │◄─────────────────────┘
                   │    aceita/rejeita│                      │
                   │  • Ajustes feitos│      ┌───────────────┘
                   │  • Outcome final │      │
                   │    (contratou?)  │      ▼
                   └────────┬─────────┘  ┌──────────────────┐
                            │            │  4. PREDIÇÃO E   │
                            │            │     SUGESTÃO     │
                            │            │                  │
                            └───────────►│  • LIA sugere    │
                                         │  • Preenche campos│
                                         │  • Explica "porquê"│
                                         └──────────────────┘
```

### 37.7 Evolução da Precisão

| Ciclo | Precisão | Fonte Principal |
|-------|----------|-----------------|
| Implementação inicial | ~60% | Templates curados (326) |
| Após importação ATS | ~75% | JDs + Templates |
| Após 10 vagas | ~80% | Histórico LIA + JDs |
| Após 50 vagas | ~87% | Padrões aprendidos |
| Após 100+ vagas | ~92% | Modelo completo |

### 37.8 Arquivos Criados (Fase 1B)

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `app/models/imported_job_description.py` | Model | Modelos ImportedJobDescription, ImportBatch, ClientSkillCatalog |
| `app/services/jd_import_service.py` | Service | Parsing e importação de JDs |
| `app/services/wizard_data_priority_service.py` | Service | Orquestrador de prioridade de dados |
| `app/api/v1/jd_import.py` | API | Endpoints de importação e sugestões |

### 37.9 Próximos Passos (Fase 1A e 2)

| Fase | Escopo | Esforço | Status |
|------|--------|---------|--------|
| **1B** | Importação ATS básica | 2-3 sem | ✅ **COMPLETO** (02/Fev/2026) |
| 1A | Workforce Planning (proativo) | 2-3 sem | ⏳ Próximo |
| 2A | Inteligência Preditiva | 4-5 sem | ⏳ Planejado |
| 2B | Datalakes/HRIS/Fopag | 4-6 sem | ⏳ Planejado |

### 37.10 Detalhes da Implementação (02/Fev/2026)

#### Arquivos Implementados
| Arquivo | Descrição |
|---------|-----------|
| `app/models/imported_job_description.py` | Modelos SQLAlchemy: ImportedJobDescription, ImportBatch, ClientSkillCatalog |
| `app/services/jd_import_service.py` | Serviço de parsing e importação com LLM (90% confidence) |
| `app/services/wizard_data_priority_service.py` | Orquestrador de 6 níveis de prioridade |
| `app/api/v1/jd_import.py` | Router `/api/v1/learning/*` com autenticação |
| `app/api/v1/wizard_suggestions.py` | Router `/api/v1/wizard/*` com respostas enriquecidas |
| `alembic/versions/007_add_learning_loop_import_tables.py` | Migration das tabelas |

#### Endpoints Disponíveis
| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/learning/import/batch` | POST | Importar múltiplos JDs |
| `/api/v1/learning/import/single` | POST | Importar um JD |
| `/api/v1/learning/import/stats` | GET | Estatísticas de importação |
| `/api/v1/learning/data-coverage` | GET | Cobertura de dados |
| `/api/v1/wizard/suggestion/{field}` | GET | Sugestão para campo específico |
| `/api/v1/wizard/suggestions/all` | POST | Todas as sugestões |
| `/api/v1/wizard/similar-jobs` | GET | Vagas similares para Fast Track |
| `/api/v1/wizard/data-coverage` | GET | Cobertura com sources detalhadas |
| `/api/v1/wizard/sources-priority` | GET | Hierarquia de prioridade (6 níveis) |

#### Dados de Teste
- 1 JD importado com 90% parsing confidence
- 112 job patterns do histórico LIA
- Hierarquia de 6 níveis funcionando

### 37.11 Fluxo de Análise e Compilação de Dados

#### Como os JDs são Processados

```
┌─────────────────────────────────────────────────────────────────┐
│  1. ENTRADA DE DADOS                                             │
│  POST /api/v1/learning/import/single                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ {                                                        │    │
│  │   "title": "Desenvolvedor Full Stack Sênior",           │    │
│  │   "description": "Responsável por...",                  │    │
│  │   "department": "Tecnologia",                           │    │
│  │   "salary_min": 12000                                   │    │
│  │ }                                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. PARSING COM LLM (JDImportService.parse_jd)                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Claude/GPT analisa o texto e extrai:                    │    │
│  │ • Título normalizado ("fullstack_developer")            │    │
│  │ • Senioridade detectada ("senior", confidence: 0.9)     │    │
│  │ • Skills técnicas: [React, Node.js, PostgreSQL]         │    │
│  │ • Competências comportamentais: [Liderança, Autonomia]  │    │
│  │ • Responsabilidades: [Desenvolver APIs, Code review]    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. PERSISTÊNCIA NO BANCO                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Tabela: imported_job_descriptions                       │    │
│  │ • Dados brutos + dados parseados                        │    │
│  │ • parsing_confidence = 0.90                             │    │
│  │ • processing_status = "parsed"                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Tabela: client_skill_catalogs (atualizado)              │    │
│  │ • Skills únicas da empresa                              │    │
│  │ • Frequência de uso                                     │    │
│  │ • Cargos associados                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### Como o Wizard Consulta Sugestões

```
┌─────────────────────────────────────────────────────────────────┐
│  WIZARD PEDE SUGESTÃO                                            │
│  GET /api/v1/wizard/suggestion/technical_skills                  │
│  ?job_title=Desenvolvedor&department=Tecnologia                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  WizardDataPriorityService.get_suggestion()                      │
│  Consulta em ORDEM DE PRIORIDADE:                                │
│                                                                   │
│  1️⃣ COMPANY_SETTINGS (100%) ────────────────────────────────────│
│     → Não encontrou skills cadastradas                           │
│                                                                   │
│  2️⃣ LIA_HISTORY (95%) ──────────────────────────────────────────│
│     → Encontrou 3 vagas similares criadas antes                  │
│     → Skills mais usadas: [React, TypeScript, Node.js]           │
│     → Retorna com confidence: 0.95                               │
│     ✅ ENCONTROU! Retorna esta sugestão                          │
│                                                                   │
│  3️⃣ IMPORTED_ATS (85%) ─── (não consultado, já encontrou)       │
│  4️⃣ WORKFORCE_PLANNING (80%) ─── (não consultado)               │
│  5️⃣ CURATED_TEMPLATES (70%) ─── (não consultado)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RESPOSTA PARA O FRONTEND                                        │
│  {                                                               │
│    "field": "technical_skills",                                  │
│    "best_suggestion": {                                          │
│      "value": ["React", "TypeScript", "Node.js"],               │
│      "source": "lia_history",                                    │
│      "confidence": 0.95,                                         │
│      "explanation": "Baseado em 3 vagas similares criadas"       │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 37.12 Integração com Menu Configurações

**O Menu Configurações NÃO foi alterado.** Ele continua funcionando como antes e é a **fonte de maior prioridade (100%)** no sistema.

O que foi criado é uma **camada adicional** que consulta outras fontes quando o Menu Configurações não tem a informação necessária:

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1️⃣ 100% | **Menu Configurações** | Dados cadastrados pelo cliente (estrutura, benefícios, faixas) |
| 2️⃣ 95% | Histórico LIA | Vagas já criadas na plataforma |
| 3️⃣ 85% | JDs Importados | **NOVO** - JDs de ATS externos |
| 4️⃣ 80% | Workforce Planning | Futuro - planos de contratação |
| 5️⃣ 70% | Templates Curados | 361 templates como fallback |

O Menu Configurações **sempre é consultado primeiro**. Se tiver a informação, ela é usada. Se não tiver, o sistema desce na hierarquia até encontrar.

### 37.13 Integração Frontend - Chamadas de API

#### Tipos TypeScript

```typescript
// types/wizard-suggestions.ts

interface Suggestion {
  value: any;
  source: 'company_settings' | 'lia_history' | 'imported_ats' | 'workforce_planning' | 'curated_templates';
  confidence: number;
  explanation: string;
  metadata?: Record<string, any>;
}

interface FieldSuggestionResponse {
  field: string;
  best_suggestion: Suggestion | null;
  all_suggestions: Suggestion[];
}

interface AllSuggestionsResponse {
  suggestions: Record<string, FieldSuggestionResponse>;
  context: {
    job_title?: string;
    department?: string;
    seniority?: string;
  };
}

interface SimilarJob {
  id: string;
  source: string;
  title: string;
  department?: string;
  seniority?: string;
  was_successful?: boolean;
  time_to_fill?: number;
  created_at: string;
  can_use_as_template: boolean;
}

interface DataCoverage {
  imported_jds: number;
  skills_catalog: number;
  job_patterns: number;
  coverage_score: number;
  recommendations: string[];
  sources: Record<string, {
    name: string;
    precision: string;
    description: string;
  }>;
}
```

#### Hook de Sugestões do Wizard

```typescript
// hooks/use-wizard-suggestions.ts

import { useState, useCallback } from 'react';

const API_BASE = '/api/v1/wizard';

export function useWizardSuggestions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Buscar sugestão para um campo específico
  const getSuggestion = useCallback(async (
    field: string,
    context: {
      job_title?: string;
      department?: string;
      seniority?: string;
      location?: string;
      work_model?: string;
    }
  ): Promise<FieldSuggestionResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (context.job_title) params.append('job_title', context.job_title);
      if (context.department) params.append('department', context.department);
      if (context.seniority) params.append('seniority', context.seniority);
      if (context.location) params.append('location', context.location);
      if (context.work_model) params.append('work_model', context.work_model);
      
      const response = await fetch(
        `${API_BASE}/wizard/suggestion/${field}?${params.toString()}`
      );
      
      if (!response.ok) throw new Error('Falha ao buscar sugestão');
      
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Buscar todas as sugestões de uma vez (mais eficiente)
  const getAllSuggestions = useCallback(async (
    context: {
      job_title?: string;
      department?: string;
      seniority?: string;
      location?: string;
      work_model?: string;
    },
    fields?: string[]
  ): Promise<AllSuggestionsResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/wizard/suggestions/all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...context, fields })
      });
      
      if (!response.ok) throw new Error('Falha ao buscar sugestões');
      
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Buscar vagas similares para Fast Track
  const getSimilarJobs = useCallback(async (
    job_title?: string,
    department?: string,
    limit: number = 5
  ): Promise<SimilarJob[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (job_title) params.append('job_title', job_title);
      if (department) params.append('department', department);
      params.append('limit', limit.toString());
      
      const response = await fetch(
        `${API_BASE}/wizard/similar-jobs?${params.toString()}`
      );
      
      if (!response.ok) throw new Error('Falha ao buscar vagas similares');
      
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Buscar cobertura de dados
  const getDataCoverage = useCallback(async (): Promise<DataCoverage | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/wizard/data-coverage`);
      
      if (!response.ok) throw new Error('Falha ao buscar cobertura');
      
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    getSuggestion,
    getAllSuggestions,
    getSimilarJobs,
    getDataCoverage
  };
}
```

#### Exemplo de Uso no Wizard

```typescript
// components/job-creation-wizard.tsx (exemplo de integração)

import { useWizardSuggestions } from '@/hooks/use-wizard-suggestions';
import { useEffect, useState } from 'react';

function JobCreationWizard() {
  const { getSuggestion, getAllSuggestions, getSimilarJobs, loading } = useWizardSuggestions();
  const [formData, setFormData] = useState({
    job_title: '',
    department: '',
    seniority: '',
    technical_skills: [],
    behavioral_competencies: [],
    salary_range: { min: 0, max: 0 }
  });
  const [suggestions, setSuggestions] = useState<Record<string, any>>({});

  // Quando o título do cargo muda, buscar sugestões
  useEffect(() => {
    if (formData.job_title && formData.job_title.length > 3) {
      const fetchSuggestions = async () => {
        const result = await getAllSuggestions({
          job_title: formData.job_title,
          department: formData.department,
          seniority: formData.seniority
        });
        
        if (result) {
          setSuggestions(result.suggestions);
          
          // Auto-preencher campos se tiver alta confiança
          Object.entries(result.suggestions).forEach(([field, suggestion]) => {
            if (suggestion.best_suggestion && suggestion.best_suggestion.confidence >= 0.8) {
              // Não sobrescrever se usuário já preencheu
              if (!formData[field] || formData[field].length === 0) {
                setFormData(prev => ({
                  ...prev,
                  [field]: suggestion.best_suggestion.value
                }));
              }
            }
          });
        }
      };
      
      // Debounce para não chamar a cada keystroke
      const timeout = setTimeout(fetchSuggestions, 500);
      return () => clearTimeout(timeout);
    }
  }, [formData.job_title, formData.department, formData.seniority]);

  // Componente de sugestão inline
  const SuggestionBadge = ({ field }: { field: string }) => {
    const suggestion = suggestions[field]?.best_suggestion;
    if (!suggestion) return null;
    
    const confidenceColor = 
      suggestion.confidence >= 0.9 ? 'bg-green-100 text-green-800' :
      suggestion.confidence >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
      'bg-gray-100 text-gray-800';
    
    const sourceLabel = {
      'company_settings': 'Configurações',
      'lia_history': 'Histórico',
      'imported_ats': 'ATS',
      'curated_templates': 'Template'
    }[suggestion.source] || suggestion.source;
    
    return (
      <div className={`text-xs px-2 py-1 rounded ${confidenceColor}`}>
        💡 Sugestão ({sourceLabel}, {Math.round(suggestion.confidence * 100)}%):
        {suggestion.explanation}
      </div>
    );
  };

  return (
    <div>
      {/* Campo de título com sugestões */}
      <div className="mb-4">
        <label>Título do Cargo</label>
        <input
          value={formData.job_title}
          onChange={(e) => setFormData(prev => ({ ...prev, job_title: e.target.value }))}
          placeholder="Ex: Desenvolvedor Full Stack"
        />
      </div>

      {/* Campo de skills com sugestão automática */}
      <div className="mb-4">
        <label>Skills Técnicas</label>
        <SuggestionBadge field="technical_skills" />
        {/* Renderizar chips de skills */}
        {formData.technical_skills.map(skill => (
          <span key={skill} className="chip">{skill}</span>
        ))}
      </div>

      {/* Indicador de carregamento */}
      {loading && <div className="text-sm text-gray-500">Buscando sugestões...</div>}
    </div>
  );
}
```

#### Proxy no Next.js (se necessário)

```typescript
// app/api/backend-proxy/wizard/[...path]/route.ts

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${BACKEND_URL}/api/v1/wizard/${path}${searchParams ? '?' + searchParams : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        // Forward auth headers if needed
      }
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const body = await request.json();
  const url = `${BACKEND_URL}/api/v1/wizard/${path}`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    );
  }
}
```

### 37.14 Resumo da Integração

| Componente | Arquivo | Função |
|------------|---------|--------|
| **Backend API** | `lia-agent-system/app/api/v1/wizard_suggestions.py` | Endpoints REST para sugestões |
| **Serviço de Prioridade** | `lia-agent-system/app/services/wizard_data_priority_service.py` | Orquestra consultas em 6 níveis |
| **Serviço de Import** | `lia-agent-system/app/services/jd_import_service.py` | Parsing e importação de JDs |
| **Modelos** | `lia-agent-system/app/models/imported_job_description.py` | Tabelas do banco |
| **Frontend Hook** | `plataforma-lia/src/hooks/use-wizard-suggestions.ts` | Hook React para consumir API |
| **Tipos** | `plataforma-lia/src/types/wizard-suggestions.ts` | Interfaces TypeScript |
| **Componente UI** | `plataforma-lia/src/components/wizard/suggestion-badge.tsx` | Badge visual de sugestão |

### 37.15 Arquivos Frontend Implementados (02/Fev/2026)

#### Tipos TypeScript (`plataforma-lia/src/types/wizard-suggestions.ts`)
- `DataSource` - Union type das 5 fontes de dados
- `Suggestion` - Interface para sugestão individual
- `FieldSuggestionResponse` - Resposta por campo
- `AllSuggestionsResponse` - Resposta de todas sugestões
- `SimilarJob` - Vaga similar para Fast Track
- `DataCoverage` - Cobertura de dados do cliente
- `SOURCE_LABELS` / `SOURCE_COLORS` - Labels e cores por fonte

#### Hook React (`plataforma-lia/src/hooks/use-wizard-suggestions.ts`)
- `useWizardSuggestions()` - Hook principal com métodos:
  - `getSuggestion(field, context)` - Sugestão por campo
  - `getAllSuggestions(request)` - Todas as sugestões em batch
  - `getSimilarJobs(job_title, department)` - Vagas similares
  - `getDataCoverage()` - Cobertura de dados
  - `getSourcesPriority()` - Hierarquia de prioridades
- `useAutoFillWizard()` - Hook para preenchimento automático com:
  - `autoFillFields(context, currentData, minConfidence)` - Preenche campos vazios
  - `isAutoFilled(field)` - Verifica se campo foi preenchido automaticamente
  - `clearAutoFilled(field?)` - Limpa marcação de auto-preenchimento

#### Componente UI (`plataforma-lia/src/components/wizard/suggestion-badge.tsx`)
- `SuggestionBadge` - Badge visual que mostra:
  - Ícone de lâmpada
  - Label da fonte (Configurações, Histórico, ATS, etc)
  - Percentual de confiança
  - Explicação da sugestão
  - Botões de aceitar/rejeitar
- `FieldWithSuggestion` - Wrapper para campos do formulário com sugestão integrada

#### Configuração de Proxy (`plataforma-lia/next.config.js`)
```javascript
async rewrites() {
  return [
    {
      source: '/api/v1/:path*',
      destination: 'http://127.0.0.1:8000/api/v1/:path*',
    },
  ];
}
```

O proxy via `rewrites` do Next.js redireciona chamadas `/api/v1/wizard/*` diretamente para o backend Python, sem necessidade de rotas de API intermediárias.

### 37.16 Como Usar no Wizard

```typescript
import { useWizardSuggestions, useAutoFillWizard } from '@/hooks/use-wizard-suggestions';
import { SuggestionBadge, FieldWithSuggestion } from '@/components/wizard/suggestion-badge';

function MeuComponente() {
  const { getSuggestion, getDataCoverage } = useWizardSuggestions();
  const { autoFillFields, isAutoFilled } = useAutoFillWizard();
  
  // Buscar sugestão individual
  const suggestion = await getSuggestion('technical_skills', {
    job_title: 'Desenvolvedor Python',
    department: 'Tecnologia'
  });
  
  // Preencher automaticamente todos os campos vazios
  const newData = await autoFillFields(
    { job_title: 'Desenvolvedor Python' },
    formData,
    0.7  // minConfidence
  );
  
  return (
    <FieldWithSuggestion
      label="Skills Técnicas"
      field="technical_skills"
      value={formData.technical_skills}
      suggestion={suggestion}
      onChange={(v) => setFormData({...formData, technical_skills: v})}
      isAutoFilled={isAutoFilled('technical_skills')}
    >
      <SkillsInput value={formData.technical_skills} />
    </FieldWithSuggestion>
  );
}
```

---
